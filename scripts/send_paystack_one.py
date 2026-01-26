import os, requests, json, hmac, hashlib
from decouple import config

PAYMENT_ID = '26d19c4d-5dd5-4f45-99fc-0fb1d8ed9f2a'
PARTICIPANT_ID = 'a2fe3185-7707-4bf6-85dd-008a3c9db1a9'
PAYLOAD = {
	'event': 'charge.success',
	'data': {
		'reference': PAYMENT_ID,
		'amount': 1000,
		'status': 'success',
		'metadata': {'payment_id': PAYMENT_ID, 'participant_id': PARTICIPANT_ID}
	}
}

# Read Paystack secret from .env / settings via python-decouple so signature matches Django settings
secret = config('PAYSTACK_SECRET_KEY', default='')
s = json.dumps(PAYLOAD)
sig = hmac.new(secret.encode(), s.encode(), hashlib.sha512).hexdigest()
url = 'https://2c3e7ebf57f1.ngrok-free.app/tournaments/paystack/webhook/'
print('Sending to', url)
r = requests.post(url, data=s, headers={'Content-Type': 'application/json', 'x-paystack-signature': sig}, timeout=10)
print('Status:', r.status_code)
print('Body:', r.text)
