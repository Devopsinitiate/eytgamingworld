from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import Tournament, Match, Participant


@shared_task
def check_tournament_start_times():
    """
    Check for tournaments that should start soon and update their status.
    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()
    
    # Move tournaments from registration to check-in
    tournaments_to_check_in = Tournament.objects.filter(
        status='registration',
        registration_end__lte=now,
        check_in_start__lte=now
    )
    
    for tournament in tournaments_to_check_in:
        tournament.status = 'check_in'
        tournament.save()
        
        # Notify registered participants
        send_check_in_notifications.delay(tournament.id)
    
    # Auto-start tournaments (if check-in is complete)
    tournaments_to_start = Tournament.objects.filter(
        status='check_in',
        start_datetime__lte=now
    )
    
    for tournament in tournaments_to_start:
        # Only start if we have enough checked-in participants
        if tournament.total_checked_in >= tournament.min_participants:
            tournament.start_tournament()
            send_tournament_start_notifications.delay(tournament.id)


@shared_task
def send_check_in_notifications(tournament_id):
    """Notify participants that check-in is open"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        participants = tournament.participants.filter(status='confirmed')
        
        for participant in participants:
            if participant.user and participant.user.email_notifications:
                send_mail(
                    subject=f'Check-in Open: {tournament.name}',
                    message=f'''
                    Check-in is now open for {tournament.name}!
                    
                    Please check in before the tournament starts at {tournament.start_datetime}.
                    
                    Check in here: {settings.SITE_URL}/tournaments/{tournament.slug}/check-in/
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.user.email],
                    fail_silently=True,
                )
    except Tournament.DoesNotExist:
        pass


@shared_task
def send_tournament_start_notifications(tournament_id):
    """Notify participants that tournament has started"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        participants = tournament.participants.filter(checked_in=True)
        
        # For team-based tournaments, use team notification service
        if tournament.is_team_based:
            from teams.notification_service import TeamNotificationService
            
            for participant in participants:
                if participant.team:
                    TeamNotificationService.notify_tournament_starting(participant.team, tournament)
        else:
            # For individual tournaments, send email notifications
            for participant in participants:
                if participant.user and participant.user.email_notifications:
                    send_mail(
                        subject=f'Tournament Started: {tournament.name}',
                        message=f'''
                        {tournament.name} has officially started!
                        
                        View the bracket: {settings.SITE_URL}/tournaments/{tournament.slug}/bracket/
                        
                        Good luck!
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[participant.user.email],
                        fail_silently=True,
                    )
    except Tournament.DoesNotExist:
        pass


@shared_task
def send_match_reminders():
    """
    Send reminders for upcoming matches.
    Runs every 10 minutes.
    """
    now = timezone.now()
    reminder_time = now + timedelta(minutes=30)
    
    # Find matches starting in next 30-40 minutes that haven't been reminded
    upcoming_matches = Match.objects.filter(
        status='ready',
        scheduled_time__gte=now,
        scheduled_time__lte=reminder_time
    ).select_related('participant1__user', 'participant2__user', 'tournament')
    
    for match in upcoming_matches:
        # Send to participant 1
        if match.participant1 and match.participant1.user:
            if match.participant1.user.email_notifications:
                send_mail(
                    subject=f'Match Starting Soon - {match.tournament.name}',
                    message=f'''
                    Your match is starting soon!
                    
                    Tournament: {match.tournament.name}
                    Opponent: {match.participant2.display_name if match.participant2 else 'TBD'}
                    Time: {match.scheduled_time}
                    
                    View match details: {settings.SITE_URL}/tournaments/match/{match.id}/
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.participant1.user.email],
                    fail_silently=True,
                )
        
        # Send to participant 2
        if match.participant2 and match.participant2.user:
            if match.participant2.user.email_notifications:
                send_mail(
                    subject=f'Match Starting Soon - {match.tournament.name}',
                    message=f'''
                    Your match is starting soon!
                    
                    Tournament: {match.tournament.name}
                    Opponent: {match.participant1.display_name if match.participant1 else 'TBD'}
                    Time: {match.scheduled_time}
                    
                    View match details: {settings.SITE_URL}/tournaments/match/{match.id}/
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.participant2.user.email],
                    fail_silently=True,
                )


@shared_task
def send_match_result_notification(match_id):
    """Notify participants of match result"""
    try:
        match = Match.objects.select_related(
            'participant1__user', 'participant2__user', 'winner', 'tournament'
        ).get(id=match_id)
        
        if not match.winner:
            return
        
        result_text = f'''
        Match Result - {match.tournament.name}
        
        {match.participant1.display_name}: {match.score_p1}
        {match.participant2.display_name}: {match.score_p2}
        
        Winner: {match.winner.display_name}
        
        View bracket: {settings.SITE_URL}/tournaments/{match.tournament.slug}/bracket/
        '''
        
        # Notify both participants
        for participant in [match.participant1, match.participant2]:
            if participant and participant.user and participant.user.email_notifications:
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
                if participant.user and participant.user.email_notifications:
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