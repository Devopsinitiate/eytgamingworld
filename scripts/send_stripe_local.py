import time, json, hmac, hashlib, requests
from decouple import config

# Payload: minimal checkout.session.completed event structure
PAYMENT_ID = '26d19c4d-5dd5-4f45-99fc-0fb1d8ed9f2a'
payload = {
    'id': 'evt_test_checkout_session_completed',
    'object': 'event',
    'type': 'checkout.session.completed',
    'data': {
        'object': {
            'id': 'cs_test_123',
            'object': 'checkout.session',
            'client_reference_id': PAYMENT_ID,
            'payment_intent': 'pi_test_123'
        }
    }
}

s = json.dumps(payload)
# Stripe signing: header = "t={ts},v1={sig}"
secret = config('STRIPE_WEBHOOK_SECRET', default='')
ts = str(int(time.time()))
signed_payload = f"{ts}.{s}".encode()
sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
header = f"t={ts},v1={sig}"

# Target URLs
local = 'http://127.0.0.1:8000/tournaments/stripe/webhook/'
ngrok = 'https://2c3e7ebf57f1.ngrok-free.app/tournaments/stripe/webhook/'

for url in (local, ngrok):
    try:
        print('Sending to', url)
        r = requests.post(url, data=s, headers={'Content-Type': 'application/json', 'Stripe-Signature': header}, timeout=10)
        print('Status:', r.status_code)
        print('Body:', r.text)
    except Exception as e:
        print('Error sending to', url, e)
