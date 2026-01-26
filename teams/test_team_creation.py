"""
Integration tests for team creation flow
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from teams.models import Team, TeamMember
from core.models import User, Game


class TeamCreationIntegrationTest(TestCase):
    """Test the complete team creation flow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test game
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game',
            genre='fps',
            description='A test game'
        )
    
    def test_team_creation_success(self):
        """Test successful team creation"""
        # Login
        self.client.login(email='test@example.com', password='testpass123')
        
        # Submit team creation form
        response = self.client.post(reverse('teams:create'), {
            'name': 'Test Team',
            'tag': 'TST',
            'game': self.game.id,
            'description': 'A test team for testing',
            'max_members': 10,
            'requires_approval': True,
            'is_recruiting': True,
            'is_public': True,
        })
        
        # Should redirect to team detail page
        self.assertEqual(response.status_code, 302)
        
        # Verify team was created
        team = Team.objects.filter(name='Test Team').first()
        self.assertIsNotNone(team)
        self.assertEqual(team.tag, 'TST')
        self.assertEqual(team.captain, self.user)
        self.assertEqual(team.status, 'active')
        
        # Verify captain membership was created
        membership = TeamMember.objects.filter(team=team, user=self.user).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, 'captain')
        self.assertEqual(membership.status, 'active')
        self.assertIsNotNone(membership.approved_at)
    
    def test_team_creation_duplicate_name(self):
        """Test team creation with duplicate name fails"""
        # Create an existing team
        captain = User.objects.create_user(
            username='captain',
            email='captain@example.com',
            password='testpass123'
        )
        
        Team.objects.create(
            name='Existing Team',
            tag='EXT',
            game=self.game,
            captain=captain
        )
        
        # Login as different user
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to create team with same name
        response = self.client.post(reverse('teams:create'), {
            'name': 'Existing Team',
            'tag': 'NEW',
            'game': self.game.id,
            'description': 'A test team',
            'max_members': 10,
        })
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Should show error message
        self.assertContains(response, 'A team with this name already exists')
    
    def test_team_creation_duplicate_tag(self):
        """Test team creation with duplicate tag fails"""
        # Create an existing team
        captain = User.objects.create_user(
            username='captain',
            email='captain@example.com',
            password='testpass123'
        )
        
        Team.objects.create(
            name='Existing Team',
            tag='DUP',
            game=self.game,
            captain=captain
        )
        
        # Login as different user
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to create team with same tag
        response = self.client.post(reverse('teams:create'), {
            'name': 'New Team',
            'tag': 'DUP',
            'game': self.game.id,
            'description': 'A test team',
            'max_members': 10,
        })
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Should show error message
        self.assertContains(response, 'A team with this tag already exists')
    
    def test_team_creation_invalid_tag_format(self):
        """Test team creation with invalid tag format fails"""
        # Login
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to create team with invalid tag (contains special characters)
        response = self.client.post(reverse('teams:create'), {
            'name': 'Test Team',
            'tag': 'T$T!',
            'game': self.game.id,
            'description': 'A test team',
            'max_members': 10,
        })
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Should show error message
        self.assertContains(response, 'Team tag can only contain letters and numbers')
    
    def test_team_creation_tag_too_short(self):
        """Test team creation with tag too short fails"""
        # Login
        self.client.login(email='test@example.com', password='testpass123')
        
        # Try to create team with tag that's too short
        response = self.client.post(reverse('teams:create'), {
            'name': 'Test Team',
            'tag': 'T',
            'game': self.game.id,
            'description': 'A test team',
            'max_members': 10,
        })
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Should show error message
        self.assertContains(response, 'Team tag must be between 2 and 10 characters')
    
    def test_team_creation_requires_authentication(self):
        """Test team creation requires user to be logged in"""
        # Try to access create page without login
        response = self.client.get(reverse('teams:create'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
