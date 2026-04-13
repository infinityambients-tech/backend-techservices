from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    for field in ['first_name', 'last_name', 'phone']:
        if field in data:
            setattr(user, field, data[field])
    if 'password' in data and len(data['password']) >= 8:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify(user.to_dict()), 200

@user_bp.route('/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    from models import Reservation
    user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200

@user_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_users():
    user_id = get_jwt_identity()
    admin = User.query.get_or_404(user_id)
    if admin.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200
