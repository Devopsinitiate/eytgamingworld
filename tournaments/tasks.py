from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import Tournament, Match, Participant


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
def check_tournament_start_times():
    """
    Check for tournaments that should start soon and update their status.
    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()
    
    # Move tournaments from draft to registration when registration_start time is reached
    tournaments_to_open_registration = Tournament.objects.filter(
        status='draft',
        registration_start__lte=now,
        registration_end__gt=now  # Ensure registration period hasn't ended
    )
    
    for tournament in tournaments_to_open_registration:
        tournament.status = 'registration'
        tournament.published_at = now
        tournament.save()
        
        # Notify organizer that registration opened automatically
        send_registration_opened_notification.delay(tournament.id)
    
    # Move tournaments from registration to check-in when registration ends and check-in starts
    tournaments_to_check_in = Tournament.objects.filter(
        status='registration',
        registration_end__lte=now,
        check_in_start__lte=now
    )
    
    for tournament in tournaments_to_check_in:
        tournament.status = 'check_in'
        tournament.save()
        
        # Notify participants that check-in is open
        send_check_in_notifications.delay(tournament.id)
    
    # Move tournaments from check-in to in_progress when start time is reached
    tournaments_to_start = Tournament.objects.filter(
        status='check_in',
        start_datetime__lte=now
    )
    
    for tournament in tournaments_to_start:
        # Check if minimum participants are checked in
        if tournament.total_checked_in >= tournament.min_participants:
            tournament.status = 'in_progress'
            tournament.save()
            
            # Generate bracket and start tournament
            from tournaments.services.bracket_generator import BracketGenerator
            try:
                generator = BracketGenerator(tournament)
                generator.generate_bracket()
                
                # Notify participants that tournament has started
                send_tournament_start_notifications.delay(tournament.id)
            except Exception as e:
                # Log error but don't fail the status update
                print(f"Error generating bracket for tournament {tournament.id}: {e}")
        else:
            # Tournament doesn't have enough participants, consider cancelling or postponing
            # For now, we'll leave it in check_in status
            pass


@shared_task
def send_registration_opened_notification(tournament_id):
    """Notify organizer that registration opened automatically"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        site_url = get_site_url()
        
        if tournament.organizer and tournament.organizer.email:
            send_mail(
                subject=f'Registration Opened: {tournament.name}',
                message=f'''
                Registration has automatically opened for your tournament: {tournament.name}
                
                Registration is now live and players can start signing up!
                
                Tournament Details:
                - Registration ends: {tournament.registration_end}
                - Tournament starts: {tournament.start_datetime}
                - Current participants: {tournament.total_registered}
                
                Manage your tournament: {site_url}/tournaments/{tournament.slug}/
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[tournament.organizer.email],
                fail_silently=True,
            )
    except Tournament.DoesNotExist:
        pass
    except Exception as e:
        # Fail silently but log the error
        print(f"Error sending registration opened notification: {e}")


@shared_task
def send_check_in_notifications(tournament_id):
    """Notify participants that check-in is open"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        participants = tournament.participants.filter(status='confirmed')
        site_url = get_site_url()
        
        # For team-based tournaments, use team notification service
        if tournament.is_team_based:
            try:
                from teams.notification_service import TeamNotificationService
                
                for participant in participants:
                    if participant.team:
                        TeamNotificationService.notify_tournament_check_in_open(participant.team, tournament)
            except ImportError:
                # Fallback if team notification service not available
                pass
        else:
            # For individual tournaments, send email notifications
            for participant in participants:
                if participant.user and hasattr(participant.user, 'email_notifications') and participant.user.email_notifications:
                    send_mail(
                        subject=f'Check-in Open: {tournament.name}',
                        message=f'''
                        Check-in is now open for {tournament.name}!
                        
                        Please check in before the tournament starts at {tournament.start_datetime}.
                        
                        Check in here: {site_url}/tournaments/{tournament.slug}/check-in/
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[participant.user.email],
                        fail_silently=True,
                    )
    except Tournament.DoesNotExist:
        pass
    except Exception as e:
        # Fail silently but log the error
        print(f"Error sending check-in notifications: {e}")


@shared_task
def send_tournament_start_notifications(tournament_id):
    """Notify participants that tournament has started"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        participants = tournament.participants.filter(checked_in=True)
        site_url = get_site_url()
        
        # For team-based tournaments, use team notification service
        if tournament.is_team_based:
            try:
                from teams.notification_service import TeamNotificationService
                
                for participant in participants:
                    if participant.team:
                        TeamNotificationService.notify_tournament_starting(participant.team, tournament)
            except ImportError:
                # Fallback if team notification service not available
                pass
        else:
            # For individual tournaments, send email notifications
            for participant in participants:
                if participant.user and hasattr(participant.user, 'email_notifications') and participant.user.email_notifications:
                    send_mail(
                        subject=f'Tournament Started: {tournament.name}',
                        message=f'''
                        {tournament.name} has officially started!
                        
                        View the bracket: {site_url}/tournaments/{tournament.slug}/bracket/
                        
                        Good luck!
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[participant.user.email],
                        fail_silently=True,
                    )
    except Tournament.DoesNotExist:
        pass
    except Exception as e:
        # Fail silently but log the error
        print(f"Error sending tournament start notifications: {e}")


@shared_task
def send_match_reminders():
    """
    Send reminders for upcoming matches.
    Runs every 10 minutes.
    """
    try:
        now = timezone.now()
        reminder_time = now + timedelta(minutes=30)
        site_url = get_site_url()
        
        # Find matches starting in next 30-40 minutes that haven't been reminded
        upcoming_matches = Match.objects.filter(
            status='ready',
            scheduled_time__gte=now,
            scheduled_time__lte=reminder_time
        ).select_related('participant1__user', 'participant2__user', 'tournament')
        
        for match in upcoming_matches:
            # Send to participant 1
            if match.participant1 and match.participant1.user:
                if hasattr(match.participant1.user, 'email_notifications') and match.participant1.user.email_notifications:
                    send_mail(
                        subject=f'Match Starting Soon - {match.tournament.name}',
                        message=f'''
                        Your match is starting soon!
                        
                        Tournament: {match.tournament.name}
                        Opponent: {match.participant2.display_name if match.participant2 else 'TBD'}
                        Time: {match.scheduled_time}
                        
                        View match details: {site_url}/tournaments/match/{match.id}/
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[match.participant1.user.email],
                        fail_silently=True,
                    )
            
            # Send to participant 2
            if match.participant2 and match.participant2.user:
                if hasattr(match.participant2.user, 'email_notifications') and match.participant2.user.email_notifications:
                    send_mail(
                        subject=f'Match Starting Soon - {match.tournament.name}',
                        message=f'''
                        Your match is starting soon!
                        
                        Tournament: {match.tournament.name}
                        Opponent: {match.participant1.display_name if match.participant1 else 'TBD'}
                        Time: {match.scheduled_time}
                        
                        View match details: {site_url}/tournaments/match/{match.id}/
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[match.participant2.user.email],
                        fail_silently=True,
                    )
    except Exception as e:
        # Fail silently but log the error
        print(f"Error sending match reminders: {e}")


@shared_task
def send_match_result_notification(match_id):
    """Notify participants of match result"""
    try:
        match = Match.objects.select_related(
            'participant1__user', 'participant1__team', 'participant2__user', 'participant2__team', 
            'winner', 'tournament'
        ).get(id=match_id)
        
        if not match.winner:
            return
        
        site_url = get_site_url()
        
        result_text = f'''
        Match Result - {match.tournament.name}
        
        {match.participant1.display_name}: {match.score_p1}
        {match.participant2.display_name}: {match.score_p2}
        
        Winner: {match.winner.display_name}
        
        View bracket: {site_url}/tournaments/{match.tournament.slug}/bracket/
        '''
        
        # Notify both participants
        for participant in [match.participant1, match.participant2]:
            if participant:
                # For team tournaments, notify team captain
                if participant.team:
                    if participant.team.captain.email_notifications:
                        send_mail(
                            subject=f'Match Result - {match.tournament.name}',
                            message=result_text,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[participant.team.captain.email],
                            fail_silently=True,
                        )
                # For individual tournaments, notify user
                elif participant.user and participant.user.email_notifications:
                    send_mail(
                        subject=f'Match Result - {match.tournament.name}',
                        message=result_text,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[participant.user.email],
                        fail_silently=True,
                    )
    except Match.DoesNotExist:
        pass


@shared_task
def auto_complete_expired_tournaments():
    """
    Automatically complete tournaments that have passed their estimated end time.
    Runs daily.
    """
    now = timezone.now()
    
    expired_tournaments = Tournament.objects.filter(
        status='in_progress',
        estimated_end__lte=now - timedelta(hours=24)  # 24 hours past estimated end
    )
    
    for tournament in expired_tournaments:
        tournament.status = 'completed'
        tournament.actual_end = now
        tournament.save()


@shared_task
def cleanup_old_tournament_data():
    """
    Archive or cleanup very old tournament data.
    Runs weekly.
    """
    cutoff_date = timezone.now() - timedelta(days=365)  # 1 year old
    
    # Delete drafts older than 1 year
    old_drafts = Tournament.objects.filter(
        status='draft',
        created_at__lt=cutoff_date
    )
    
    count = old_drafts.count()
    old_drafts.delete()
    
    return f"Cleaned up {count} old draft tournaments"


@shared_task
def generate_tournament_standings(tournament_id):
    """Generate and cache tournament standings"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        
        # Calculate standings based on tournament format
        participants = tournament.participants.all().order_by(
            '-matches_won', '-games_won', 'matches_lost', 'games_lost'
        )
        
        # Update placements
        for idx, participant in enumerate(participants, start=1):
            participant.final_placement = idx
            participant.save(update_fields=['final_placement'])
        
        return f"Generated standings for {tournament.name}"
    except Tournament.DoesNotExist:
        return "Tournament not found"


@shared_task
def distribute_prizes(tournament_id):
    """Calculate and mark prize distribution for completed tournament"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.status != 'completed' or not tournament.prize_distribution:
            return "Tournament not ready for prize distribution"
        
        # Get top finishers
        top_participants = tournament.participants.filter(
            final_placement__isnull=False
        ).order_by('final_placement')
        
        prize_pool = float(tournament.prize_pool)
        
        for placement_key, percentage in tournament.prize_distribution.items():
            placement_num = int(placement_key.replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            
            participant = top_participants.filter(final_placement=placement_num).first()
            if participant:
                prize_amount = (prize_pool * percentage) / 100
                participant.prize_won = prize_amount
                participant.save(update_fields=['prize_won'])
                
                # Notify winner
                if participant.team:
                    # For team tournaments, notify team captain
                    if participant.team.captain.email_notifications:
                        send_mail(
                            subject=f'Prize Won - {tournament.name}',
                            message=f'''
                            Congratulations on finishing {placement_key} place in {tournament.name}!
                            
                            Your team has won: ${prize_amount:.2f}
                            
                            Prize information will be sent to you separately.
                            ''',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[participant.team.captain.email],
                            fail_silently=True,
                        )
                elif participant.user and participant.user.email_notifications:
                    # For individual tournaments, notify user
                    send_mail(
                        subject=f'Prize Won - {tournament.name}',
                        message=f'''
                        Congratulations on finishing {placement_key} place in {tournament.name}!
                        
                        You've won: ${prize_amount:.2f}
                        
                        Prize information will be sent to you separately.
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[participant.user.email],
                        fail_silently=True,
                    )
        
        return f"Distributed prizes for {tournament.name}"
    except Tournament.DoesNotExist:
        return "Tournament not found"