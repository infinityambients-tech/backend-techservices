from flask import Blueprint, request, jsonify
from extensions import db, limiter
from models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re

# Blueprint prefix is applied in app.py via register_blueprint(..., url_prefix='/api/auth')
auth_bp = Blueprint('auth', __name__)


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

    if not email or not valid_email(email):
        return jsonify({"error": "Nieprawidłowy email"}), 400

    if not valid_password(password):
        return jsonify({"error": "Hasło min. 8 znaków"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email już istnieje"}), 400

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Zarejestrowano pomyślnie",
        "user_id": str(user.id),
        "role": user.role,
        "access_token": token
    }), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        if user:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            db.session.commit()

        return jsonify({"error": "Błędne dane logowania"}), 401

    user.failed_attempts = 0
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Zalogowano",
        "user_id": str(user.id),
        "role": user.role,
        "access_token": token
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
    data = request.get_json() or {}

    email = (data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first()

    if user:
        pass  # email system later

    return jsonify({
        "message": "Jeśli konto istnieje, wysłano link"
    }), 200
