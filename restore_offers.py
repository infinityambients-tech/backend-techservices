import sys
import os

# Add the current directory to sys.path so we can import app and models
sys.path.append(os.getcwd())

from app import create_app
from extensions import db
from models import Offer

app = create_app()
with app.app_context():
    offers_to_add = [
        {
            'name': 'Konsultacja Techniczna', 
            'description': 'Analiza architektury, code review, plan rozwoju', 
            'price_from': 500, 
            'price_to': 500, 
            'duration_label': '1-2h', 
            'is_active': True, 
            'is_featured': True
        },
        {
            'name': 'MVP Development', 
            'description': 'Prototype, Backend + Frontend, Deployment', 
            'price_from': 2000, 
            'price_to': 2000, 
            'duration_label': '2-4 tygodnie', 
            'is_active': True
        },
    ]
    
    for data in offers_to_add:
        exists = Offer.query.filter_by(name=data['name']).first()
        if not exists:
            o = Offer(**data)
            db.session.add(o)
            print(f"Restored: {data['name']}")
        else:
            print(f"Skipped (already exists): {data['name']}")
            
    db.session.commit()
    print("Done.")
