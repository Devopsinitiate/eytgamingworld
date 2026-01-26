"""
Team Notification Service

This module handles all team-related notifications.
Centralizes notification logic for team events, invites, applications, announcements, etc.

Requirements: 4.3, 5.3, 9.2, 15.4
"""

from django.utils import timezone
from notifications.models import Notification


class TeamNotificationService:
    """Service for managing team-related notifications"""
    
    # ========================================================================
    # Team Invitations (Requirement 4.3)
    # ========================================================================
    
    @classmethod
    def notify_team_invite(cls, invite, invited_by):
        """
        Send notification when a user is invited to join a team
        
        Args:
            invite: TeamInvite instance
            invited_by: User who sent the invite
        
        Requirement: 4.3
        """
        Notification.create_notification(
            user=invite.invited_user,
            title=f"Team Invitation from {invite.team.name}",
            message=f"{invited_by.get_display_name()} has invited you to join {invite.team.name} [{invite.team.tag}].",
            notification_type='team',
            priority='normal',
            content_object=invite,
            action_url=f'/teams/invite/{invite.id}/accept/',
            delivery_methods=['in_app', 'email'],
            metadata={
                'team_id': str(invite.team.id),
                'team_name': invite.team.name,
                'invited_by_id': str(invited_by.id),
                'invited_by_name': invited_by.get_display_name(),
            }
        )
    
    @classmethod
    def notify_invite_accepted(cls, invite, team):
        """
        Notify team captain when an invite is accepted
        
        Args:
            invite: TeamInvite instance
            team: Team instance
        """
        Notification.create_notification(
            user=team.captain,
            title=f"{invite.invited_user.get_display_name()} joined your team",
            message=f"{invite.invited_user.get_display_name()} has accepted the invitation to join {team.name}.",
            notification_type='team',
            priority='normal',
            content_object=team,
            action_url=f'/teams/{team.slug}/',
            delivery_methods=['in_app'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'user_id': str(invite.invited_user.id),
                'user_name': invite.invited_user.get_display_name(),
            }
        )
    
    @classmethod
    def notify_invite_declined(cls, invite, team):
        """
        Notify team captain when an invite is declined
        
        Args:
            invite: TeamInvite instance
            team: Team instance
        """
        Notification.create_notification(
            user=team.captain,
            title=f"Team invitation declined",
            message=f"{invite.invited_user.get_display_name()} has declined the invitation to join {team.name}.",
            notification_type='team',
            priority='low',
            content_object=team,
            action_url=f'/teams/{team.slug}/roster/',
            delivery_methods=['in_app'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'user_id': str(invite.invited_user.id),
                'user_name': invite.invited_user.get_display_name(),
            }
        )
    
    # ========================================================================
    # Team Applications (Requirement 5.3)
    # ========================================================================
    
    @classmethod
    def notify_new_application(cls, application, team):
        """
        Notify team captain when someone applies to join
        
        Args:
            application: TeamMember instance (status='pending')
            team: Team instance
        
        Requirement: 5.3
        """
        Notification.create_notification(
            user=team.captain,
            title=f"New Team Application",
            message=f"{application.user.get_display_name()} has applied to join {team.name}.",
            notification_type='team',
            priority='normal',
            content_object=application,
            action_url=f'/teams/{team.slug}/roster/',
            delivery_methods=['in_app', 'email'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'applicant_id': str(application.user.id),
                'applicant_name': application.user.get_display_name(),
            }
        )
    
    @classmethod
    def notify_application_approved(cls, member, team):
        """
        Notify user when their application is approved
        
        Args:
            member: TeamMember instance
            team: Team instance
        
        Requirement: 5.3
        """
        Notification.create_notification(
            user=member.user,
            title=f"Application Approved",
            message=f"Your application to join {team.name} has been approved! Welcome to the team.",
            notification_type='team',
            priority='normal',
            content_object=team,
            action_url=f'/teams/{team.slug}/',
            delivery_methods=['in_app', 'email'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
            }
        )
    
    @classmethod
    def notify_application_declined(cls, user, team):
        """
        Notify user when their application is declined
        
        Args:
            user: User instance
            team: Team instance
        
        Requirement: 5.3
        """
        Notification.create_notification(
            user=user,
            title=f"Application Declined",
            message=f"Your application to join {team.name} has been declined.",
            notification_type='team',
            priority='low',
            content_object=team,
            action_url=f'/teams/',
            delivery_methods=['in_app'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
            }
        )
    
    # ========================================================================
    # Team Announcements (Requirement 9.2)
    # ========================================================================
    
    @classmethod
    def notify_team_announcement(cls, announcement, team, posted_by):
        """
        Notify all active team members about a new announcement
        
        Args:
            announcement: TeamAnnouncement instance
            team: Team instance
            posted_by: User who posted the announcement
        
        Requirement: 9.2
        """
        active_members = team.members.filter(status='active').select_related('user')
        
        # Set notification priority based on announcement priority
        priority_mapping = {
            'urgent': 'high',
            'important': 'normal',
            'normal': 'low'
        }
        notif_priority = priority_mapping.get(announcement.priority, 'normal')
        
        # Use email for urgent announcements
        delivery_methods = ['in_app', 'email'] if announcement.priority == 'urgent' else ['in_app']
        
        for member in active_members:
            # Don't notify the person who posted the announcement
            if member.user != posted_by:
                Notification.create_notification(
                    user=member.user,
                    title=f"New Team Announcement: {announcement.title}",
                    message=f"{posted_by.get_display_name()} posted an announcement in {team.name}.",
                    notification_type='team',
                    priority=notif_priority,
                    content_object=announcement,
                    action_url=f'/teams/{team.slug}/announcements/',
                    delivery_methods=delivery_methods,
                    metadata={
                        'team_id': str(team.id),
                        'team_name': team.name,
                        'announcement_id': str(announcement.id),
                        'announcement_priority': announcement.priority,
                        'posted_by_id': str(posted_by.id),
                        'posted_by_name': posted_by.get_display_name(),
                    }
                )
    
    # ========================================================================
    # Role Changes
    # ========================================================================
    
    @classmethod
    def notify_role_change(cls, member, old_role, new_role, team):
        """
        Notify user when their team role changes
        
        Args:
            member: TeamMember instance
            old_role: Previous role
            new_role: New role
            team: Team instance
        """
        role_display = {
            'captain': 'Captain',
            'co_captain': 'Co-Captain',
            'member': 'Member',
            'substitute': 'Substitute'
        }
        
        old_role_name = role_display.get(old_role, old_role)
        new_role_name = role_display.get(new_role, new_role)
        
        # Higher priority for promotions
        priority = 'high' if new_role in ['captain', 'co_captain'] else 'normal'
        
        Notification.create_notification(
            user=member.user,
            title=f"Your role in {team.name} has changed",
            message=f"Your role has been changed from {old_role_name} to {new_role_name}.",
            notification_type='team',
            priority=priority,
            content_object=team,
            action_url=f'/teams/{team.slug}/',
            delivery_methods=['in_app', 'email'] if priority == 'high' else ['in_app'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'old_role': old_role,
                'new_role': new_role,
            }
        )
    
    @classmethod
    def notify_captaincy_transfer(cls, new_captain, team, transferred_by):
        """
        Notify user when they become team captain
        
        Args:
            new_captain: User instance
            team: Team instance
            transferred_by: User who transferred captaincy
        """
        Notification.create_notification(
            user=new_captain,
            title=f"You are now captain of {team.name}",
            message=f"{transferred_by.get_display_name()} has transferred team captaincy to you.",
            notification_type='team',
            priority='high',
            content_object=team,
            action_url=f'/teams/{team.slug}/',
            delivery_methods=['in_app', 'email'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'transferred_by_id': str(transferred_by.id),
                'transferred_by_name': transferred_by.get_display_name(),
            }
        )
    
    # ========================================================================
    # Team Events (Tournament Registration, Starts, Wins)
    # ========================================================================
    
    @classmethod
    def notify_tournament_registration(cls, team, tournament, registered_by):
        """
        Notify all team members when team is registered for a tournament
        
        Args:
            team: Team instance
            tournament: Tournament instance
            registered_by: User who registered the team
        """
        active_members = team.members.filter(status='active').select_related('user')
        
        for member in active_members:
            # Don't notify the person who registered
            if member.user != registered_by:
                Notification.create_notification(
                    user=member.user,
                    title=f"Team registered for {tournament.name}",
                    message=f"{team.name} has been registered for {tournament.name} by {registered_by.get_display_name()}.",
                    notification_type='tournament',
                    priority='normal',
                    content_object=tournament,
                    action_url=f'/tournaments/{tournament.slug}/',
                    delivery_methods=['in_app'],
                    metadata={
                        'team_id': str(team.id),
                        'team_name': team.name,
                        'tournament_id': str(tournament.id),
                        'tournament_name': tournament.name,
                        'registered_by_id': str(registered_by.id),
                        'registered_by_name': registered_by.get_display_name(),
                    }
                )
    
    @classmethod
    def notify_tournament_starting(cls, team, tournament):
        """
        Notify all team members when their tournament is about to start
        
        Args:
            team: Team instance
            tournament: Tournament instance
        """
        active_members = team.members.filter(status='active').select_related('user')
        
        for member in active_members:
            Notification.create_notification(
                user=member.user,
                title=f"Tournament starting soon: {tournament.name}",
                message=f"Your team {team.name} has a tournament starting soon!",
                notification_type='tournament',
                priority='high',
                content_object=tournament,
                action_url=f'/tournaments/{tournament.slug}/',
                delivery_methods=['in_app', 'email'],
                metadata={
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'tournament_id': str(tournament.id),
                    'tournament_name': tournament.name,
                }
            )
    
    @classmethod
    def notify_tournament_win(cls, team, tournament):
        """
        Notify all team members when team wins a tournament
        
        Args:
            team: Team instance
            tournament: Tournament instance
        """
        active_members = team.members.filter(status='active').select_related('user')
        
        for member in active_members:
            Notification.create_notification(
                user=member.user,
                title=f"🏆 {team.name} won {tournament.name}!",
                message=f"Congratulations! Your team has won {tournament.name}!",
                notification_type='tournament',
                priority='high',
                content_object=tournament,
                action_url=f'/teams/{team.slug}/',
                delivery_methods=['in_app', 'email'],
                metadata={
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'tournament_id': str(tournament.id),
                    'tournament_name': tournament.name,
                }
            )
    
    # ========================================================================
    # Team Achievements (Requirement 15.4)
    # ========================================================================
    
    @classmethod
    def notify_achievement_earned(cls, team, achievement):
        """
        Notify all active team members when team earns an achievement
        
        Args:
            team: Team instance
            achievement: TeamAchievement instance
        
        Requirement: 15.4
        """
        active_members = team.members.filter(status='active').select_related('user')
        
        for member in active_members:
            Notification.create_notification(
                user=member.user,
                title=f"🏆 New Achievement Unlocked!",
                message=f"{team.name} earned: {achievement.title} - {achievement.description}",
                notification_type='team',
                priority='normal',
                content_object=achievement,
                action_url=f'/teams/{team.slug}/',
                delivery_methods=['in_app'],
                metadata={
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'achievement_id': str(achievement.id),
                    'achievement_type': achievement.achievement_type,
                    'achievement_title': achievement.title,
                }
            )
    
    # ========================================================================
    # Roster Changes (Joins, Leaves, Removals)
    # ========================================================================
    
    @classmethod
    def notify_member_joined(cls, team, new_member):
        """
        Notify team captain when a new member joins
        
        Args:
            team: Team instance
            new_member: User instance who joined
        """
        Notification.create_notification(
            user=team.captain,
            title=f"{new_member.get_display_name()} joined {team.name}",
            message=f"{new_member.get_display_name()} has joined your team.",
            notification_type='team',
            priority='normal',
            content_object=team,
            action_url=f'/teams/{team.slug}/roster/',
            delivery_methods=['in_app'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'user_id': str(new_member.id),
                'user_name': new_member.get_display_name(),
            }
        )
    
    @classmethod
    def notify_member_left(cls, team, left_member, all_members=False):
        """
        Notify team captain (or all members) when someone leaves
        
        Args:
            team: Team instance
            left_member: User instance who left
            all_members: If True, notify all members instead of just captain
        """
        if all_members:
            # Notify all active members
            active_members = team.members.filter(status='active').select_related('user')
            for member in active_members:
                if member.user != left_member:
                    Notification.create_notification(
                        user=member.user,
                        title=f"{left_member.get_display_name()} left {team.name}",
                        message=f"{left_member.get_display_name()} has left the team.",
                        notification_type='team',
                        priority='low',
                        content_object=team,
                        action_url=f'/teams/{team.slug}/',
                        delivery_methods=['in_app'],
                        metadata={
                            'team_id': str(team.id),
                            'team_name': team.name,
                            'user_id': str(left_member.id),
                            'user_name': left_member.get_display_name(),
                        }
                    )
        else:
            # Notify only captain
            Notification.create_notification(
                user=team.captain,
                title=f"{left_member.get_display_name()} left {team.name}",
                message=f"{left_member.get_display_name()} has left the team.",
                notification_type='team',
                priority='normal',
                content_object=team,
                action_url=f'/teams/{team.slug}/roster/',
                delivery_methods=['in_app'],
                metadata={
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'user_id': str(left_member.id),
                    'user_name': left_member.get_display_name(),
                }
            )
    
    @classmethod
    def notify_member_removed(cls, removed_member, team, removed_by):
        """
        Notify user when they are removed from a team
        
        Args:
            removed_member: User instance who was removed
            team: Team instance
            removed_by: User who removed them
        """
        Notification.create_notification(
            user=removed_member,
            title=f"Removed from {team.name}",
            message=f"You have been removed from {team.name} by {removed_by.get_display_name()}.",
            notification_type='team',
            priority='normal',
            content_object=team,
            action_url='/teams/',
            delivery_methods=['in_app', 'email'],
            metadata={
                'team_id': str(team.id),
                'team_name': team.name,
                'removed_by_id': str(removed_by.id),
                'removed_by_name': removed_by.get_display_name(),
            }
        )
    
    @classmethod
    def notify_team_disbanded(cls, team, disbanded_by, members):
        """
        Notify all members when team is disbanded
        
        Args:
            team: Team instance
            disbanded_by: User who disbanded the team
            members: List of TeamMember instances
        """
        for member in members:
            if member.user != disbanded_by:
                Notification.create_notification(
                    user=member.user,
                    title=f"{team.name} has been disbanded",
                    message=f"Team captain {disbanded_by.get_display_name()} has disbanded the team.",
                    notification_type='team',
                    priority='normal',
                    content_object=team,
                    action_url='/teams/',
                    delivery_methods=['in_app', 'email'],
                    metadata={
                        'team_id': str(team.id),
                        'team_name': team.name,
                        'disbanded_by_id': str(disbanded_by.id),
                        'disbanded_by_name': disbanded_by.get_display_name(),
                    }
                )
