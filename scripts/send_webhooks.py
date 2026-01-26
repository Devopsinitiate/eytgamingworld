import os, json, time, hmac, hashlib, requests

NGROK = os.environ.get('NGROK_URL', 'https://2c3e7ebf57f1.ngrok-free.app')
PAYMENT_ID = '26d19c4d-5dd5-4f45-99fc-0fb1d8ed9f2a'
PARTICIPANT_ID = 'a2fe3185-7707-4bf6-85dd-008a3c9db1a9'

# Paystack webhook
paystack_secret = os.environ.get('PAYSTACK_SECRET_KEY')
paystack_payload = {
    "event": "charge.success",
    "data": {
        "reference": "ps_ref_12345",
        "amount": 1000,
        "status": "success",
        "metadata": {
            "payment_id": PAYMENT_ID,
            "participant_id": PARTICIPANT_ID
        }
    }
}
pay_payload_txt = json.dumps(paystack_payload)
if paystack_secret:
    sig = hmac.new(paystack_secret.encode('utf-8'), pay_payload_txt.encode('utf-8'), hashlib.sha512).hexdigest()
else:
    sig = ''

pay_url = NGROK.rstrip('/') + '/tournaments/paystack/webhook/'
print('Posting Paystack webhook to', pay_url)
headers = {'Content-Type':'application/json'}
if sig:
    headers['x-paystack-signature'] = sig

    try:
        r = requests.post(pay_url, data=pay_payload_txt, headers=headers, timeout=15)
        print('Paystack response status:', r.status_code)
        print('Paystack response headers:', r.headers)
        print('Paystack response body:', r.text)
    except Exception as e:
        print('Paystack request failed:', repr(e))

# Stripe webhook
stripe_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
stripe_payload = {
    "id": "evt_test_webhook",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": "cs_test_123",
            "payment_status": "paid",
            "metadata": {
                "payment_id": PAYMENT_ID,
                "participant_id": PARTICIPANT_ID
            }
        }
    }
}
stripe_payload_txt = json.dumps(stripe_payload)

# Create Stripe signature header (t=timestamp,v1=signature) using HMAC SHA256
if stripe_secret:
    t = str(int(time.time()))
    signed = f"{t}.{stripe_payload_txt}"
    sig = hmac.new(stripe_secret.encode('utf-8'), signed.encode('utf-8'), hashlib.sha256).hexdigest()
    stripe_sig_header = f"t={t},v1={sig}"
else:
    stripe_sig_header = ''

stripe_url = NGROK.rstrip('/') + '/tournaments/stripe/webhook/'
print('Posting Stripe webhook to', stripe_url)
headers = {'Content-Type':'application/json'}
if stripe_sig_header:
    headers['Stripe-Signature'] = stripe_sig_header

    try:
        r2 = requests.post(stripe_url, data=stripe_payload_txt, headers=headers, timeout=15)
        print('Stripe response status:', r2.status_code)
        print('Stripe response headers:', r2.headers)
        print('Stripe response body:', r2.text)
    except Exception as e:
        print('Stripe request failed:', repr(e))
