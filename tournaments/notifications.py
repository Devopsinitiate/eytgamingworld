"""
Tournament Notification Utilities

Handles sending notifications for tournament events.
"""

from notifications.models import Notification
from django.urls import reverse


def send_registration_confirmation(participant):
    """
    Send confirmation notification when a user registers for a tournament.
    
    Requirements: 2.3
    """
    tournament = participant.tournament
    user = participant.user if participant.user else participant.team.captain
    
    title = f"Registration Confirmed: {tournament.name}"
    message = (
        f"You have successfully registered for {tournament.name}. "
        f"The tournament starts on {tournament.start_datetime.strftime('%B %d, %Y at %I:%M %p')}. "
        f"Make sure to check in before the tournament begins!"
    )
    
    action_url = reverse('tournaments:detail', kwargs={'slug': tournament.slug})
    
    Notification.create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='tournament',
        priority='normal',
        content_object=tournament,
        action_url=action_url,
        delivery_methods=['in_app', 'email'],
        tournament_id=str(tournament.id),
        participant_id=str(participant.id)
    )


def send_match_schedule_notification(match):
    """
    Send notification when a match is scheduled.
    
    Requirements: 6.2
    """
    if not match.scheduled_time:
        return
    
    # Notify both participants
    participants = [match.participant1, match.participant2]
    
    for participant in participants:
        if not participant:
            continue
            
        user = participant.user if participant.user else participant.team.captain
        opponent = match.participant2 if participant == match.participant1 else match.participant1
        
        title = f"Match Scheduled: {match.tournament.name}"
        message = (
            f"Your match against {opponent.display_name} has been scheduled for "
            f"{match.scheduled_time.strftime('%B %d, %Y at %I:%M %p')}. "
            f"Round {match.round_number}, Match {match.match_number}. Good luck!"
        )
        
        action_url = reverse('tournaments:bracket', kwargs={'slug': match.tournament.slug})
        
        Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type='match',
            priority='normal',
            content_object=match,
            action_url=action_url,
            delivery_methods=['in_app', 'email'],
            match_id=str(match.id),
            tournament_id=str(match.tournament.id)
        )


def send_tournament_status_change_notification(tournament, old_status, new_status):
    """
    Send notification when tournament status changes.
    
    Requirements: 7.5
    """
    # Get all participants
    participants = tournament.participants.all()
    
    # Define status change messages
    status_messages = {
        'registration': {
            'title': f"Registration Open: {tournament.name}",
            'message': f"Registration is now open for {tournament.name}! Sign up before {tournament.registration_end.strftime('%B %d, %Y')}.",
            'priority': 'normal'
        },
        'check_in': {
            'title': f"Check-in Started: {tournament.name}",
            'message': f"Registration has closed. Check-in is now open for {tournament.name}. Please check in before the tournament starts!",
            'priority': 'high'
        },
        'in_progress': {
            'title': f"Tournament Started: {tournament.name}",
            'message': f"{tournament.name} has officially started! Check the bracket to see your matches. Good luck!",
            'priority': 'high'
        },
        'completed': {
            'title': f"Tournament Completed: {tournament.name}",
            'message': f"{tournament.name} has concluded. Thank you for participating! Check the final results and standings.",
            'priority': 'normal'
        },
        'cancelled': {
            'title': f"Tournament Cancelled: {tournament.name}",
            'message': f"Unfortunately, {tournament.name} has been cancelled. We apologize for any inconvenience.",
            'priority': 'urgent'
        }
    }
    
    notification_info = status_messages.get(new_status)
    if not notification_info:
        return
    
    action_url = reverse('tournaments:detail', kwargs={'slug': tournament.slug})
    
    # Send to all participants
    for participant in participants:
        user = participant.user if participant.user else participant.team.captain
        
        Notification.create_notification(
            user=user,
            title=notification_info['title'],
            message=notification_info['message'],
            notification_type='tournament',
            priority=notification_info['priority'],
            content_object=tournament,
            action_url=action_url,
            delivery_methods=['in_app', 'email'],
            tournament_id=str(tournament.id),
            old_status=old_status,
            new_status=new_status
        )


def send_dispute_notification_to_admins(dispute):
    """
    Send notification to admins when a dispute is filed.
    
    Requirements: 6.5
    """
    from core.models import User
    
    # Get all admin users
    admins = User.objects.filter(role='admin')
    
    match = dispute.match
    tournament = match.tournament
    
    title = f"New Dispute Filed: {tournament.name}"
    message = (
        f"A dispute has been filed for Round {match.round_number}, Match {match.match_number} "
        f"in {tournament.name} by {dispute.reporter.get_display_name()}. "
        f"Please review and resolve the dispute."
    )
    
    action_url = f"/admin/tournaments/matchdispute/{dispute.id}/change/"
    
    # Send to all admins
    for admin in admins:
        Notification.create_notification(
            user=admin,
            title=title,
            message=message,
            notification_type='tournament',
            priority='high',
            content_object=dispute,
            action_url=action_url,
            delivery_methods=['in_app', 'email'],
            dispute_id=str(dispute.id),
            match_id=str(match.id),
            tournament_id=str(tournament.id)
        )


def send_match_result_notification(match):
    """
    Send notification when match results are recorded.
    """
    if not match.winner:
        return
    
    # Notify both participants
    participants = [match.participant1, match.participant2]
    
    for participant in participants:
        if not participant:
            continue
            
        user = participant.user if participant.user else participant.team.captain
        is_winner = participant == match.winner
        
        if is_winner:
            title = f"Victory! You won your match"
            message = (
                f"Congratulations! You won your match in {match.tournament.name}. "
                f"Final score: {match.score_p1}-{match.score_p2}. "
                f"Check the bracket for your next match."
            )
        else:
            title = f"Match Result: {match.tournament.name}"
            message = (
                f"Your match in {match.tournament.name} has concluded. "
                f"Final score: {match.score_p1}-{match.score_p2}. "
                f"Thank you for participating!"
            )
        
        action_url = reverse('tournaments:bracket', kwargs={'slug': match.tournament.slug})
        
        Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type='match',
            priority='normal',
            content_object=match,
            action_url=action_url,
            delivery_methods=['in_app'],
            match_id=str(match.id),
            tournament_id=str(match.tournament.id),
            is_winner=is_winner
        )


def send_check_in_reminder(tournament):
    """
    Send reminder to participants to check in.
    """
    # Get participants who haven't checked in
    participants = tournament.participants.filter(checked_in=False, status='confirmed')
    
    title = f"Check-in Reminder: {tournament.name}"
    message = (
        f"Reminder: Please check in for {tournament.name}. "
        f"The tournament starts soon at {tournament.start_datetime.strftime('%I:%M %p')}. "
        f"Don't miss out!"
    )
    
    action_url = reverse('tournaments:detail', kwargs={'slug': tournament.slug})
    
    for participant in participants:
        user = participant.user if participant.user else participant.team.captain
        
        Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type='tournament',
            priority='high',
            content_object=tournament,
            action_url=action_url,
            delivery_methods=['in_app', 'email'],
            tournament_id=str(tournament.id),
            participant_id=str(participant.id)
        )
