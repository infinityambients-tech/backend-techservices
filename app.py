import logging
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

# Importy rozszerzeń i modeli
from extensions import db, migrate, cors, jwt, mail, limiter

# 1. Załadowanie .env na samym początku, przed jakąkolwiek logiką
load_dotenv()

def create_app():
    app = Flask(__name__)

    # --- KONFIGURACJA ŚCIEŻEK (Kluczowe dla home.pl VPS) ---
    # Wymuszamy pełną ścieżkę, aby uniknąć problemu "pustej bazy"
    BASE_DIR = "/var/www/techservices/backend-techservices"
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_PATH, 'app.db')

    # Ustawienie ścieżki instancji dla Flaska
    app.instance_path = INSTANCE_PATH

    # ===== AFTER REQUEST HEADER (Security) =====
    @app.after_request
    def add_header(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' https://api.techservices.com.pl;"
        )
        return response

    # --- POMOCNIK KONFIGURACJI ---
    is_prod = os.getenv('FLASK_ENV') == 'production'

    def get_env_var(name, default=None):
        val = os.getenv(name)
        if not val:
            if is_prod and default is None:
                return None # Pozwalamy na None, obsłużymy to niżej
            return default
        return val

    # --- PODSTAWOWE USTAWIENIA FLASKA ---
    app.url_map.strict_slashes = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SECRET_KEY'] = get_env_var('SECRET_KEY', 'dev-secret-key')

    # --- DATABASE CONFIG (Fix: Wymuszona ścieżka absolutna) ---
    # Nawet jeśli DATABASE_URL jest w .env, upewniamy się, że celuje w poprawne miejsce
    env_db_url = os.getenv('DATABASE_URL')
    if env_db_url and 'sqlite' in env_db_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{DB_PATH}'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{DB_PATH}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT
    app.config['JWT_SECRET_KEY'] = get_env_var('JWT_SECRET_KEY', 'jwt-dev-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 24h

    # --- MAIL CONFIG ---
    app.config['MAIL_SERVER'] = get_env_var('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(get_env_var('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = get_env_var('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = get_env_var('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = get_env_var('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = get_env_var('MAIL_DEFAULT_SENDER')

    # Rate limiter
    app.config["RATELIMIT_DEFAULT"] = "100 per minute"
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    # --- Inicjalizacja rozszerzeń ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # --- CORS (Z Twoimi domenami) ---
    cors.init_app(
        app,
        resources={r"/api/*": {
            "origins": [
                "https://techservices.com.pl",
                "https://www.techservices.com.pl",
                "http://localhost:5173",
                "http://localhost:3000"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }},
        supports_credentials=True
    )

    # Logging
    logging.basicConfig(
        level=logging.INFO if is_prod else logging.DEBUG,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # --- Rejestracja Blueprintów (Wszystkie 7 modułów) ---
    from routes.auth import auth_bp
    from routes.offers import offers_bp
    from routes.reservations import reservation_bp
    from routes.slots import slots_bp
    from routes.user import user_bp
    from routes.contact import contact_bp
    from routes.payment import payment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(offers_bp, url_prefix='/api/offers')
    app.register_blueprint(reservation_bp, url_prefix='/api/reservations')
    app.register_blueprint(slots_bp, url_prefix='/api/slots')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')

    # --- DIAGNOSTYKA ENDPOINT (Dla Ciebie do sprawdzenia bazy) ---
    @app.route('/api/debug-db')
    def debug_db():
        from models import Offer
        try:
            count = Offer.query.count()
            return jsonify({
                "db_uri": app.config['SQLALCHEMY_DATABASE_URI'],
                "db_exists": os.path.exists(DB_PATH),
                "offers_count": count,
                "db_path_used": DB_PATH
            })
        except Exception as e:
            return jsonify({"error": str(e), "path": DB_PATH}), 500

    # --- DB INIT ---
    with app.app_context():
        try:
            # Import modeli przed create_all
            import models 
            db.create_all()
        except Exception as e:
            app.logger.error(f"[startup-db-error] {str(e)}")

    # --- GLOBAL ERROR HANDLERS ---
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request"""
        return jsonify({
            "error": "Bad request",
            "message": str(error.description) if hasattr(error, 'description') else "Invalid request format"
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized - Missing or invalid token"""
        return jsonify({
            "error": "Unauthorized",
            "message": "Token jest wymagany lub jest nieprawidłowy"
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden - Insufficient permissions"""
        return jsonify({
            "error": "Forbidden",
            "message": "Brak uprawnień do tego zasobu"
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found"""
        return jsonify({
            "error": "Not found",
            "message": "Zasób nie został znaleziony"
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429 Too Many Requests"""
        return jsonify({
            "error": "Rate limit exceeded",
            "message": "Zbyt wiele żądań. Spróbuj ponownie za chwilę."
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error"""
        app.logger.error(f"[500 ERROR] {error}")
        db.session.rollback()
        return jsonify({
            "error": "Internal server error",
            "message": "Błąd serwera. Spróbuj ponownie później."
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Catch all unhandled exceptions"""
        app.logger.error(f"[UNHANDLED ERROR] {type(error).__name__}: {error}")
        db.session.rollback()
        
        # Don't leak server details in production
        if is_prod:
            return jsonify({
                "error": "Internal server error",
                "message": "Coś poszło nie tak"
            }), 500
        else:
            return jsonify({
                "error": type(error).__name__,
                "message": str(error)
            }), 500

    return app

# Tworzenie JEDYNEJ instancji aplikacji
app = create_app()

if __name__ == '__main__':
    # Uruchomienie lokalne
    app.run(host='0.0.0.0', port=5000, debug=True)