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
