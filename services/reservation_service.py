from extensions import db
from models import Reservation, TimeSlot, Offer, OfferStatistics
from services.zoom import generate_zoom_link
from datetime import datetime


class SlotUnavailableError(Exception):
    pass


def create_reservation_atomic(user_id, offer_id, time_slot_id, manual_datetime=None, notes=''):
    """
    Atomically lock a slot and create a reservation.
    Falls back to manual_datetime when no DB slot is selected.
    """
    meeting_link = None
    slot = None

    if time_slot_id:
        # SELECT FOR UPDATE — prevents race conditions in PostgreSQL
        # SQLite doesn't support it natively, so we handle it gracefully
        try:
            slot = (
                TimeSlot.query
                .filter_by(id=time_slot_id, is_available=True)
                .with_for_update()
                .first()
            )
        except Exception:
            # SQLite fallback (dev only)
            slot = TimeSlot.query.filter_by(id=time_slot_id, is_available=True).first()

        if not slot:
            raise SlotUnavailableError("Ten termin jest już zajęty. Wybierz inny.")

        slot.is_available = False
        slot.reserved_by = user_id
        meeting_link = generate_zoom_link(
            "Tech Service Consultation",
            slot.start_time,
            "60"
        )
    else:
        # Calendar-picker path: no DB slot, just a datetime
        meeting_link = generate_zoom_link(
            "Tech Service Consultation",
            manual_datetime,
            "60"
        )

    reservation = Reservation(
        user_id=user_id,
        offer_id=offer_id,
        time_slot_id=time_slot_id,
        manual_datetime=manual_datetime,
        meeting_link=meeting_link,
        notes=notes,
        status='new',
    )
    db.session.add(reservation)

    # Update statistics
    if offer_id:
        stats = OfferStatistics.query.filter_by(offer_id=offer_id).first()
        if not stats:
            stats = OfferStatistics(offer_id=offer_id, reservations_count=0)
            db.session.add(stats)
        stats.reservations_count = (stats.reservations_count or 0) + 1
        stats.last_reserved_at = datetime.utcnow()

    db.session.commit()
    return reservation
