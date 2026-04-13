from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Reservation, TimeSlot, Offer, User, OfferStatistics
from services.reservation_service import create_reservation_atomic
from services.zoom import generate_zoom_link
from services.email import send_email
from services.discord import send_discord_notification
from datetime import datetime

reservation_bp = Blueprint('reservations', __name__)


@reservation_bp.route('/', methods=['POST'])
@jwt_required()
def create_reservation():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    offer_id = data.get('offer_id')
    time_slot_id = data.get('time_slot_id')
    manual_datetime_str = data.get('manual_datetime')
    notes = data.get('notes', '')

    manual_datetime = None
    if manual_datetime_str:
        try:
            manual_datetime = datetime.fromisoformat(manual_datetime_str)
        except ValueError:
            return jsonify({"error": "Nieprawidłowy format manual_datetime"}), 400

    if not time_slot_id and not manual_datetime:
        return jsonify({"error": "Podaj time_slot_id lub manual_datetime"}), 400

    if not offer_id:
        return jsonify({"error": "offer_id jest wymagany"}), 400

    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({"error": "Nie znaleziono oferty"}), 404

    try:
        reservation = create_reservation_atomic(
            user_id=user_id,
            offer_id=offer_id,
            time_slot_id=time_slot_id,
            manual_datetime=manual_datetime,
            notes=notes,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 409

    # ── Notifications (fire-and-forget) ──
    try:
        user = User.query.get(user_id)
        if user:
            send_email(
                user.email,
                "Twoja rezerwacja oczekuje na płatność — TECH.SERVICES",
                f"Złożyłeś zamówienie na {reservation.offer.name if reservation.offer else 'usługę'}. "
                "Po pomyślnym opłaceniu rezerwacji otrzymasz link do spotkania Zoom."
            )
        send_discord_notification(
            f"⏳ Nowa rezerwacja (nieopłacona) #{reservation.id[:8]} | user: {user.email if user else user_id}"
        )
    except Exception as e:
        print(f"[initial notification error] {e}")

    return jsonify({
        "message": "Rezerwacja utworzona",
        "reservation_id": str(reservation.id),
        "meeting_link": reservation.meeting_link,
    }), 201


@reservation_bp.route('/', methods=['GET'])
def get_all_reservations():
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200


@reservation_bp.route('/user/<user_id>', methods=['GET'])
def get_user_reservations(user_id):
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200


@reservation_bp.route('/<reservation_id>/status', methods=['PATCH'])
def update_status(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    data = request.get_json() or {}
    status = data.get('status')
    allowed = ('new', 'confirmed', 'done', 'cancelled')
    if status not in allowed:
        return jsonify({"error": f"Status musi być jednym z: {allowed}"}), 400
    reservation.status = status
    db.session.commit()
    return jsonify(reservation.to_dict()), 200


@reservation_bp.route('/<reservation_id>/cancel', methods=['PATCH'])
@jwt_required()
def cancel_reservation(reservation_id):
    user_id = get_jwt_identity()
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if str(reservation.user_id) != str(user_id):
        return jsonify({"error": "Brak uprawnień do anulowania tej rezerwacji"}), 403
        
    if reservation.status == 'cancelled':
        return jsonify({"error": "Rezerwacja jest już anulowana"}), 400
        
    reservation.status = 'cancelled'
    
    # Free up the slot if it exists
    if reservation.time_slot_id:
        slot = TimeSlot.query.get(reservation.time_slot_id)
        if slot:
            slot.is_available = True
            
    db.session.commit()
    
    try:
        send_discord_notification(f"❌ Rezerwacja anulowana: {reservation.id[:8]} przez użytkownika.")
    except Exception:
        pass
        
    return jsonify({"message": "Rezerwacja została anulowana", "status": "cancelled"}), 200


@reservation_bp.route('/stats', methods=['GET'])
def get_stats():
    stats = OfferStatistics.query.all()
    total = Reservation.query.count()
    return jsonify({
        "total_reservations": total,
        "by_offer": [s.to_dict() for s in stats],
    }), 200
