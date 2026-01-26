from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from teams.models import Team, TeamMember
from core.models import User, Game


class TeamSettingsViewTests(TestCase):
    """Unit tests for team settings functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test game
        self.game = Game.objects.create(
            name="Test Game",
            slug="test-game",
            description="Test game description"
        )
        
        # Create a captain user
        self.captain = User.objects.create_user(
            username="captain",
            email="captain@test.com",
            password="testpass123"
        )
        
        # Create a regular member user
        self.member = User.objects.create_user(
            username="member",
            email="member@test.com",
            password="testpass123"
        )
        
        # Create a non-member user
        self.non_member = User.objects.create_user(
            username="nonmember",
            email="nonmember@test.com",
            password="testpass123"
        )
        
        # Create a team
        self.team = Team.objects.create(
            name="Test Team",
            tag="TEST",
            game=self.game,
            captain=self.captain,
            description="Test team description",
            max_members=10,
            is_recruiting=True,
            is_public=True,
            requires_approval=False
        )
        
        # Create captain membership
        self.captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.captain,
            role='captain',
            status='active',
            approved_at=timezone.now()
        )
        
        # Create regular member membership
        self.member_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member,
            role='member',
            status='active',
            approved_at=timezone.now()
        )
        
        self.client = Client()
    
    def test_captain_can_access_settings(self):
        """Test that captain can access team settings page (Requirement 12.1)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        response = self.client.get(url)
        
        # Check if redirected (might be due to missing permissions)
        if response.status_code == 302:
            print(f"Redirected to: {response.url}")
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Settings')
        self.assertContains(response, self.team.name)
    
    def test_member_cannot_access_settings(self):
        """Test that regular member cannot access team settings (Requirement 12.2)"""
        self.client.force_login(self.member)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        response = self.client.get(url)
        
        # Should be redirected or forbidden
        self.assertNotEqual(response.status_code, 200)
    
    def test_non_member_cannot_access_settings(self):
        """Test that non-member cannot access team settings (Requirement 12.1)"""
        self.client.force_login(self.non_member)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        response = self.client.get(url)
        
        # Should be redirected or forbidden
        self.assertNotEqual(response.status_code, 200)
    
    def test_captain_can_update_team_info(self):
        """Test that captain can update team information (Requirement 7.2)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Update team information (include all required fields)
        response = self.client.post(url, {
            'name': 'Updated Team Name',
            'tag': 'UPDT',
            'description': 'Updated description',
            'max_members': 15,
            'is_recruiting': 'false',  # Use string for checkbox
            'is_public': 'on',  # Use 'on' for checked checkbox
            'requires_approval': 'on',  # Use 'on' for checked checkbox
        }, follow=True)
        
        # Refresh team from database
        self.team.refresh_from_db()
        
        # Verify updates
        self.assertEqual(self.team.name, 'Updated Team Name')
        self.assertEqual(self.team.tag, 'UPDT')
        self.assertEqual(self.team.description, 'Updated description')
        self.assertEqual(self.team.max_members, 15)
        self.assertEqual(self.team.requires_approval, True)
    
    def test_captain_can_toggle_recruiting(self):
        """Test that captain can toggle recruiting status (Requirement 7.4)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Toggle recruiting off (don't include is_recruiting to uncheck it)
        response = self.client.post(url, {
            'name': self.team.name,
            'tag': self.team.tag,
            'description': self.team.description,
            'max_members': self.team.max_members,
            # is_recruiting not included = unchecked
            'is_public': 'on',
            # requires_approval not included = unchecked
        }, follow=True)
        
        self.team.refresh_from_db()
        self.assertEqual(self.team.is_recruiting, False)
    
    def test_captain_can_toggle_approval_requirement(self):
        """Test that captain can toggle approval requirement (Requirement 7.4)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Toggle requires_approval on
        response = self.client.post(url, {
            'name': self.team.name,
            'tag': self.team.tag,
            'description': self.team.description,
            'max_members': self.team.max_members,
            'is_recruiting': 'on',
            'is_public': 'on',
            'requires_approval': 'on',  # Toggle on
        }, follow=True)
        
        self.team.refresh_from_db()
        self.assertEqual(self.team.requires_approval, True)
    
    def test_captain_can_toggle_public_status(self):
        """Test that captain can toggle public status (Requirement 7.4)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Toggle is_public off (don't include is_public to uncheck it)
        response = self.client.post(url, {
            'name': self.team.name,
            'tag': self.team.tag,
            'description': self.team.description,
            'max_members': self.team.max_members,
            'is_recruiting': 'on',
            # is_public not included = unchecked
            # requires_approval not included = unchecked
        }, follow=True)
        
        self.team.refresh_from_db()
        self.assertEqual(self.team.is_public, False)
    
    def test_cannot_update_with_duplicate_name(self):
        """Test that team name must remain unique"""
        # Create another team
        other_team = Team.objects.create(
            name="Other Team",
            tag="OTHR",
            game=self.game,
            captain=self.captain,
            max_members=10
        )
        
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Try to update to duplicate name
        response = self.client.post(url, {
            'name': 'Other Team',  # Duplicate name
            'tag': self.team.tag,
            'description': self.team.description,
            'max_members': self.team.max_members,
            'is_recruiting': 'on',
            'is_public': 'on',
        })
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'name', 'A team with this name already exists.')
    
    def test_cannot_update_with_duplicate_tag(self):
        """Test that team tag must remain unique"""
        # Create another team
        other_team = Team.objects.create(
            name="Other Team",
            tag="OTHR",
            game=self.game,
            captain=self.captain,
            max_members=10
        )
        
        self.client.force_login(self.captain)
        
        url = reverse('teams:settings', kwargs={'slug': self.team.slug})
        
        # Try to update to duplicate tag
        response = self.client.post(url, {
            'name': self.team.name,
            'tag': 'OTHR',  # Duplicate tag
            'description': self.team.description,
            'max_members': self.team.max_members,
            'is_recruiting': 'on',
            'is_public': 'on',
        })
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'tag', 'A team with this tag already exists.')


class TeamTransferCaptaincyTests(TestCase):
    """Unit tests for transfer captaincy functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test game
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
        
        self.member = User.objects.create_user(
            username="member",
            email="member@test.com",
            password="testpass123"
        )
        
        # Create a team
        self.team = Team.objects.create(
            name="Test Team",
            tag="TEST",
            game=self.game,
            captain=self.captain,
            max_members=10
        )
        
        # Create memberships
        self.captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.captain,
            role='captain',
            status='active',
            approved_at=timezone.now()
        )
        
        self.member_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member,
            role='member',
            status='active',
            approved_at=timezone.now()
        )
        
        self.client = Client()
    
    def test_captain_can_transfer_captaincy(self):
        """Test that captain can transfer captaincy to another member (Requirement 7.5)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:transfer_captaincy', kwargs={'slug': self.team.slug})
        
        response = self.client.post(url, {
            'new_captain': str(self.member_membership.id)
        })
        
        # Refresh from database
        self.team.refresh_from_db()
        self.captain_membership.refresh_from_db()
        self.member_membership.refresh_from_db()
        
        # Verify transfer
        self.assertEqual(self.team.captain, self.member)
        self.assertEqual(self.member_membership.role, 'captain')
        self.assertEqual(self.captain_membership.role, 'member')


class TeamDisbandTests(TestCase):
    """Unit tests for team disband functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test game
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
        
        self.member1 = User.objects.create_user(
            username="member1",
            email="member1@test.com",
            password="testpass123"
        )
        
        self.member2 = User.objects.create_user(
            username="member2",
            email="member2@test.com",
            password="testpass123"
        )
        
        # Create a team
        self.team = Team.objects.create(
            name="Test Team",
            tag="TEST",
            game=self.game,
            captain=self.captain,
            max_members=10
        )
        
        # Create memberships
        TeamMember.objects.create(
            team=self.team,
            user=self.captain,
            role='captain',
            status='active',
            approved_at=timezone.now()
        )
        
        TeamMember.objects.create(
            team=self.team,
            user=self.member1,
            role='member',
            status='active',
            approved_at=timezone.now()
        )
        
        TeamMember.objects.create(
            team=self.team,
            user=self.member2,
            role='member',
            status='active',
            approved_at=timezone.now()
        )
        
        self.client = Client()
    
    def test_captain_can_disband_team(self):
        """Test that captain can disband team (Requirement 7.5)"""
        self.client.force_login(self.captain)
        
        url = reverse('teams:disband', kwargs={'slug': self.team.slug})
        
        response = self.client.post(url)
        
        # Refresh from database
        self.team.refresh_from_db()
        
        # Verify team is disbanded
        self.assertEqual(self.team.status, 'disbanded')
        
        # Verify all members are inactive
        active_members = self.team.members.filter(status='active').count()
        self.assertEqual(active_members, 0)
        
        inactive_members = self.team.members.filter(status='inactive').count()
        self.assertEqual(inactive_members, 3)  # Captain + 2 members
