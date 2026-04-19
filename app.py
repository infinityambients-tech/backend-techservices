import logging
from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, migrate, cors, jwt, mail, limiter
import os
from dotenv import load_dotenv
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

load_dotenv()


def create_app():
    app = Flask(__name__)

    # ProxyFix dla Nginx (X-Forwarded-For, X-Forwarded-Proto itd.)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Setup logging
    is_prod = os.getenv('FLASK_ENV') == 'production'
    logging.basicConfig(
        level=logging.INFO if is_prod else logging.DEBUG,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )    # ── Config ────────────────────────────────────────────
    # Helper for safe secrets (błędy na starcie w produkcji jeśli brakuje)
    def get_env_var(name, default=None):
        val = os.getenv(name)
        if not val:
            if is_prod and default is None:
                raise ValueError(f"Missing required ENV var in production: {name}")
            return default
        return val

    # Database: domyślnie sqlite w dev, ale w prod musi zczytać DATABASE_URL (np. postgres)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_env_var('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Secrets
    app.config['SECRET_KEY'] = get_env_var('SECRET_KEY', None if is_prod else 'dev-secret-key-change-in-prod')
    app.config['JWT_SECRET_KEY'] = get_env_var('JWT_SECRET_KEY', None if is_prod else 'jwt-secret-key-change-in-prod')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 24h

    # Mail
    app.config['MAIL_SERVER'] = get_env_var('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(get_env_var('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = get_env_var('MAIL_USERNAME', None if is_prod else 'dev@techservices.pl')
    app.config['MAIL_PASSWORD'] = get_env_var('MAIL_PASSWORD', None if is_prod else 'dev-pass')
    app.config['MAIL_DEFAULT_SENDER'] = get_env_var('MAIL_DEFAULT_SENDER', 'noreply@techservices.pl')

    # ── Extensions ────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)

    cors.init_app(
        app,
        resources={r"/api/*": {
            "origins": ["https://techservices.com.pl"], 
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        }},
        supports_credentials=True
    )

    jwt.init_app(app)
    mail.init_app(app)
    
    # Rate limiter
    app.config["RATELIMIT_DEFAULT"] = "100 per minute"
    limiter.init_app(app)

    # ── JWT ERRORS ────────────────────────────────────────
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return {"error": "Missing or invalid Authorization header", "details": reason}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return {"error": "Invalid JWT token", "details": reason}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"error": "JWT token has expired"}, 401

    # ── GLOBAL ERROR HANDLER (PATCH) ──────────────────────
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return {
                "error": e.name,
                "details": e.description,
            }, e.code
            
        app.logger.error(f"Server error: {str(e)}")
        return {
            "error": "Server error",
            "type": str(type(e).__name__) if not is_prod else "Internal Error",
            "details": "Internal Server Error" if is_prod else str(e)
        }, 500

    # ── Blueprints ────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.offers import offers_bp
    from routes.reservations import reservation_bp
    from routes.slots import slots_bp
    from routes.user import user_bp
    from routes.contact import contact_bp
    from routes.payment import payment_bp

    app.register_blueprint(auth_bp,        url_prefix='/api/auth')
    app.register_blueprint(offers_bp,      url_prefix='/api/offers')
    app.register_blueprint(reservation_bp, url_prefix='/api/reservations')
    app.register_blueprint(slots_bp,       url_prefix='/api/slots')
    app.register_blueprint(user_bp,        url_prefix='/api/user')
    app.register_blueprint(contact_bp,     url_prefix='/api/contact')
    app.register_blueprint(payment_bp,     url_prefix='/api/payments')

    # ── Health check ──────────────────────────────────────
    @app.route('/api/health')
    def health():
        return {"status": "ok"}

    # ── DEBUG ROUTES (PATCH) ──────────────────────────────
    # Flask 3 removed `before_first_request`, so we print once on the first request.
    _routes_printed = False

    @app.before_request
    def _debug_routes_once():
        nonlocal _routes_printed
        # Wyłącz debugowanie route w środowisku produkcyjnym
        if _routes_printed or is_prod:
            return None
        _routes_printed = True

        print("\nREGISTERED ROUTES:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint:35s} -> {rule}")
        print("\n")
        return None

    # ── DB INIT (SAFE PATCHED VERSION) ────────────────────
    with app.app_context():
        try:
            db.create_all()

            # schema fix safe
            try:
                _ensure_sqlite_schema_compat()
            except Exception as e:
                print("[schema-error]", e)

            # seed safe
            try:
                _seed_offers_if_empty()
            except Exception as e:
                print("[seed-error]", e)

        except Exception as e:
            print("[startup-db-error]", e)

    return app


def _seed_offers_if_empty():
    from models import Offer

    if Offer.query.count() == 0:
        offers = [
            Offer(
                name='Konsultacja Techniczna',
                description='Analiza architektury, code review, plan rozwoju',
                price_from=500,
                price_to=500,
                duration_label='1-2h',
                is_active=True,
                is_featured=True
            ),
            Offer(
                name='MVP Development',
                description='Prototype, Backend + Frontend, Deployment',
                price_from=2000,
                price_to=2000,
                duration_label='2-4 tygodnie',
                is_active=True
            ),
            Offer(
                name='Full Scale System',
                description='Complex logic, Microservices, Scale',
                price_from=5000,
                price_to=None,
                duration_label='2-3 miesiące',
                is_active=True
            ),
            Offer(
                name='Additional Services',
                description='Indywidualne wyceny, dedykowane rozwiązania',
                price_from=None,
                price_to=None,
                duration_label='Do ustalenia',
                is_active=True
            ),
        ]

        for o in offers:
            db.session.add(o)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("[seed-commit-error]", e)


def _ensure_sqlite_schema_compat():
    if db.engine.url.get_backend_name() != 'sqlite':
        return

    def _table_columns(table_name):
        rows = db.session.execute(
            text(f"PRAGMA table_info({table_name})")
        ).fetchall()
        return {r[1] for r in rows}

    def _add_column_if_missing(table_name, column_name, ddl):
        cols = _table_columns(table_name)
        if column_name in cols:
            return
        db.session.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
        )
        db.session.commit()
        print(f"[schema] Added column: {table_name}.{column_name}")

    _add_column_if_missing(
        "reservations",
        "payment_status",
        "payment_status VARCHAR(20) DEFAULT 'unpaid'",
    )

    _add_column_if_missing("payments", "tenant_id", "tenant_id VARCHAR(36)")
    _add_column_if_missing("payments", "paypal_order_id", "paypal_order_id VARCHAR(255)")
    _add_column_if_missing("payments", "paypal_payer_id", "paypal_payer_id VARCHAR(255)")
    _add_column_if_missing("payments", "paypal_subscription_id", "paypal_subscription_id VARCHAR(255)")
    _add_column_if_missing("payments", "currency", "currency VARCHAR(10) DEFAULT 'pln'")
    _add_column_if_missing("payments", "status", "status VARCHAR(20) DEFAULT 'pending'")
    _add_column_if_missing("payments", "created_at", "created_at DATETIME")

    _add_column_if_missing("offers", "is_generated", "is_generated BOOLEAN DEFAULT 0")
    _add_column_if_missing("offers", "source_offers", "source_offers TEXT")
    _add_column_if_missing("offer_statistics", "views", "views INTEGER DEFAULT 0")
    _add_column_if_missing("offer_statistics", "conversions", "conversions INTEGER DEFAULT 0")
    _add_column_if_missing("offer_statistics", "updated_at", "updated_at DATETIME")


app = create_app()

# Fallback development server (Production should use Gunicorn: gunicorn app:app --bind 0.0.0.0:5000)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
