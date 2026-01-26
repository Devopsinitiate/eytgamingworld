"""
Tests for Team Notification Service

This module tests the notification triggers for team events.
Requirements: 4.3, 5.3, 9.2, 15.4
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.models import User, Game
from teams.models import Team, TeamMember, TeamInvite, TeamAnnouncement, TeamAchievement
from teams.notification_service import TeamNotificationService
from notifications.models import Notification


class TeamNotificationServiceTest(TestCase):
    """Test team notification service"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.captain = User.objects.create_user(
            username='captain',
            email='captain@test.com',
            password='testpass123'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='testpass123'
        )
        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='testpass123'
        )
        self.applicant = User.objects.create_user(
            username='applicant',
            email='applicant@test.com',
            password='testpass123'
        )
        
        # Create game
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game'
        )
        
        # Create team
        self.team = Team.objects.create(
            name='Test Team',
            slug='test-team',
            tag='TT',
            game=self.game,
            captain=self.captain,
            status='active'
        )
        
        # Create team members
        TeamMember.objects.create(
            team=self.team,
            user=self.captain,
            role='captain',
            status='active'
        )
        TeamMember.objects.create(
            team=self.team,
            user=self.member1,
            role='member',
            status='active'
        )
        TeamMember.objects.create(
            team=self.team,
            user=self.member2,
            role='member',
            status='active'
        )
    
    def test_notify_team_invite(self):
        """Test team invitation notification (Requirement 4.3)"""
        # Create invite
        invite = TeamInvite.objects.create(
            team=self.team,
            invited_by=self.captain,
            invited_user=self.applicant,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Send notification
        TeamNotificationService.notify_team_invite(invite, self.captain)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.applicant,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn(self.team.name, notification.title)
        self.assertEqual(notification.priority, 'normal')
    
    def test_notify_new_application(self):
        """Test application notification to captain (Requirement 5.3)"""
        # Create application
        application = TeamMember.objects.create(
            team=self.team,
            user=self.applicant,
            role='member',
            status='pending'
        )
        
        # Send notification
        TeamNotificationService.notify_new_application(application, self.team)
        
        # Check notification was created for captain
        notification = Notification.objects.filter(
            user=self.captain,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Application', notification.title)
        self.assertEqual(notification.priority, 'normal')
    
    def test_notify_application_approved(self):
        """Test application approval notification (Requirement 5.3)"""
        # Create member
        member = TeamMember.objects.create(
            team=self.team,
            user=self.applicant,
            role='member',
            status='active'
        )
        
        # Send notification
        TeamNotificationService.notify_application_approved(member, self.team)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.applicant,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Approved', notification.title)
        self.assertEqual(notification.priority, 'normal')
    
    def test_notify_team_announcement(self):
        """Test team announcement notifications (Requirement 9.2)"""
        # Create announcement
        announcement = TeamAnnouncement.objects.create(
            team=self.team,
            posted_by=self.captain,
            title='Test Announcement',
            content='This is a test',
            priority='important'
        )
        
        # Send notifications
        TeamNotificationService.notify_team_announcement(announcement, self.team, self.captain)
        
        # Check notifications were created for all members except captain
        notifications = Notification.objects.filter(
            notification_type='team'
        )
        
        # Should have 2 notifications (member1 and member2, not captain)
        self.assertEqual(notifications.count(), 2)
        
        # Check captain didn't receive notification
        captain_notification = notifications.filter(user=self.captain).first()
        self.assertIsNone(captain_notification)
        
        # Check members received notifications
        member1_notification = notifications.filter(user=self.member1).first()
        self.assertIsNotNone(member1_notification)
        self.assertIn('Announcement', member1_notification.title)
    
    def test_notify_team_announcement_urgent_priority(self):
        """Test urgent announcement uses email delivery (Requirement 9.2)"""
        # Create urgent announcement
        announcement = TeamAnnouncement.objects.create(
            team=self.team,
            posted_by=self.captain,
            title='Urgent Announcement',
            content='This is urgent',
            priority='urgent'
        )
        
        # Send notifications
        TeamNotificationService.notify_team_announcement(announcement, self.team, self.captain)
        
        # Check notification priority and delivery methods
        notification = Notification.objects.filter(
            user=self.member1,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.priority, 'high')
        self.assertIn('email', notification.delivery_methods)
    
    def test_notify_role_change(self):
        """Test role change notification"""
        # Get member
        member = TeamMember.objects.get(team=self.team, user=self.member1)
        
        # Send notification
        TeamNotificationService.notify_role_change(member, 'member', 'co_captain', self.team)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.member1,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('role', notification.title.lower())
        self.assertEqual(notification.priority, 'high')  # Promotion to co-captain
    
    def test_notify_captaincy_transfer(self):
        """Test captaincy transfer notification"""
        # Send notification
        TeamNotificationService.notify_captaincy_transfer(self.member1, self.team, self.captain)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.member1,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('captain', notification.title.lower())
        self.assertEqual(notification.priority, 'high')
        self.assertIn('email', notification.delivery_methods)
    
    def test_notify_member_removed(self):
        """Test member removal notification"""
        # Send notification
        TeamNotificationService.notify_member_removed(self.member1, self.team, self.captain)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.member1,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Removed', notification.title)
        self.assertIn('email', notification.delivery_methods)
    
    def test_notify_team_disbanded(self):
        """Test team disbanded notifications"""
        # Get all active members
        active_members = list(self.team.members.filter(status='active'))
        
        # Send notifications
        TeamNotificationService.notify_team_disbanded(self.team, self.captain, active_members)
        
        # Check notifications were created for all members except captain
        notifications = Notification.objects.filter(
            notification_type='team'
        )
        
        # Should have 2 notifications (member1 and member2, not captain)
        self.assertEqual(notifications.count(), 2)
        
        # Check all notifications mention disbanded
        for notification in notifications:
            self.assertIn('disbanded', notification.title.lower())
    
    def test_notify_achievement_earned(self):
        """Test achievement notification (Requirement 15.4)"""
        # Create achievement
        achievement = TeamAchievement.objects.create(
            team=self.team,
            achievement_type='first_win',
            title='First Victory',
            description='Won your first tournament',
            icon='🏆'
        )
        
        # Send notifications
        TeamNotificationService.notify_achievement_earned(self.team, achievement)
        
        # Check notifications were created for all active members
        notifications = Notification.objects.filter(
            notification_type='team'
        )
        
        # Should have 3 notifications (captain, member1, member2)
        self.assertEqual(notifications.count(), 3)
        
        # Check notification content
        notification = notifications.first()
        self.assertIn('Achievement', notification.title)
        self.assertIn(achievement.title, notification.message)
    
    def test_notify_member_joined(self):
        """Test member joined notification"""
        # Create new user
        new_member = User.objects.create_user(
            username='newmember',
            email='newmember@test.com',
            password='testpass123'
        )
        
        # Send notification
        TeamNotificationService.notify_member_joined(self.team, new_member)
        
        # Check notification was created for captain
        notification = Notification.objects.filter(
            user=self.captain,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('joined', notification.title.lower())
        self.assertIn(new_member.get_display_name(), notification.title)
    
    def test_notify_member_left(self):
        """Test member left notification"""
        # Send notification
        TeamNotificationService.notify_member_left(self.team, self.member1)
        
        # Check notification was created for captain
        notification = Notification.objects.filter(
            user=self.captain,
            notification_type='team'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('left', notification.title.lower())
        self.assertIn(self.member1.get_display_name(), notification.title)
    
    def test_notify_tournament_registration(self):
        """Test tournament registration notification"""
        # Create mock tournament
        from tournaments.models import Tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.captain,
            status='registration',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=7),
            check_in_start=timezone.now() + timedelta(days=7),
            start_datetime=timezone.now() + timedelta(days=8),
            max_participants=16,
            is_team_based=True,
            team_size=3
        )
        
        # Send notifications
        TeamNotificationService.notify_tournament_registration(self.team, tournament, self.captain)
        
        # Check notifications were created for all members except captain
        notifications = Notification.objects.filter(
            notification_type='tournament'
        )
        
        # Should have 2 notifications (member1 and member2, not captain)
        self.assertEqual(notifications.count(), 2)
        
        # Check notification content
        notification = notifications.first()
        self.assertIn('registered', notification.title.lower())
        self.assertIn(tournament.name, notification.title)
    
    def test_notify_tournament_starting(self):
        """Test tournament starting notification"""
        # Create mock tournament
        from tournaments.models import Tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.captain,
            status='in_progress',
            registration_start=timezone.now() - timedelta(days=8),
            registration_end=timezone.now() - timedelta(days=1),
            check_in_start=timezone.now() - timedelta(hours=2),
            start_datetime=timezone.now(),
            max_participants=16,
            is_team_based=True,
            team_size=3
        )
        
        # Send notifications
        TeamNotificationService.notify_tournament_starting(self.team, tournament)
        
        # Check notifications were created for all active members
        notifications = Notification.objects.filter(
            notification_type='tournament'
        )
        
        # Should have 3 notifications (captain, member1, member2)
        self.assertEqual(notifications.count(), 3)
        
        # Check notification content and priority
        notification = notifications.first()
        self.assertIn('starting', notification.title.lower())
        self.assertEqual(notification.priority, 'high')
        self.assertIn('email', notification.delivery_methods)
    
    def test_notify_tournament_win(self):
        """Test tournament win notification"""
        # Create mock tournament
        from tournaments.models import Tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.captain,
            status='completed',
            registration_start=timezone.now() - timedelta(days=10),
            registration_end=timezone.now() - timedelta(days=3),
            check_in_start=timezone.now() - timedelta(days=2),
            start_datetime=timezone.now() - timedelta(days=1),
            max_participants=16,
            is_team_based=True,
            team_size=3
        )
        
        # Send notifications
        TeamNotificationService.notify_tournament_win(self.team, tournament)
        
        # Check notifications were created for all active members
        notifications = Notification.objects.filter(
            notification_type='tournament'
        )
        
        # Should have 3 notifications (captain, member1, member2)
        self.assertEqual(notifications.count(), 3)
        
        # Check notification content and priority
        notification = notifications.first()
        self.assertIn('won', notification.title.lower())
        self.assertEqual(notification.priority, 'high')
        self.assertIn('email', notification.delivery_methods)


# Integration tests would go here if needed
# The unit tests above cover the notification service functionality
