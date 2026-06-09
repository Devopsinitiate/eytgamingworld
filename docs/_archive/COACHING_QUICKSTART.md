# Coaching System - Quick Start Guide

## Immediate Setup (5 Minutes)

### 1. Run Migrations
```bash
python manage.py makemigrations coaching
python manage.py migrate
```

### 2. Update URLs
Ensure `config/urls.py` includes:
```python
path('coaching/', include('coaching.urls')),
```

### 3. Configure Stripe (Test Mode)
Add to `.env`:
```bash
STRIPE_PUBLIC_KEY=pk_test_51234567890
STRIPE_SECRET_KEY=sk_test_51234567890
```

Get test keys from: https://dashboard.stripe.com/test/apikeys

## Create Your First Coach (2 Methods)

### Method 1: Via Admin (Easiest)
```bash
# 1. Create/select a user with coach role
http://localhost:8000/admin/core/user/

# 2. Create coach profile
http://localhost:8000/admin/coaching/coachprofile/add/

# 3. Add game expertise
# (Use inline form or add separately)

# 4. Set availability
# (Use inline form or add separately)

# 5. Mark as verified ✓
```

### Method 2: Via Django Shell
```python
python manage.py shell

from coaching.models import CoachProfile, CoachGameExpertise, CoachAvailability
from core.models import User, Game

# Get coach user
user = User.objects.filter(role='coach').first()
# or create: user = User.objects.create_user('coach@test.com', 'password', role='coach')

# Create profile
coach = CoachProfile.objects.create(
    user=user,
    bio="Expert coach with tournament experience",
    experience_level='professional',
    years_experience=5,
    hourly_rate=50.00,
    status='active',
    accepting_students=True,
    is_verified=True,
    min_session_duration=60,
    max_session_duration=180,
    session_increment=30
)

# Add game
game = Game.objects.first()
CoachGameExpertise.objects.create(
    coach=coach,
    game=game,
    rank='master',
    is_primary=True
)

# Add availability (Monday 2-8 PM)
CoachAvailability.objects.create(
    coach=coach,
    weekday=0,
    start_time='14:00',
    end_time='20:00'
)
```

## Test the Booking Flow

### As a Student:
1. **Browse Coaches**
   ```
   http://localhost:8000/coaching/
   ```

2. **View Coach Profile**
   - Click on a coach
   - See their expertise, reviews, availability

3. **Book a Session**
   - Click "Book Session"
   - Select date (must be in future)
   - Choose available time slot
   - Pick duration (60/90/120 min)
   - Add your learning goals
   - Submit

4. **Make Payment**
   - Use test card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any 3-digit CVC
   - Any ZIP code
   - Click Pay

5. **Confirm Booking**
   - Payment processes
   - Session is confirmed
   - Email sent to both parties

### As a Coach:
1. **View Your Sessions**
   ```
   http://localhost:8000/coaching/sessions/?type=coaching
   ```

2. **Start Session** (at scheduled time)
   - Go to session detail
   - Click "Start Session"
   - Share video link with student

3. **Complete Session**
   - Add coach notes
   - Click "Complete Session"
   - Student can now review

## Test Stripe Webhooks (Optional)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe  # Mac
# or download from: https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks
stripe listen --forward-to localhost:8000/payments/webhook/

# Test payment
stripe trigger payment_intent.succeeded
```

## Common Tasks

### Create Multiple Coaches
```python
from coaching.models import CoachProfile
from core.models import User

for i in range(5):
    user = User.objects.create_user(
        email=f'coach{i}@test.com',
        username=f'coach{i}',
        password='testpass123',
        role='coach'
    )
    CoachProfile.objects.create(
        user=user,
        bio=f"Coach #{i} - Expert in multiple games",
        hourly_rate=30 + (i * 10),
        status='active',
        is_verified=True
    )
```

### View All Bookings
```bash
http://localhost:8000/admin/coaching/coachingsession/
```

### Check Celery Tasks
```bash
# In separate terminal
celery -A config worker -l info

# Watch for:
# - Session confirmations
# - Reminders
# - Auto-completions
```

## Troubleshooting

### Issue: "Coach not available at this time"
**Solution**: Add availability slots for the coach
```python
CoachAvailability.objects.create(
    coach=coach,
    weekday=1,  # Tuesday
    start_time='10:00',
    end_time='18:00',
    is_active=True
)
```

### Issue: "Payment failed"
**Solution**: 
1. Check Stripe keys in `.env`
2. Use test card: 4242 4242 4242 4242
3. Check Stripe dashboard for errors

### Issue: "No available slots showing"
**Solution**:
1. Ensure coach has availability for selected day
2. Check existing bookings aren't blocking
3. Date must be in the future

### Issue: "Emails not sending"
**Solution**: 
1. Check Celery worker is running
2. Check email settings in .env
3. Check user has `email_notifications=True`

## Default Test Data

Create sample data:
```bash
python manage.py shell

from django.core.management import call_command
call_command('loaddata', 'fixtures/sample_coaches.json')
```

Or manually:
```python
from coaching.models import *
from core.models import *

# Create 3 coaches with different rates
coaches = []
for i, rate in enumerate([30, 50, 75]):
    user = User.objects.create_user(
        email=f'coach{i}@example.com',
        username=f'Coach_{i}',
        role='coach'
    )
    coach = CoachProfile.objects.create(
        user=user,
        bio=f"Professional coach - ${rate}/hr",
        hourly_rate=rate,
        is_verified=True,
        status='active'
    )
    coaches.append(coach)

print(f"Created {len(coaches)} coaches")
```

## Monitoring

### Key Metrics to Watch
```python
from coaching.models import CoachProfile, CoachingSession

# Active coaches
CoachProfile.objects.filter(status='active').count()

# Total sessions this week
from django.utils import timezone
from datetime import timedelta
week_ago = timezone.now() - timedelta(days=7)
CoachingSession.objects.filter(created_at__gte=week_ago).count()

# Average rating
CoachProfile.objects.aggregate(avg_rating=models.Avg('average_rating'))

# Total earnings
CoachingSession.objects.filter(
    status='completed', is_paid=True
).aggregate(total=models.Sum('price'))
```

## Next Steps

Once coaching system is working:

1. ✅ Test full booking flow
2. ✅ Verify payments work
3. ✅ Check email notifications
4. ✅ Test reviews
5. ✅ Try package purchases
6. 🎨 Build frontend templates
7. 📹 Add video integration
8. 📱 Create mobile interface

---

**Need Help?**
- Check `PHASE_3_COMPLETE.md` for full documentation
- Review models in `coaching/models.py`
- Test endpoints in `coaching/urls.py`
- Monitor admin at http://localhost:8000/admin/coaching/

**Ready to go!** 🚀