from django.conf import settings
print('STRIPE_WEBHOOK_SECRET=', getattr(settings,'STRIPE_WEBHOOK_SECRET',None))
print('STRIPE_SECRET_KEY=', getattr(settings,'STRIPE_SECRET_KEY',None))
print('PAYSTACK_SECRET_KEY=', getattr(settings,'PAYSTACK_SECRET_KEY',None))
print('PAYSTACK_WEBHOOK_SECRET=', getattr(settings,'PAYSTACK_WEBHOOK_SECRET',None))
