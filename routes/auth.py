#importy
import secrets
import re

#from xxx importy xxx

from flask import Blueprint, request, jsonify, url_for, current_app
from extensions import db, mail, limiter
from models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message, Mail


auth_bp = Blueprint('auth', __name__)
mail = Mail() # Inicjalizacja tutaj, powiążemy ją z app w app.py

def valid_email(email):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email)

def valid_password(pwd):
    return len(pwd) >= 8

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    data = request.get_json() or {}

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    phone = data.get('phone', '')

    # 1. Walidacja wejścia
    if not email or not valid_email(email):
        return jsonify({"error": "Nieprawidłowy email"}), 400

    if not valid_password(password):
        return jsonify({"error": "Hasło musi mieć min. 8 znaków"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email już istnieje w systemie"}), 400

    # 2. Tworzymy użytkownika - automatycznie zweryfikowanego
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        is_verified=True,  # Automatycznie zweryfikowany
        verification_token=None  # Brak tokena, bo niepotrzebny
    )
    user.set_password(password)

    try:
        # Dodajemy użytkownika do bazy i zapisujemy od razu
        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Zarejestrowano pomyślnie. Możesz się teraz zalogować."
        }), 201

    except Exception as e:
        # W razie błędu - cofamy zmiany
        db.session.rollback()
        current_app.logger.error(f"Rejestracja błąd: {str(e)}")
        return jsonify({"error": "Wystąpił błąd podczas rejestracji. Spróbuj ponownie później."}), 500

# DODAJ TĘ TRASĘ, aby link z maila działał:
@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return "<h1>Błąd weryfikacji</h1><p>Link jest nieprawidłowy lub wygasł.</p>", 400
    
    if user.is_verified:
        return "<h1>Konto już aktywne</h1><p>Twoje konto zostało już wcześniej zweryfikowane. Możesz się zalogować.</p>", 200

    try:
        user.is_verified = True
        user.verification_token = None  # Usuwamy token po użyciu
        db.session.commit()
        
        # Tutaj możesz zwrócić prosty HTML lub przekierować na stronę logowania
        return "<h1>Konto aktywowane!</h1><p>Dziękujemy. Możesz teraz wrócić do strony i się zalogować.</p>", 200
    except Exception as e:
        db.session.rollback()
        return "<h1>Błąd serwera</h1><p>Nie udało się aktywować konta. Spróbuj później.</p>", 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Błędne dane logowania"}), 401

    # Użytkownik jest automatycznie zweryfikowany podczas rejestracji
    user.failed_attempts = 0
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Zalogowano",
        "access_token": token,
        "role": user.role
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Wylogowano"}), 200


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password():
    """
    Wysłanie emaila z linkiem do resetowania hasła.
    
    Request (JSON):
    {"email": "user@example.com"}
    
    Response (200):
    {"message": "Jeśli konto istnieje, wysłano link"}
    
    Side Effects:
    - Generates reset token (valid 1 hour)
    - Stores reset_token in User
    - Sends email with reset link
    """
    from services.email import send_email
    from datetime import datetime, timedelta
    
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    
    if not email or not valid_email(email):
        return jsonify({
            "message": "Jeśli konto istnieje, wysłano link"
        }), 200
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        try:
            # Generate reset token (valid 1 hour)
            reset_token = secrets.token_urlsafe(32)
            user.verification_token = reset_token  # Reuse verification_token field
            user.failed_attempts = datetime.utcnow() + timedelta(hours=1)  # Store expiry time
            db.session.commit()
            
            # Send reset email
            reset_link = f"https://techservices.com.pl/reset-password?token={reset_token}"
            subject = "🔑 Resetowanie hasła — TECH.SERVICES"
            body = f"""Witaj {user.first_name}!

Aby zresetować hasło, kliknij w poniższy link:

{reset_link}

Link jest ważny przez 1 godzinę.

Jeśli to nie Ty złożyłeś wniosek, zignoruj tę wiadomość.
"""
            html_body = f"""
            <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
              <h2 style="border-bottom:2px solid #000;padding-bottom:16px">TECH.SERVICES</h2>
              <h3>🔑 Resetowanie hasła</h3>
              <p style="color:#555">Aby przywrócić dostęp do konta, kliknij poniższy przycisk:</p>
              <p style="margin:32px 0">
                <a href="{reset_link}" style="background-color:#007AFF;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block">
                  Zresetuj hasło
                </a>
              </p>
              <p style="color:#999;font-size:12px">Link jest ważny przez 1 godzinę. Jeśli link nie działa, skopiuj go do przeglądarki: {reset_link}</p>
            </div>
            """
            send_email(email, subject, body, html_body)
            print(f"[AUTH] Reset password email sent to {email}")
            
        except Exception as e:
            current_app.logger.error(f"Reset password error: {str(e)}")
            db.session.rollback()
    
    # Always return success message (don't reveal if email exists)
    return jsonify({
        "message": "Jeśli konto istnieje, wysłano link do resetowania hasła."
    }), 200


@auth_bp.route('/reset-password/confirm', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password_confirm():
    """
    Potwierdzenie resetowania hasła z użyciem tokena.
    
    Request (JSON):
    {
        "token": "reset_token_from_email",
        "new_password": "newpassword123"
    }
    
    Response (200):
    {"message": "Hasło zmienione pomyślnie. Możesz się zalogować."}
    
    Errors:
    - 400: Token nieprawidłowy/wygasł / Hasło za krótkie
    - 404: Użytkownik nie znaleziony
    """
    data = request.get_json() or {}
    token = data.get('token') or ''
    new_password = data.get('new_password') or ''
    
    if not new_password or not valid_password(new_password):
        return jsonify({"error": "Hasło musi mieć min. 8 znaków"}), 400
    
    if not token:
        return jsonify({"error": "Token resetowania jest wymagany"}), 400
    
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({"error": "Token jest nieprawidłowy lub wygasł"}), 400
    
    # Check expiry (failed_attempts field holds expiry datetime)
    try:
        from datetime import datetime
        expiry = user.failed_attempts
        if isinstance(expiry, int):
            # Old format (failed attempts counter)
            expiry = datetime.utcnow() + timedelta(hours=-1)
        
        if datetime.utcnow() > expiry:
            return jsonify({"error": "Token wygasł. Spróbuj ponownie."}), 400
    except:
        pass
    
    try:
        # Set new password
        user.set_password(new_password)
        user.verification_token = None  # Clear token
        user.failed_attempts = 0  # Reset
        db.session.commit()
        
        return jsonify({
            "message": "Hasło zmienione pomyślnie. Możesz się teraz zalogować."
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset confirm error: {str(e)}")
        return jsonify({"error": "Błąd podczas zmiany hasła"}), 500
