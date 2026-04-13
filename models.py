from extensions import db
from datetime import datetime
import uuid

# Use String-based UUID for SQLite compatibility (auto-upgrades with PostgreSQL via env)
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    UUID_TYPE = PG_UUID(as_uuid=True)
except Exception:
    UUID_TYPE = db.String(36)

from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True) # For multi-tenancy
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))

    role = db.Column(db.String(20), default='user')      # user / admin
    is_verified = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservations = db.relationship('Reservation', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Offer(db.Model):
    __tablename__ = 'offers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price_from = db.Column(db.Integer)
    price_to = db.Column(db.Integer)
    duration_days = db.Column(db.Integer)
    duration_label = db.Column(db.String(100))   # e.g. "2-4 tygodnie"

    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_generated = db.Column(db.Boolean, default=False)
    source_offers = db.Column(db.Text, nullable=True) # JSON list of IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    statistics = db.relationship('OfferStatistics', backref='offer', cascade="all, delete-orphan", uselist=False)
    reservations = db.relationship('Reservation', back_populates='offer', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Offer {self.name}>'

    def to_dict(self):
        stats = self.statistics
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price_from': self.price_from,
            'price_to': self.price_to,
            'duration_label': self.duration_label,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'is_generated': self.is_generated,
            'source_offers': json.loads(self.source_offers) if self.source_offers else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'stats': {
                'views': stats.views if stats else 0,
                'conversions': stats.conversions if stats else 0,
                'reservations_count': stats.reservations_count if stats else 0
            } if stats else None
        }

    def update_stats(self, stat_type):
        from extensions import db
        if not self.statistics:
            from models import OfferStatistics
            self.statistics = OfferStatistics(offer_id=self.id)
            db.session.add(self.statistics)
        
        if stat_type == 'view':
            self.statistics.views += 1
        elif stat_type == 'reservation':
            self.statistics.reservations_count += 1
        elif stat_type == 'conversion':
            self.statistics.conversions += 1
        
        db.session.commit()


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    reserved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    reserved_until = db.Column(db.DateTime, nullable=True) # For temporary 15min locks

    reservation = db.relationship('Reservation', backref='time_slot', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'start': self.start_time.isoformat(),
            'end': self.end_time.isoformat(),
            'is_available': self.is_available,
        }


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    offer_id = db.Column(db.String(36), db.ForeignKey('offers.id'), nullable=True)
    time_slot_id = db.Column(db.String(36), db.ForeignKey('time_slots.id'), nullable=True)

    meeting_link = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Manual datetime fallback (when no slot from DB — calendar picker)
    manual_datetime = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), default='new')  # new / confirmed / done / cancelled
    payment_status = db.Column(db.String(20), default='unpaid') # unpaid / paid

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='reservations')
    offer = db.relationship('Offer', back_populates='reservations')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'offer_id': self.offer_id,
            'time_slot_id': self.time_slot_id,
            'meeting_link': self.meeting_link,
            'notes': self.notes,
            'status': self.status,
            'payment_status': self.payment_status,
            'manual_datetime': self.manual_datetime.isoformat() if self.manual_datetime else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # joined
            'offer_name': self.offer.name if self.offer else None,
            'start_time': self.time_slot.start_time.isoformat() if self.time_slot else (
                self.manual_datetime.isoformat() if self.manual_datetime else None
            ),
            'user_email': self.user.email if self.user else None,
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    reservation_id = db.Column(db.String(36), db.ForeignKey('reservations.id'), nullable=False)
    
    paypal_order_id = db.Column(db.String(255))
    paypal_payer_id = db.Column(db.String(255))
    paypal_subscription_id = db.Column(db.String(255))

    amount = db.Column(db.Integer)  # in cents
    currency = db.Column(db.String(10), default='pln')

    status = db.Column(db.String(20), default='pending') # pending / paid / failed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservation = db.relationship('Reservation', backref='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'paypal_order_id': self.paypal_order_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)

    discount_type = db.Column(db.String(20), nullable=False)  # percentage / fixed
    value = db.Column(db.Integer, nullable=False) # % or amount in cents

    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)

    valid_until = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_type': self.discount_type,
            'value': self.value,
            'max_uses': self.max_uses,
            'used_count': self.used_count,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active
        }


class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    paypal_plan_id = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False) # in cents
    interval = db.Column(db.String(50), default="month") # month / year

    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'interval': self.interval,
            'is_active': self.is_active
        }


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    paypal_subscription_id = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending') # active / cancelled / expired
    current_period_end = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None
        }


class ConnectedAccount(db.Model):
    __tablename__ = "connected_accounts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    paypal_email = db.Column(db.String(255))
    merchant_id = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'paypal_email': self.paypal_email,
            'merchant_id': self.merchant_id,
            'is_active': self.is_active
        }


class OfferStatistics(db.Model):
    __tablename__ = 'offer_statistics'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_id = db.Column(db.String(36), db.ForeignKey('offers.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    reservations_count = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    last_reserved_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship defined in Offer model with cascade

    def to_dict(self):
        return {
            'offer_id': self.offer_id,
            'offer_name': self.offer.name if self.offer else None,
            'reservations_count': self.reservations_count,
            'last_reserved_at': self.last_reserved_at.isoformat() if self.last_reserved_at else None,
        }


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='new')   # new / read / archived

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), unique=True)
    
    # Company details for invoicing
    company_name = db.Column(db.String(255))
    company_nip = db.Column(db.String(50))
    company_address = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain
        }


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reservation_id = db.Column(db.String(36), db.ForeignKey('reservations.id'), nullable=True)
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'), nullable=True)

    invoice_number = db.Column(db.String(50), unique=True)

    net_amount = db.Column(db.Integer)      # in cents
    vat_rate = db.Column(db.Integer)        # e.g., 23
    vat_amount = db.Column(db.Integer)      # in cents
    gross_amount = db.Column(db.Integer)    # in cents

    currency = db.Column(db.String(10), default="PLN")

    buyer_name = db.Column(db.String(255))
    buyer_address = db.Column(db.Text)
    buyer_nip = db.Column(db.String(50), nullable=True)

    pdf_url = db.Column(db.Text)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'net_amount': self.net_amount,
            'vat_rate': self.vat_rate,
            'vat_amount': self.vat_amount,
            'gross_amount': self.gross_amount,
            'currency': self.currency,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'pdf_url': self.pdf_url
        }


class InvoiceSequence(db.Model):
    __tablename__ = "invoice_sequences"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    last_value = db.Column(db.Integer, default=0)
