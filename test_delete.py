from app import create_app
from extensions import db
from models import Offer

app = create_app()
with app.app_context():
    offer = Offer.query.first()
    if not offer:
        print("No offers found")
    else:
        print(f"Attempting to delete offer: {offer.id} ({offer.name})")
        try:
            db.session.delete(offer)
            db.session.commit()
            print("Successfully deleted")
        except Exception as e:
            print(f"Error: {e}")
