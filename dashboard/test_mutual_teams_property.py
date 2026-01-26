"""
Property-based tests for mutual teams identification functionality.

This module tests the mutual teams identification property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from core.models import User, Game
from teams.models import Team, TeamMember
from dashboard.services import SocialService
import uuid


@pytest.mark.django_db
class TestMutualTeamsIdentification:
    """
    **Feature: user-profile-dashboard, Property 14: Mutual teams identification**
    
    For any two users, the mutual teams displayed must be exactly the set intersection 
    of teams where both users are members.
    
    **Validates: Requirements 10.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_teams=st.integers(min_value=0, max_value=8),
        user1_team_indices=st.lists(
            st.integers(min_value=0, max_value=7), 
            min_size=0, 
            max_size=6,
            unique=True
        ),
        user2_team_indices=st.lists(
            st.integers(min_value=0, max_value=7), 
            min_size=0, 
            max_size=6,
            unique=True
        )
    )
    def test_mutual_teams_set_intersection_property(self, num_teams, user1_team_indices, user2_team_indices):
        """Property: Mutual teams must be exactly the set intersection of both users' teams"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        user1 = User.objects.create_user(
            email=f'user1_{unique_id}@example.com',
            username=f'user1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'user2_{unique_id}@example.com',
            username=f'user2_{unique_id}',
            password='testpass123'
        )
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create teams
        teams = []
        for i in range(num_teams):
            team = Team.objects.create(
                name=f'Team {i} {unique_id}',
                tag=f'T{i}',
                game=game,
                captain=user1,  # Use user1 as captain for all teams
                description=f'Test team {i}',
                status='active'
            )
            teams.append(team)
        
        # Filter indices to only include valid team indices
        valid_user1_indices = [idx for idx in user1_team_indices if idx < num_teams]
        valid_user2_indices = [idx for idx in user2_team_indices if idx < num_teams]
        
        # Add user1 to their teams
        user1_teams = set()
        for idx in valid_user1_indices:
            team = teams[idx]
            # Create membership (user1 is already captain, but add explicit membership)
            TeamMember.objects.get_or_create(
                team=team,
                user=user1,
                defaults={
                    'role': 'captain',
                    'status': 'active',
                    'joined_at': timezone.now()
                }
            )
            user1_teams.add(team.id)
        
        # Add user2 to their teams
        user2_teams = set()
        for idx in valid_user2_indices:
            team = teams[idx]
            TeamMember.objects.create(
                team=team,
                user=user2,
                role='member',
                status='active',
                joined_at=timezone.now()
            )
            user2_teams.add(team.id)
        
        # Calculate expected mutual teams (set intersection)
        expected_mutual_team_ids = user1_teams.intersection(user2_teams)
        
        # Get mutual teams using the service
        mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
        actual_mutual_team_ids = {uuid.UUID(team['team_id']) for team in mutual_teams}
        
        # Property 1: Mutual teams must be exactly the set intersection
        assert actual_mutual_team_ids == expected_mutual_team_ids, \
            f"Expected mutual teams {expected_mutual_team_ids}, but got {actual_mutual_team_ids}"
        
        # Property 2: Count must match
        expected_count = len(expected_mutual_team_ids)
        actual_count = len(mutual_teams)
        assert actual_count == expected_count, \
            f"Expected {expected_count} mutual teams, but got {actual_count}"
        
        # Property 3: Each mutual team must have both users as active members
        for team_data in mutual_teams:
            team_id = uuid.UUID(team_data['team_id'])
            
            # Check user1 membership
            user1_membership = TeamMember.objects.filter(
                team_id=team_id,
                user=user1,
                status='active'
            ).exists()
            assert user1_membership, \
                f"User1 should be an active member of team {team_id}"
            
            # Check user2 membership
            user2_membership = TeamMember.objects.filter(
                team_id=team_id,
                user=user2,
                status='active'
            ).exists()
            assert user2_membership, \
                f"User2 should be an active member of team {team_id}"
        
        # Property 4: No team should appear in mutual teams if only one user is a member
        all_team_ids = {team.id for team in teams}
        non_mutual_team_ids = all_team_ids - expected_mutual_team_ids
        
        for team_id in non_mutual_team_ids:
            # This team should not appear in mutual teams
            assert team_id not in actual_mutual_team_ids, \
                f"Team {team_id} appears in mutual teams but should not"
            
            # Verify that at least one user is not a member of this team
            user1_in_team = team_id in user1_teams
            user2_in_team = team_id in user2_teams
            assert not (user1_in_team and user2_in_team), \
                f"Team {team_id} has both users but was not identified as mutual"
        
        # Cleanup - delete teams first, then game
        for team in teams:
            team.delete()
        game.delete()
        user1.delete()
        user2.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_teams=st.integers(min_value=1, max_value=6),
        overlap_ratio=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_mutual_teams_overlap_property(self, num_teams, overlap_ratio):
        """Property: Mutual teams count should match the calculated overlap"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        user1 = User.objects.create_user(
            email=f'user1_{unique_id}@example.com',
            username=f'user1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'user2_{unique_id}@example.com',
            username=f'user2_{unique_id}',
            password='testpass123'
        )
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create teams
        teams = []
        for i in range(num_teams):
            team = Team.objects.create(
                name=f'Team {i} {unique_id}',
                tag=f'T{i}',
                game=game,
                captain=user1,
                description=f'Test team {i}',
                status='active'
            )
            teams.append(team)
        
        # Calculate how many teams should overlap
        num_overlap = int(num_teams * overlap_ratio)
        
        # Add user1 to all teams
        user1_teams = set()
        for team in teams:
            TeamMember.objects.get_or_create(
                team=team,
                user=user1,
                defaults={
                    'role': 'captain',
                    'status': 'active',
                    'joined_at': timezone.now()
                }
            )
            user1_teams.add(team.id)
        
        # Add user2 to first num_overlap teams (creating overlap)
        user2_teams = set()
        for i in range(num_overlap):
            team = teams[i]
            TeamMember.objects.create(
                team=team,
                user=user2,
                role='member',
                status='active',
                joined_at=timezone.now()
            )
            user2_teams.add(team.id)
        
        # Get mutual teams
        mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
        
        # Property: Mutual teams count should equal the overlap
        assert len(mutual_teams) == num_overlap, \
            f"Expected {num_overlap} mutual teams, but got {len(mutual_teams)}"
        
        # Property: Each mutual team should be in the first num_overlap teams
        expected_team_ids = {teams[i].id for i in range(num_overlap)}
        actual_team_ids = {uuid.UUID(team['team_id']) for team in mutual_teams}
        
        assert actual_team_ids == expected_team_ids, \
            f"Expected mutual teams {expected_team_ids}, but got {actual_team_ids}"
        
        # Cleanup - delete teams first, then game
        for team in teams:
            team.delete()
        game.delete()
        user1.delete()
        user2.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_users=st.integers(min_value=3, max_value=6),
        num_teams=st.integers(min_value=2, max_value=5)
    )
    def test_mutual_teams_pairwise_property(self, num_users, num_teams):
        """Property: Mutual teams calculation should be consistent for any pair of users"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        users = []
        for i in range(num_users):
            user = User.objects.create_user(
                email=f'user{i}_{unique_id}@example.com',
                username=f'user{i}_{unique_id}',
                password='testpass123'
            )
            users.append(user)
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create teams
        teams = []
        for i in range(num_teams):
            team = Team.objects.create(
                name=f'Team {i} {unique_id}',
                tag=f'T{i}',
                game=game,
                captain=users[0],  # Use first user as captain
                description=f'Test team {i}',
                status='active'
            )
            teams.append(team)
        
        # Randomly assign users to teams
        user_team_memberships = {}
        for user_idx, user in enumerate(users):
            user_teams = set()
            
            # Each user joins a random subset of teams
            for team_idx, team in enumerate(teams):
                # Use a deterministic pattern based on user and team indices
                # This ensures reproducible test results
                if (user_idx + team_idx) % 3 == 0:  # Join roughly 1/3 of teams
                    role = 'captain' if user == users[0] else 'member'
                    TeamMember.objects.get_or_create(
                        team=team,
                        user=user,
                        defaults={
                            'role': role,
                            'status': 'active',
                            'joined_at': timezone.now()
                        }
                    )
                    user_teams.add(team.id)
            
            user_team_memberships[user.id] = user_teams
        
        # Test mutual teams for all pairs of users
        for i in range(num_users):
            for j in range(i + 1, num_users):
                user1 = users[i]
                user2 = users[j]
                
                # Calculate expected mutual teams
                user1_teams = user_team_memberships[user1.id]
                user2_teams = user_team_memberships[user2.id]
                expected_mutual = user1_teams.intersection(user2_teams)
                
                # Get mutual teams using service
                mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
                actual_mutual = {uuid.UUID(team['team_id']) for team in mutual_teams}
                
                # Property: Mutual teams should match set intersection
                assert actual_mutual == expected_mutual, \
                    f"For users {i} and {j}: expected {expected_mutual}, got {actual_mutual}"
                
                # Property: Mutual teams should be symmetric (A∩B = B∩A)
                reverse_mutual_teams = SocialService.get_mutual_teams(user2.id, user1.id)
                reverse_mutual = {uuid.UUID(team['team_id']) for team in reverse_mutual_teams}
                
                assert actual_mutual == reverse_mutual, \
                    f"Mutual teams not symmetric for users {i} and {j}: {actual_mutual} != {reverse_mutual}"
        
        # Cleanup - delete teams first, then game
        for team in teams:
            team.delete()
        game.delete()
        for user in users:
            user.delete()
    
    def test_mutual_teams_edge_case_no_teams(self):
        """Edge case: Users with no team memberships should have no mutual teams"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users with no team memberships
        user1 = User.objects.create_user(
            email=f'user1_{unique_id}@example.com',
            username=f'user1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'user2_{unique_id}@example.com',
            username=f'user2_{unique_id}',
            password='testpass123'
        )
        
        # Get mutual teams (should be empty)
        mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
        
        # Property: No mutual teams when users have no teams
        assert len(mutual_teams) == 0, \
            f"Expected 0 mutual teams for users with no teams, got {len(mutual_teams)}"
        
        # Cleanup
        user1.delete()
        user2.delete()
    
    def test_mutual_teams_edge_case_same_user(self):
        """Edge case: User compared with themselves should return all their teams"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'user_{unique_id}@example.com',
            username=f'user_{unique_id}',
            password='testpass123'
        )
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create teams and add user to them
        teams = []
        for i in range(3):
            team = Team.objects.create(
                name=f'Team {i} {unique_id}',
                tag=f'T{i}',
                game=game,
                captain=user,
                description=f'Test team {i}',
                status='active'
            )
            teams.append(team)
            
            TeamMember.objects.get_or_create(
                team=team,
                user=user,
                defaults={
                    'role': 'captain',
                    'status': 'active',
                    'joined_at': timezone.now()
                }
            )
        
        # Get mutual teams (user with themselves)
        mutual_teams = SocialService.get_mutual_teams(user.id, user.id)
        
        # Property: User should have mutual teams with themselves equal to all their teams
        assert len(mutual_teams) == len(teams), \
            f"Expected {len(teams)} mutual teams for user with themselves, got {len(mutual_teams)}"
        
        # Property: All user's teams should be in the mutual teams
        user_team_ids = {team.id for team in teams}
        mutual_team_ids = {uuid.UUID(team['team_id']) for team in mutual_teams}
        
        assert mutual_team_ids == user_team_ids, \
            f"Expected mutual teams {user_team_ids}, got {mutual_team_ids}"
        
        # Cleanup - delete teams first, then game
        for team in teams:
            team.delete()
        game.delete()
        user.delete()
    
    def test_mutual_teams_edge_case_inactive_memberships(self):
        """Edge case: Inactive team memberships should not count as mutual teams"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        user1 = User.objects.create_user(
            email=f'user1_{unique_id}@example.com',
            username=f'user1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'user2_{unique_id}@example.com',
            username=f'user2_{unique_id}',
            password='testpass123'
        )
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create team
        team = Team.objects.create(
            name=f'Team {unique_id}',
            tag='T1',
            game=game,
            captain=user1,
            description='Test team',
            status='active'
        )
        
        # Add user1 as active member
        TeamMember.objects.create(
            team=team,
            user=user1,
            role='captain',
            status='active',
            joined_at=timezone.now()
        )
        
        # Add user2 as inactive member (left the team)
        TeamMember.objects.create(
            team=team,
            user=user2,
            role='member',
            status='left',
            joined_at=timezone.now() - timezone.timedelta(days=30),
            left_at=timezone.now() - timezone.timedelta(days=10)
        )
        
        # Get mutual teams
        mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
        
        # Property: Inactive memberships should not create mutual teams
        assert len(mutual_teams) == 0, \
            f"Expected 0 mutual teams with inactive membership, got {len(mutual_teams)}"
        
        # Now make user2's membership active
        user2_membership = TeamMember.objects.get(team=team, user=user2)
        user2_membership.status = 'active'
        user2_membership.left_at = None
        user2_membership.save()
        
        # Get mutual teams again
        mutual_teams_active = SocialService.get_mutual_teams(user1.id, user2.id)
        
        # Property: Active memberships should create mutual teams
        assert len(mutual_teams_active) == 1, \
            f"Expected 1 mutual team with active memberships, got {len(mutual_teams_active)}"
        
        assert mutual_teams_active[0]['team_id'] == str(team.id), \
            f"Expected team {team.id} in mutual teams, got {mutual_teams_active[0]['team_id']}"
        
        # Cleanup - delete team first, then game
        team.delete()
        game.delete()
        user1.delete()
        user2.delete()
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_teams=st.integers(min_value=1, max_value=5)
    )
    def test_mutual_teams_data_completeness_property(self, num_teams):
        """Property: Mutual teams data should include all required fields"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        user1 = User.objects.create_user(
            email=f'user1_{unique_id}@example.com',
            username=f'user1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'user2_{unique_id}@example.com',
            username=f'user2_{unique_id}',
            password='testpass123'
        )
        
        # Create a test game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}',
            description='Test game for mutual teams',
            genre='other',
            is_active=True
        )
        
        # Create teams and add both users to all teams
        for i in range(num_teams):
            team = Team.objects.create(
                name=f'Team {i} {unique_id}',
                tag=f'T{i}',
                game=game,
                captain=user1,
                description=f'Test team {i}',
                status='active'
            )
            
            # Add user1 as captain
            TeamMember.objects.get_or_create(
                team=team,
                user=user1,
                defaults={
                    'role': 'captain',
                    'status': 'active',
                    'joined_at': timezone.now()
                }
            )
            
            # Add user2 as member
            TeamMember.objects.create(
                team=team,
                user=user2,
                role='member',
                status='active',
                joined_at=timezone.now()
            )
        
        # Get mutual teams
        mutual_teams = SocialService.get_mutual_teams(user1.id, user2.id)
        
        # Property: Should have all teams as mutual
        assert len(mutual_teams) == num_teams, \
            f"Expected {num_teams} mutual teams, got {len(mutual_teams)}"
        
        # Property: Each mutual team data should have all required fields
        required_fields = [
            'team_id', 'team_name', 'team_tag', 'game_name',
            'user1_role', 'user2_role', 'user1_joined_at', 'user2_joined_at'
        ]
        
        for team_data in mutual_teams:
            for field in required_fields:
                assert field in team_data, \
                    f"Missing required field '{field}' in team data: {team_data}"
                
                # Check that field is not None (except for optional datetime fields)
                if field not in ['user1_joined_at', 'user2_joined_at']:
                    assert team_data[field] is not None, \
                        f"Field '{field}' should not be None in team data: {team_data}"
            
            # Property: Roles should be valid
            assert team_data['user1_role'] in ['captain', 'co_captain', 'member', 'substitute'], \
                f"Invalid user1_role: {team_data['user1_role']}"
            
            assert team_data['user2_role'] in ['captain', 'co_captain', 'member', 'substitute'], \
                f"Invalid user2_role: {team_data['user2_role']}"
            
            # Property: Team ID should be valid UUID string
            try:
                uuid.UUID(team_data['team_id'])
            except ValueError:
                pytest.fail(f"Invalid team_id format: {team_data['team_id']}")
        
        # Cleanup - delete teams first, then game
        for i in range(num_teams):
            # Teams were created in the loop, need to get them again for deletion
            try:
                team = Team.objects.get(name=f'Team {i} {unique_id}')
                team.delete()
            except Team.DoesNotExist:
                pass
        game.delete()
        user1.delete()
        user2.delete()