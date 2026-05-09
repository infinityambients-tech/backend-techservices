import requests
import os

# Base URL should be https://api-m.sandbox.paypal.com or https://api-m.paypal.com
BASE_URL = os.getenv("PAYPAL_BASE_URL")

def get_access_token():
    url = f"{BASE_URL}/v1/oauth2/token"

    response = requests.post(
        url,
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_SECRET") or os.getenv("PAYPAL_CLIENT_SECRET"))
    )

    if response.status_code != 200:
        raise Exception(f"PayPal Auth Failed: {response.text}")

    return response.json()["access_token"]


def create_order(amount):
    token = get_access_token()

    url = f"{BASE_URL}/v2/checkout/orders"

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "PLN",
                "value": str(amount)
            }
        }],
        "application_context": {
            # Use production or sandbox domain in .env
            "return_url": os.getenv("PAYPAL_RETURN_URL", "https://twojadomena.pl/payment/success"),
            "cancel_url": os.getenv("PAYPAL_CANCEL_URL", "https://twojadomena.pl/payment/cancel")
        }
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )

    if response.status_code != 201:
        raise Exception(f"PayPal Order Creation Failed: {response.text}")

    data = response.json()

    for link in data["links"]:
        if link["rel"] == "approve":
            return link["href"]

    raise Exception("Brak linku PayPal (rel=approve)")


def handle_successful_payment(order_id, resource):
    """
    Obsługa pomyślnej płatności z webhookù PayPal.
    
    Called by: WebhookService.handle_payment_capture()
    
    Parameters:
    - order_id: str (PayPal Order ID)
    - resource: dict (PayPal payment resource from webhook)
    
    Process:
    1. Find reservation by order_id reference
    2. Update Reservation.payment_status = 'paid'
    3. Generate Invoice
    4. Send confirmation email
    5. Send Discord notification
    
    Raises:
    - Exception if reservation not found or DB error
    """
    from extensions import db
    from models import Reservation, Payment, User
    from services.email import send_reservation_confirmation
    from services.invoice_service import InvoiceService
    from services.discord import send_discord_notification
    from datetime import datetime
    
    try:
        print(f"[PAYMENT] Processing successful payment: order_id={order_id}")
        
        # Find payment by PayPal order ID
        payment = Payment.query.filter_by(paypal_order_id=order_id).first()
        
        if not payment:
            print(f"[PAYMENT WARNING] No payment found for order_id={order_id}")
            return False
        
        # Find reservation
        reservation = payment.reservation
        if not reservation:
            print(f"[PAYMENT WARNING] No reservation for payment {payment.id}")
            return False
        
        # Update payment status
        payment.status = 'paid'
        payment.paypal_payer_id = resource.get('payer', {}).get('payer_info', {}).get('payer_id')
        
        # Update reservation status
        reservation.payment_status = 'paid'
        reservation.status = 'confirmed'
        
        db.session.commit()
        print(f"[PAYMENT] Reservation {reservation.id} marked as paid")
        
        # Generate invoice
        invoice = InvoiceService.generate_invoice_for_payment(payment)
        print(f"[PAYMENT] Invoice generated: {invoice.invoice_number if invoice else 'FAILED'}")
        
        # Send confirmation email
        user = reservation.user
        if user:
            send_reservation_confirmation(user.email, reservation)
            print(f"[PAYMENT] Confirmation email sent to {user.email}")
        
        # Send Discord notification
        send_discord_notification(
            f"✅ Płatność potwierdzona! | "
            f"Rezerwacja #{reservation.id[:8]} | "
            f"Użytkownik: {user.email if user else 'N/A'} | "
            f"Kwota: {payment.amount/100} PLN"
        )
        
        return True
        
    except Exception as e:
        print(f"[PAYMENT ERROR] handle_successful_payment failed: {str(e)}")
        db.session.rollback()
        return False
