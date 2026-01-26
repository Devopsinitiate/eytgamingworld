from tournaments.models import Payment, Participant
p = Payment.objects.filter(id='26d19c4d-5dd5-4f45-99fc-0fb1d8ed9f2a').first()
if p:
    print('PAYMENT', p.id, p.status, p.provider_transaction_id, p.updated_at)
    part = p.participant
    print('PARTICIPANT', part.id, part.has_paid, part.amount_paid)
else:
    print('Payment not found')
