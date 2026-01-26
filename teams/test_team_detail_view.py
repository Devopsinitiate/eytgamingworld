"""
Integration tests for team detail view
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from teams.models import Team, TeamMember, TeamAnnouncement, TeamAchievement
from tournaments.models import Tournament, Participant
from core.models import User, Game


class TeamDetailViewTest(TestCase):
    """Test team detail view functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a game
        self.game = Game.objects.create(
            name="Test Game",
            slug="test-game",
            description="Test game description"
        )
        
        # Create users
        self.captain = User.objects.create_user(
            username="captain",
            email="captain@test.com",
            password="testpass123"
        )
        self.captain.is_active = True
        self.captain.save()
        
        self.member = User.objects.create_user(
            username="member",
            email="member@test.com",
            password="testpass123"
        )
        self.member.is_active = True
        self.member.save()
        
        self.non_member = User.objects.create_user(
            username="nonmember",
            email="nonmember@test.com",
            password="testpass123"
        )
        self.non_member.is_active = True
        self.non_member.save()
        
        # Create a public team
        self.public_team = Team.objects.create(
            name="Public Team",
            tag="PUB",
            game=self.game,
            captain=self.captain,
            is_public=True,
            description="A public test team"
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=self.public_team,
            user=self.captain,
            role='captain',
            status='active'
        )
        
        # Create member membership
        TeamMember.objects.create(
            team=self.public_team,
            user=self.member,
            role='member',
            status='active'
        )
        
        # Create a private team
        self.private_team = Team.objects.create(
            name="Private Team",
            tag="PRIV",
            game=self.game,
            captain=self.captain,
            is_public=False,
            description="A private test team"
        )
        
        # Create captain membership for private team
        TeamMember.objects.create(
            team=self.private_team,
            user=self.captain,
            role='captain',
            status='active'
        )
        
        self.client = Client()
    
    def test_public_team_accessible_to_all(self):
        """Test that public teams are accessible to everyone"""
        # Unauthenticated user
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_team.name)
        
        # Authenticated non-member
        self.client.login(username='nonmember', password='testpass123')
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_team.name)
    
    def test_private_team_access_control(self):
        """Test that private teams enforce access control"""
        # Unauthenticated user should be redirected
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.private_team.slug}))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Authenticated non-member should be redirected
        self.client.force_login(self.non_member)
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.private_team.slug}))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Authenticated member should have access
        self.client.force_login(self.captain)
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.private_team.slug}))
        self.assertEqual(response.status_code, 200, f"Captain should have access to private team. Response: {response.status_code}")
        self.assertContains(response, self.private_team.name)
    
    def test_roster_display(self):
        """Test that roster displays only active members"""
        # Create an inactive member
        inactive_user = User.objects.create_user(
            username="inactive",
            email="inactive@test.com",
            password="testpass123"
        )
        TeamMember.objects.create(
            team=self.public_team,
            user=inactive_user,
            role='member',
            status='inactive'
        )
        
        # Get the page
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Check that active members are displayed
        self.assertContains(response, self.captain.get_display_name())
        self.assertContains(response, self.member.get_display_name())
        
        # Check that inactive member is NOT displayed
        self.assertNotContains(response, inactive_user.get_display_name())
    
    def test_team_stats_display(self):
        """Test that team statistics are displayed correctly"""
        # Update team stats
        self.public_team.tournaments_played = 5
        self.public_team.tournaments_won = 2
        self.public_team.total_wins = 10
        self.public_team.total_losses = 5
        self.public_team.save()
        
        # Get the page
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Check that stats are displayed
        self.assertContains(response, '5')  # tournaments played
        self.assertContains(response, '2')  # tournaments won
        self.assertContains(response, '66.67')  # win rate
    
    def test_action_buttons_for_member(self):
        """Test that correct action buttons are shown for members"""
        # Login as member
        self.client.force_login(self.member)
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Should show "Leave Team" button
        self.assertContains(response, 'Leave Team')
        
        # Should NOT show "Manage Team" button (not captain)
        self.assertNotContains(response, 'Manage Team')
    
    def test_action_buttons_for_captain(self):
        """Test that correct action buttons are shown for captain"""
        # Login as captain
        self.client.force_login(self.captain)
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Should show both "Manage Team" and "Leave Team" buttons
        self.assertContains(response, 'Manage Team')
        self.assertContains(response, 'Leave Team')
    
    def test_action_buttons_for_non_member(self):
        """Test that correct action buttons are shown for non-members"""
        # Login as non-member
        self.client.force_login(self.non_member)
        
        # Set team to recruiting
        self.public_team.is_recruiting = True
        self.public_team.save()
        
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.public_team.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Should show "Apply to Join" button
        self.assertContains(response, 'Apply to Join')
        
        # Should NOT show member-only buttons
        self.assertNotContains(response, 'Leave Team')
        self.assertNotContains(response, 'Manage Team')
