from flask import Blueprint, request, jsonify
from services.payment_service import create_order

payment_bp = Blueprint("payment", __name__)

@payment_bp.route("/create-order", methods=["POST"])
def create():
    try:
        data = request.json
        amount = data.get("amount")

        if not amount:
            return jsonify({"error": "Kwota (amount) jest wymagana"}), 400

        # create_order now returns the approval_url
        url = create_order(amount)

        return jsonify({"approval_url": url})

    except Exception as e:
        # In production, we log the error and return a generic message
        # but for now, we'll return the error string for debugging as requested
        print(f"[Payment Error] {e}")
        return jsonify({"error": str(e)}), 500
