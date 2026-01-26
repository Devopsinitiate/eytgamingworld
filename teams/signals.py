"""
Team signals for handling achievement awards and other team events
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from teams.models import Team, TeamMember
from teams.achievement_service import AchievementService
from teams.notification_service import TeamNotificationService


@receiver(post_save, sender='tournaments.Participant')
def check_tournament_achievements(sender, instance, created, **kwargs):
    """
    Check and award achievements when a tournament participant's status changes
    
    This signal fires when:
    - A team wins a tournament (final_placement == 1)
    - A team completes a tournament (any placement)
    """
    # Only process team-based participants
    if not instance.team:
        return
    
    team = instance.team
    
    # Check if this is a tournament win (final_placement == 1)
    if instance.final_placement == 1:
        # Notify team members of tournament win
        TeamNotificationService.notify_tournament_win(team, instance.tournament)
        
        # Award tournament win achievements
        AchievementService.check_tournament_win_achievements(
            team=team,
            tournament=instance.tournament,
            participant=instance
        )
        
        # Check win streak achievements
        AchievementService.check_win_streak_achievements(team=team)


@receiver(post_save, sender=TeamMember)
def check_roster_achievements(sender, instance, created, **kwargs):
    """
    Check and award roster-related achievements when team membership changes
    
    This signal fires when:
    - A new member joins the team
    - A member's status changes to active
    """
    # Only check when a member becomes active
    if instance.status == 'active':
        team = instance.team
        
        # Check if team is now full
        AchievementService.check_roster_achievements(team=team)


@receiver(pre_save, sender=Team)
def check_tournament_participation_achievements(sender, instance, **kwargs):
    """
    Check and award achievements based on tournament participation count
    
    This signal fires when team statistics are updated
    """
    # Only check if tournaments_played has changed
    if instance.pk:
        try:
            old_instance = Team.objects.get(pk=instance.pk)
            
            # Check if tournaments_played increased
            if instance.tournaments_played > old_instance.tournaments_played:
                # Award participation achievements after save
                # We'll use post_save for this
                pass
        except Team.DoesNotExist:
            pass


@receiver(post_save, sender=Team)
def award_participation_achievements(sender, instance, created, **kwargs):
    """
    Award achievements after team statistics are saved
    """
    if not created:
        # Check participation milestones
        AchievementService.check_tournament_participation_achievements(instance)
