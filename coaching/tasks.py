from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import CoachingSession, PackagePurchase


def get_site_url():
    """Get the site URL from settings with fallback"""
    # Try to get SITE_URL from settings, otherwise construct from ALLOWED_HOSTS
    if hasattr(settings, 'SITE_URL'):
        return settings.SITE_URL
    
    # Fallback: construct from first ALLOWED_HOST
    if settings.ALLOWED_HOSTS:
        host = settings.ALLOWED_HOSTS[0]
        if host not in ['*', '.ngrok-free.app', '.ngrok.io', '.ngrok.app']:
            # Use https in production, http in development
            protocol = 'https' if not settings.DEBUG else 'http'
            return f'{protocol}://{host}'
    
    # Final fallback for development
    return 'http://127.0.0.1:8000'


@shared_task
def send_session_confirmation(session_id):
    """Send confirmation email for booked session"""
    try:
        session = CoachingSession.objects.select_related(
            'coach__user', 'student', 'game'
        ).get(id=session_id)
        
        site_url = get_site_url()
        
        # Email to student
        if hasattr(session.student, 'email_notifications') and session.student.email_notifications:
            send_mail(
                subject=f'Session Confirmed - {session.coach.user.get_display_name()}',
                message=f'''
                Your coaching session has been confirmed!
                
                Coach: {session.coach.user.get_display_name()}
                Game: {session.game.name}
                Date/Time: {session.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}
                Duration: {session.duration_minutes} minutes
                Price: ${session.price}
                
                Session Details: {site_url}/coaching/session/{session.id}/
                
                Please join using: {session.video_link or session.coach.preferred_platform}
                
                If you need to cancel, please do so at least 24 hours in advance.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[session.student.email],
                fail_silently=True,
            )
        
        # Email to coach
        if hasattr(session.coach.user, 'email_notifications') and session.coach.user.email_notifications:
            send_mail(
                subject=f'New Session Booking - {session.student.get_display_name()}',
                message=f'''
                You have a new coaching session!
                
                Student: {session.student.get_display_name()}
                Game: {session.game.name}
                Date/Time: {session.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}
                Duration: {session.duration_minutes} minutes
                Earning: ${session.price}
                
                Student's Goals: {session.student_notes}
                
                Session Details: {site_url}/coaching/session/{session.id}/
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[session.coach.user.email],
                fail_silently=True,
            )
        
        return f"Confirmation sent for session {session_id}"
    except CoachingSession.DoesNotExist:
        return f"Session {session_id} not found"
    except Exception as e:
        print(f"Error sending session confirmation: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_session_reminders():
    """
    Send reminders for upcoming sessions (24h and 1h before).
    Runs every 30 minutes.
    """
    try:
        now = timezone.now()
        site_url = get_site_url()
        
        # 24-hour reminders
        tomorrow = now + timedelta(hours=24)
        tomorrow_end = tomorrow + timedelta(minutes=30)
        
        sessions_24h = CoachingSession.objects.filter(
            status='confirmed',
            scheduled_start__gte=tomorrow,
            scheduled_start__lt=tomorrow_end
        ).select_related('coach__user', 'student', 'game')
        
        for session in sessions_24h:
            # Send to both coach and student
            for user in [session.coach.user, session.student]:
                if hasattr(user, 'email_notifications') and user.email_notifications:
                    send_mail(
                        subject=f'Session Tomorrow - {session.game.name}',
                        message=f'''
                        Reminder: You have a coaching session tomorrow!
                        
                        {'Coach' if user == session.coach.user else 'Student'}: {session.coach.user.get_display_name() if user == session.student else session.student.get_display_name()}
                        Game: {session.game.name}
                        Time: {session.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}
                        Duration: {session.duration_minutes} minutes
                        
                        Session Link: {site_url}/coaching/session/{session.id}/
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
        
        # 1-hour reminders
        one_hour = now + timedelta(hours=1)
        one_hour_end = one_hour + timedelta(minutes=30)
        
        sessions_1h = CoachingSession.objects.filter(
            status='confirmed',
            scheduled_start__gte=one_hour,
            scheduled_start__lt=one_hour_end
        ).select_related('coach__user', 'student', 'game')
        
        for session in sessions_1h:
            for user in [session.coach.user, session.student]:
                if hasattr(user, 'email_notifications') and user.email_notifications:
                    send_mail(
                        subject=f'Session Starting Soon - {session.game.name}',
                        message=f'''
                        Your coaching session starts in 1 hour!
                        
                        Time: {session.scheduled_start.strftime('%I:%M %p')}
                        Duration: {session.duration_minutes} minutes
                        Platform: {session.video_link or session.coach.preferred_platform}
                        
                        Join here: {site_url}/coaching/session/{session.id}/
                        
                        Make sure you're ready to go!
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
        
        return f"Sent {sessions_24h.count()} 24h reminders and {sessions_1h.count()} 1h reminders"
    except Exception as e:
        print(f"Error sending session reminders: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_cancellation_notification(session_id):
    """Notify about session cancellation"""
    try:
        session = CoachingSession.objects.select_related(
            'coach__user', 'student', 'cancelled_by'
        ).get(id=session_id)
        
        # Notify the other party
        if session.cancelled_by == session.student:
            recipient = session.coach.user
            cancelled_by_name = session.student.get_display_name()
        else:
            recipient = session.student
            cancelled_by_name = session.coach.user.get_display_name()
        
        if recipient.email_notifications:
            send_mail(
                subject=f'Session Cancelled - {session.game.name}',
                message=f'''
                A coaching session has been cancelled.
                
                Cancelled by: {cancelled_by_name}
                Game: {session.game.name}
                Original Time: {session.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}
                Reason: {session.cancellation_reason or 'Not provided'}
                
                {'A refund has been initiated.' if session.is_paid else ''}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        
        return f"Cancellation notification sent for session {session_id}"
    except CoachingSession.DoesNotExist:
        return f"Session {session_id} not found"


@shared_task
def auto_complete_sessions():
    """
    Automatically mark sessions as completed if they ended more than 2 hours ago.
    Runs every hour.
    """
    cutoff = timezone.now() - timedelta(hours=2)
    
    sessions = CoachingSession.objects.filter(
        status='in_progress',
        scheduled_end__lt=cutoff
    )
    
    count = 0
    for session in sessions:
        session.status = 'completed'
        session.actual_end = session.scheduled_end
        session.save()
        
        # Update coach stats
        session.coach.total_sessions += 1
        if not CoachingSession.objects.filter(
            coach=session.coach, student=session.student, status='completed'
        ).exclude(id=session.id).exists():
            session.coach.total_students += 1
        session.coach.total_earnings += session.price
        session.coach.save()
        
        count += 1
    
    return f"Auto-completed {count} sessions"


@shared_task
def mark_no_shows():
    """
    Mark sessions as no-show if not started 30 minutes after scheduled time.
    Runs every 30 minutes.
    """
    try:
        cutoff = timezone.now() - timedelta(minutes=30)
        
        sessions = CoachingSession.objects.filter(
            status='confirmed',
            scheduled_start__lt=cutoff
        )
        
        count = sessions.count()
        sessions.update(status='no_show')
        
        # Send notifications
        for session in sessions:
            # Notify both parties
            for user in [session.coach.user, session.student]:
                if hasattr(user, 'email_notifications') and user.email_notifications:
                    send_mail(
                        subject='Session Marked as No-Show',
                        message=f'''
                        A coaching session has been marked as a no-show.
                        
                        Session: {session.game.name}
                        Scheduled: {session.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}
                        
                        If this was an error, please contact support.
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
        
        return f"Marked {count} sessions as no-show"
    except Exception as e:
        print(f"Error marking no-shows: {e}")
        return f"Error: {str(e)}"


@shared_task
def expire_packages():
    """
    Mark packages as expired if past expiration date.
    Runs daily.
    """
    now = timezone.now()
    
    expired = PackagePurchase.objects.filter(
        status='active',
        expires_at__lt=now
    ).update(status='expired')
    
    return f"Expired {expired} packages"


@shared_task
def send_review_requests():
    """
    Send review requests for completed sessions (24h after completion).
    Runs daily.
    """
    try:
        yesterday = timezone.now() - timedelta(hours=24)
        two_days_ago = yesterday - timedelta(hours=24)
        site_url = get_site_url()
        
        # Get completed sessions without reviews
        sessions = CoachingSession.objects.filter(
            status='completed',
            actual_end__gte=two_days_ago,
            actual_end__lt=yesterday,
            review__isnull=True
        ).select_related('student', 'coach__user', 'game')
        
        count = 0
        for session in sessions:
            if hasattr(session.student, 'email_notifications') and session.student.email_notifications:
                send_mail(
                    subject=f'Review Your Session with {session.coach.user.get_display_name()}',
                    message=f'''
                    How was your coaching session?
                    
                    Coach: {session.coach.user.get_display_name()}
                    Game: {session.game.name}
                    Date: {session.actual_end.strftime('%B %d, %Y')}
                    
                    Please take a moment to leave a review. Your feedback helps other students
                    and helps coaches improve.
                    
                    Leave Review: {site_url}/coaching/session/{session.id}/review/
                    
                    Thank you!
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[session.student.email],
                    fail_silently=True,
                )
                count += 1
        
        return f"Sent {count} review requests"
    except Exception as e:
        print(f"Error sending review requests: {e}")
        return f"Error: {str(e)}"


@shared_task
def calculate_coach_earnings_report(coach_profile_id, start_date, end_date):
    """Generate earnings report for a coach"""
    try:
        from .models import CoachProfile
        coach = CoachProfile.objects.get(id=coach_profile_id)
        
        sessions = CoachingSession.objects.filter(
            coach=coach,
            status='completed',
            actual_end__gte=start_date,
            actual_end__lt=end_date
        )
        
        report = {
            'total_sessions': sessions.count(),
            'total_earnings': sum(s.price for s in sessions),
            'unique_students': sessions.values('student').distinct().count(),
            'average_session_price': sessions.aggregate(
                avg=models.Avg('price')
            )['avg'] or 0,
        }
        
        # Send email with report
        if coach.user.email_notifications:
            send_mail(
                subject=f'Earnings Report - {start_date} to {end_date}',
                message=f'''
                Here's your coaching earnings report:
                
                Period: {start_date} to {end_date}
                Total Sessions: {report['total_sessions']}
                Total Earnings: ${report['total_earnings']:.2f}
                Unique Students: {report['unique_students']}
                Average per Session: ${report['average_session_price']:.2f}
                
                Keep up the great work!
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[coach.user.email],
                fail_silently=True,
            )
        
        return report
    except CoachProfile.DoesNotExist:
        return {'error': 'Coach not found'}