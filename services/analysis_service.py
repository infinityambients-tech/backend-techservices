import json
from models import Offer, Reservation, db
from datetime import datetime

class AnalysisService:
    @staticmethod
    def identify_optimal_offer():
        """
        Analyze offers and suggest a new 'Best Value' bundle.
        Algorithm:
        1. Find the top 2 offers with highest reservations count.
        2. Combine them into a bundle with a 15% discount.
        """
        offers = Offer.query.filter_by(is_active=True, is_generated=False).all()
        if len(offers) < 2:
            return None
        
        # Sort by reservations_count (via statistics relation)
        def get_res_count(o):
            return o.statistics.reservations_count if o.statistics else 0
            
        sorted_offers = sorted(offers, key=get_res_count, reverse=True)
        top_offers = sorted_offers[:2]
        
        # Check if we have any data at all
        if get_res_count(top_offers[0]) == 0:
            # Fallback for fresh installs: pick first 2
            top_offers = offers[:2]
            
        combined_name = f"Zestaw Korzyści: {top_offers[0].name.split(':')[0]} & {top_offers[1].name.split(':')[0]}"
        combined_desc = f"Specjalnie wygenerowany pakiet łączący nasze najczęściej wybierane usługi: {top_offers[0].name} oraz {top_offers[1].name}. Oszczędzasz 15% kupując w duecie!"
        
        # Price: 85% of combined price_from
        p1 = top_offers[0].price_from or 100
        p2 = top_offers[1].price_from or 100
        bundle_price = int((p1 + p2) * 0.85)
        
        new_offer = Offer(
            name=combined_name,
            description=combined_desc,
            price_from=bundle_price,
            price_to=None,
            duration_label="Termin ekspresowy",
            is_active=True,
            is_featured=True,
            is_generated=True,
            source_offers=json.dumps([o.id for o in top_offers])
        )
        
        return new_offer

    @staticmethod
    def get_market_insights():
        """Returns insights about which package is currently leading."""
        offers = Offer.query.filter_by(is_active=True).all()
        if not offers:
            return "Brak aktywnych ofert."
            
        def get_conv(o):
            return o.statistics.conversions if o.statistics else 0
            
        bestseller = max(offers, key=get_conv)
        if get_conv(bestseller) > 0:
            return f"Najchętniej wybierany pakiet to '{bestseller.name}' ({get_conv(bestseller)} zakupów)."
        return "Czekamy na pierwsze zamówienia, aby wyznaczyć trendy."
