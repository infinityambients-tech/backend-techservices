from extensions import db
from models import Payment, Reservation, TimeSlot, Subscription
from services.payment_service import handle_successful_payment
import json

class WebhookService:
    @staticmethod
    def handle_event(data):
        """
        Unified handler for PayPal webhook events.
        Supported events:
        - PAYMENT.CAPTURE.COMPLETED
        - BILLING.SUBSCRIPTION.ACTIVATED
        - BILLING.SUBSCRIPTION.CANCELLED
        """
        event_type = data.get('event_type')
        resource = data.get('resource', {})
        
        print(f"[Webhook] Processing event: {event_type}")
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            WebhookService.handle_payment_capture(resource)
            
        elif event_type == 'CHECKOUT.ORDER.APPROVED':
            # This event occurs when the buyer approves the payment but it's not yet captured.
            # We can treat this as a signal to confirm the reservation if intent was CAPTURE.
            WebhookService.handle_payment_capture(resource)

        elif event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            WebhookService.handle_subscription_status(resource, 'active')
            
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            WebhookService.handle_subscription_status(resource, 'cancelled')
            
        else:
            print(f"[Webhook] Unhandled event type: {event_type}")

    @staticmethod
    def handle_payment_capture(resource):
        # Extract PayPal order ID
        order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
        if not order_id:
            order_id = resource.get('id')
            
        if not order_id:
            print("[Webhook Error] No order ID found in resource")
            return

        try:
            handle_successful_payment(order_id, resource)
        except Exception as e:
            print(f"[Webhook Error] handle_successful_payment failed: {e}")

    @staticmethod
    def handle_subscription_status(resource, new_status):
        paypal_sub_id = resource.get('id')
        if not paypal_sub_id:
            return
            
        sub = Subscription.query.filter_by(paypal_subscription_id=paypal_sub_id).first()
        if sub:
            sub.status = new_status
            db.session.commit()
            print(f"[Webhook] Subscription {paypal_sub_id} updated to {new_status}")
