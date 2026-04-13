from models import Reservation, Offer, db
from sqlalchemy import func

class RecommendationService:
    @staticmethod
    def get_recommendations_for_user(user_id, limit=3):
        """
        Simple recommendation logic:
        1. Find what the user already bought.
        2. Find what other users who bought the same things also bought.
        3. Return top N offers the user hasn't bought yet.
        """
        # User's current offer IDs
        user_offers = db.session.query(Reservation.offer_id).filter(
            Reservation.user_id == user_id,
            Reservation.payment_status == 'paid'
        ).all()
        user_offer_ids = [o[0] for o in user_offers if o[0]]

        if not user_offer_ids:
            # Fallback: return featured/popular offers
            return Offer.query.filter_by(is_active=True).order_by(Offer.is_featured.desc()).limit(limit).all()

        # Users who bought the same offers
        similar_users = db.session.query(Reservation.user_id).filter(
            Reservation.offer_id.in_(user_offer_ids),
            Reservation.user_id != user_id
        ).distinct().all()
        similar_user_ids = [u[0] for u in similar_users]

        if not similar_user_ids:
            # Fallback if no similar users found
            return Offer.query.filter_by(is_active=True).filter(
                Offer.id.notin_(user_offer_ids)
            ).limit(limit).all()

        # Recommended offers from similar users
        recommendations = db.session.query(
            Offer, func.count(Reservation.id).label('score')
        ).join(Reservation).filter(
            Reservation.user_id.in_(similar_user_ids),
            Offer.id.notin_(user_offer_ids),
            Offer.is_active == True
        ).group_by(Offer).order_by(db.text('score DESC')).limit(limit).all()

        return [r[0] for r in recommendations]
