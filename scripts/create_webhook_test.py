from django.utils import timezone
from core.models import User, Game
from tournaments.models import Tournament, Participant, Payment

user, created = User.objects.get_or_create(
    email='webhook-tester@example.com',
    defaults={'username':'webhooktester','first_name':'Webhook','last_name':'Tester'}
)
if created:
    user.set_password('test')
    user.save()

game, _ = Game.objects.get_or_create(name='TestGame', defaults={'slug':'testgame','genre':'other'})

t, _ = Tournament.objects.get_or_create(
    slug='webhook-tourney',
    defaults={
        'name':'Webhook Tourney',
        'description':'For webhook tests',
        'game':game,
        'organizer':user,
        'registration_start':timezone.now(),
        'registration_end':timezone.now(),
        'check_in_start':timezone.now(),
        'start_datetime':timezone.now(),
    }
)

part, _ = Participant.objects.get_or_create(tournament=t, user=user, defaults={'status':'confirmed'})

payment = Payment.objects.create(participant=part, amount=10.00, provider='paystack', status='pending')

print('PARTICIPANT_ID:'+str(part.id))
print('PAYMENT_ID:'+str(payment.id))
