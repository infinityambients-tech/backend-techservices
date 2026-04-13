from flask import Flask
from extensions import db, migrate, cors, jwt, mail, limiter
import os
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


def create_app():
    app = Flask(__name__)

    # ── CONFIG ────────────────────────────────────────────
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECRET_KEY'] = os.getenv(
        'SECRET_KEY', 'dev-secret-key-change-in-prod'
    )
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY', 'jwt-secret-key-change-in-prod'
    )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400

    # Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv(
        'MAIL_DEFAULT_SENDER', 'noreply@techservices.pl'
    )

    # ── IMPORTANT FIX (CORS PROD READY) ───────────────────
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True
    )

    # ── EXTENSIONS ────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
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

    # ── BLUEPRINTS ────────────────────────────────────────
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

    # ── HEALTH CHECK ──────────────────────────────────────
    @app.route('/')
    def index():
        return {
            "message": "TECH.SERVICES API v2.0",
            "status": "ok"
        }

    @app.route('/health')
    def health():
        return {"status": "healthy"}

    # ── DB INIT (SAFE FOR VPS) ────────────────────────────
    with app.app_context():
        db.create_all()
        _ensure_sqlite_schema_compat()
        _seed_offers_if_empty()

    return app


# ── SEED OFFERS ──────────────────────────────────────────
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
                description='Backend + Frontend + Deployment',
                price_from=2000,
                price_to=2000,
                duration_label='2-4 tygodnie',
                is_active=True
            ),
            Offer(
                name='Full Scale System',
                description='Systemy skalowalne, microservices',
                price_from=5000,
                price_to=None,
                duration_label='2-3 miesiące',
                is_active=True
            ),
        ]

        for o in offers:
            db.session.add(o)

        db.session.commit()
        print("[seed] Default offers created")


# ── SQLITE COMPAT (SAFE MIGRATION) ───────────────────────
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
        "payment_status VARCHAR(20) DEFAULT 'unpaid'"
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


# ── APP INSTANCE ─────────────────────────────────────────
app = create_app()