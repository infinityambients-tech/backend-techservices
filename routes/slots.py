from flask import Blueprint, request, jsonify
from extensions import db
from models import TimeSlot
from sqlalchemy import or_
from datetime import datetime, timedelta

slots_bp = Blueprint('slots', __name__)

@slots_bp.route('/', methods=['GET'])
def get_slots():
    week_param = request.args.get('week')  # e.g. 2026-02-18
    now = datetime.utcnow()
    # Available if is_available=True AND (no reserved_until OR reserved_until in the past)
    query = TimeSlot.query.filter(
        TimeSlot.is_available == True,
        or_(
            TimeSlot.reserved_until == None,
            TimeSlot.reserved_until < now
        )
    )

    if week_param:
        try:
            week_start = datetime.fromisoformat(week_param)
            week_end = week_start + timedelta(days=7)
            query = query.filter(
                TimeSlot.start_time >= week_start,
                TimeSlot.start_time < week_end
            )
        except ValueError:
            return jsonify({"error": "Nieprawidłowy format daty (użyj YYYY-MM-DD)"}), 400

    slots = query.order_by(TimeSlot.start_time).all()
    return jsonify([s.to_dict() for s in slots]), 200


@slots_bp.route('/', methods=['POST'])
def create_slot():
    data = request.get_json() or {}
    try:
        start = datetime.fromisoformat(data['start_time'])
        end = datetime.fromisoformat(data['end_time'])
    except (KeyError, ValueError):
        return jsonify({"error": "Podaj start_time i end_time w formacie ISO"}), 400

    slot = TimeSlot(start_time=start, end_time=end)
    db.session.add(slot)
    db.session.commit()
    return jsonify(slot.to_dict()), 201


@slots_bp.route('/<slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    slot = TimeSlot.query.get_or_404(slot_id)
    db.session.delete(slot)
    db.session.commit()
    return jsonify({"message": "Slot usunięty"}), 200


@slots_bp.route('/bulk', methods=['POST'])
def bulk_create_slots():
    """Create multiple slots at once — used by admin calendar."""
    data = request.get_json() or {}
    slots_data = data.get('slots', [])
    created = []
    for s in slots_data:
        try:
            start = datetime.fromisoformat(s['start_time'])
            end = datetime.fromisoformat(s['end_time'])
            slot = TimeSlot(start_time=start, end_time=end)
            db.session.add(slot)
            created.append(slot)
        except Exception:
            continue
    db.session.commit()
    return jsonify([s.to_dict() for s in created]), 201
