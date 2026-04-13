from flask import Blueprint, request, jsonify
from extensions import db
from models import Offer
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.recommender_service import RecommendationService

offers_bp = Blueprint('offers', __name__)

@offers_bp.route('/', methods=['GET'])
def get_offers():
    offers = Offer.query.filter_by(is_active=True).order_by(Offer.created_at).all()
    return jsonify([o.to_dict() for o in offers]), 200

@offers_bp.route('/<offer_id>', methods=['GET'])
def get_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    offer.update_stats('view')
    return jsonify(offer.to_dict()), 200

@offers_bp.route('/generate-optimal', methods=['POST'])
@jwt_required()
def generate_optimal_offer():
    from models import User
    from services.analysis_service import AnalysisService
    
    user_id = get_jwt_identity()
    admin = User.query.get_or_404(user_id)
    if admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
        
    new_offer = AnalysisService.identify_optimal_offer()
    if not new_offer:
        return jsonify({"error": "Not enough offers to generate a bundle"}), 400
        
    db.session.add(new_offer)
    db.session.commit()
    return jsonify(new_offer.to_dict()), 201

@offers_bp.route('/insights', methods=['GET'])
def get_insights():
    from services.analysis_service import AnalysisService
    return jsonify({"insights": AnalysisService.get_market_insights()}), 200

@offers_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    recommendations = RecommendationService.get_recommendations_for_user(user_id)
    return jsonify([o.to_dict() for o in recommendations]), 200

# ── Admin ──────────────────────────────────────────────
@offers_bp.route('/', methods=['POST'])
def create_offer():
    data = request.get_json() or {}
    offer = Offer(
        name=data.get('name', ''),
        description=data.get('description'),
        price_from=data.get('price_from'),
        price_to=data.get('price_to'),
        duration_days=data.get('duration_days'),
        duration_label=data.get('duration_label'),
        is_active=data.get('is_active', True),
        is_featured=data.get('is_featured', False),
    )
    db.session.add(offer)
    db.session.commit()
    return jsonify(offer.to_dict()), 201

@offers_bp.route('/<offer_id>', methods=['PUT'])
def update_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json() or {}
    for field in ['name', 'description', 'price_from', 'price_to', 'duration_days', 'duration_label', 'is_active', 'is_featured']:
        if field in data:
            setattr(offer, field, data[field])
    db.session.commit()
    return jsonify(offer.to_dict()), 200

@offers_bp.route('/<offer_id>/toggle', methods=['PATCH'])
def toggle_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    offer.is_active = not offer.is_active
    db.session.commit()
    return jsonify({"is_active": offer.is_active}), 200

@offers_bp.route('/<offer_id>', methods=['DELETE'])
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    return jsonify({"message": "Oferta usunięta"}), 200
