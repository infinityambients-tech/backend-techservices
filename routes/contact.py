from flask import Blueprint, request, jsonify
from extensions import db
from models import ContactMessage
from services.email import send_email
import os

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/', methods=['POST'])
def send_message():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not message:
        return jsonify({'error': 'Wszystkie pola sa wymagane'}), 400

    msg = ContactMessage(name=name, email=email, message=message)
    db.session.add(msg)
    db.session.commit()

    receiver_email = os.getenv('CONTACT_RECEIVER_EMAIL', 'igorzajq0@gmail.com')
    subject = f"[Kontakt] Nowa wiadomosc od {name}"
    body = (
        'Nowe zgloszenie z formularza kontaktowego:\n\n'
        f"ID: {msg.id}\n"
        f"Data: {msg.created_at.isoformat() if msg.created_at else 'n/a'}\n"
        f"Imie i nazwisko: {name}\n"
        f"Email: {email}\n"
        f"IP: {request.remote_addr or 'n/a'}\n"
        f"User-Agent: {request.headers.get('User-Agent', 'n/a')}\n\n"
        'Wiadomosc:\n'
        f"{message}\n"
    )
    send_email(receiver_email, subject, body)

    return jsonify({'message': 'Wiadomosc wyslana'}), 201


@contact_bp.route('/', methods=['GET'])
def get_messages():
    msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return jsonify([m.to_dict() for m in msgs]), 200


@contact_bp.route('/<msg_id>/status', methods=['PATCH'])
def update_status(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    data = request.get_json() or {}
    status = data.get('status')
    if status in ('new', 'read', 'archived'):
        msg.status = status
        db.session.commit()
    return jsonify(msg.to_dict()), 200

