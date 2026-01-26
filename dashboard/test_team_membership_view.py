"""
Tests for team membership view.

Tests verify that the team_membership view correctly:
- Displays active team memberships
- Displays team history (left teams)
- Calculates team statistics from tournament participations
- Displays pending team invitations
- Handles users with no teams
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from core.models import User, Game
from teams.models import Team, TeamMember, TeamInvite
from tournaments.models import Tournament, Participant, Bracket, Match


@pytest.mark.django_db
class TeamMembershipViewTests(TestCase):
    """Tests for team_membership view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test game
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game',
            description='A test game'
        )
        
        # Create test teams
        self.team1 = Team.objects.create(
            name='Test Team 1',
            slug='test-team-1',
            tag='TT1',
            game=self.game,
            captain=self.user,
            status='active'
        )
        
        self.team2 = Team.objects.create(
            name='Test Team 2',
            slug='test-team-2',
            tag='TT2',
            game=self.game,
            captain=self.user,
            status='active'
        )
        
        # Create another user for invitations
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(reverse('dashboard:team_membership'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_view_with_no_teams(self):
        """Test view displays correctly when user has no teams"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No active teams')
        self.assertEqual(response.context['total_active_teams'], 0)
        self.assertEqual(response.context['total_pending_invites'], 0)
    
    def test_view_displays_active_memberships(self):
        """Test view displays active team memberships"""
        # Create active membership
        membership = TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='member',
            status='active'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_active_teams'], 1)
        self.assertIn(membership, response.context['active_memberships'])
        self.assertContains(response, 'Test Team 1')
    
    def test_view_displays_team_history(self):
        """Test view displays team history for left teams"""
        # Create inactive membership
        membership = TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='member',
            status='inactive',
            left_at=timezone.now()
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_teams_left'], 1)
        self.assertIn(membership, response.context['team_history'])
        self.assertContains(response, 'Team History')
    
    def test_view_displays_pending_invitations(self):
        """Test view displays pending team invitations"""
        # Create pending invitation
        invitation = TeamInvite.objects.create(
            team=self.team1,
            invited_by=self.other_user,
            invited_user=self.user,
            status='pending',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_pending_invites'], 1)
        self.assertIn(invitation, response.context['pending_invitations'])
        self.assertContains(response, 'Pending Invitations')
    
    def test_view_excludes_expired_invitations(self):
        """Test view does not display expired invitations"""
        # Create expired invitation
        TeamInvite.objects.create(
            team=self.team1,
            invited_by=self.other_user,
            invited_user=self.user,
            status='pending',
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_pending_invites'], 0)
    
    def test_view_calculates_team_statistics(self):
        """Test view calculates team statistics from tournament participations"""
        # Create active membership
        membership = TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='member',
            status='active'
        )
        
        # Create tournament - check Tournament model for correct fields
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=self.game,
            organizer=self.user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            status='registration'
        )
        
        # Create team participation
        participation = Participant.objects.create(
            tournament=tournament,
            team=self.team1,
            status='confirmed',
            final_placement=1
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check team stats
        team_stats = response.context['team_stats']
        self.assertEqual(len(team_stats), 1)
        self.assertEqual(team_stats[0]['total_tournaments'], 1)
        self.assertEqual(team_stats[0]['tournaments_won'], 1)
    
    def test_view_displays_multiple_teams(self):
        """Test view displays multiple active teams"""
        # Create memberships for both teams
        TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='captain',
            status='active'
        )
        
        TeamMember.objects.create(
            team=self.team2,
            user=self.user,
            role='member',
            status='active'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_active_teams'], 2)
        self.assertContains(response, 'Test Team 1')
        self.assertContains(response, 'Test Team 2')
    
    def test_view_shows_role_badges(self):
        """Test view displays role badges for captain and co-captain"""
        # Create captain membership
        TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='captain',
            status='active'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Captain')
    
    def test_view_calculates_overall_statistics(self):
        """Test view calculates overall team statistics"""
        # Create memberships
        TeamMember.objects.create(
            team=self.team1,
            user=self.user,
            role='member',
            status='active'
        )
        
        TeamMember.objects.create(
            team=self.team2,
            user=self.user,
            role='member',
            status='active'
        )
        
        # Create tournaments for both teams
        tournament1 = Tournament.objects.create(
            name='Tournament 1',
            slug='tournament-1',
            game=self.game,
            organizer=self.user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            status='registration'
        )
        
        tournament2 = Tournament.objects.create(
            name='Tournament 2',
            slug='tournament-2',
            game=self.game,
            organizer=self.user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=2),
            status='registration'
        )
        
        Participant.objects.create(
            tournament=tournament1,
            team=self.team1,
            status='confirmed',
            final_placement=1
        )
        
        Participant.objects.create(
            tournament=tournament2,
            team=self.team2,
            status='confirmed',
            final_placement=2
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:team_membership'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_team_tournaments'], 2)
        self.assertEqual(response.context['total_team_wins'], 1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
