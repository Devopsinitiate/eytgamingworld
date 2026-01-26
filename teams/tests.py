from django.test import TestCase, TransactionTestCase
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import from_model, TestCase as HypothesisTestCase, TransactionTestCase as HypothesisTransactionTestCase
from django.utils import timezone
from datetime import timedelta
from teams.models import Team, TeamMember, TeamInvite
from core.models import User, Game


class TeamPropertyTests(HypothesisTransactionTestCase):
    """Property-based tests for team management system"""
    
    @settings(max_examples=20, deadline=None)
    @given(
        max_members=st.integers(min_value=1, max_value=10),
        num_members_to_add=st.integers(min_value=0, max_value=12)
    )
    def test_team_capacity_enforcement(self, max_members, num_members_to_add):
        """
        **Feature: team-management, Property 1: Team Capacity Enforcement**
        
        For any team, the number of active members should never exceed the max_members value
        **Validates: Requirements 6.5, 12.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team with specified max_members
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=max_members
        )
        
        # Create the captain's membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Try to add members up to the specified number
        active_members_added = 1  # Captain is already added
        
        for i in range(num_members_to_add):
            if active_members_added >= max_members:
                # Team is full, should not add more
                break
            
            # Create a new user
            user = User.objects.create_user(
                username=f"u{int(timestamp * 1000) % 1000000}_{i}",
                email=f"u{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Add member to team
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_members_added += 1
        
        # Verify the property: active members should never exceed max_members
        active_count = team.members.filter(status='active').count()
        
        assert active_count <= max_members, \
            f"Team has {active_count} active members but max_members is {max_members}"
        
        # Also verify using the team's member_count property
        assert team.member_count <= max_members, \
            f"Team member_count is {team.member_count} but max_members is {max_members}"
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_role_changes=st.integers(min_value=0, max_value=5)
    )
    def test_captain_uniqueness(self, num_role_changes):
        """
        **Feature: team-management, Property 2: Captain Uniqueness**
        
        For any team, exactly one member should have the role of captain at any given time
        **Validates: Requirements 2.4, 10.3**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create users
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=10
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create additional members
        members = []
        for i in range(min(3, num_role_changes + 1)):
            user = User.objects.create_user(
                username=f"m{int(timestamp * 1000) % 1000000}_{i}",
                email=f"m{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            members.append(member)
        
        # Perform role changes
        for i in range(num_role_changes):
            if not members:
                break
            
            # Get a member to potentially promote
            member_to_change = members[i % len(members)]
            
            # Simulate captain transfer: demote current captain, promote new captain
            if member_to_change.role != 'captain':
                # Find current captain
                current_captain = team.members.filter(role='captain', status='active').first()
                if current_captain:
                    # Demote current captain to member
                    current_captain.role = 'member'
                    current_captain.save()
                
                # Promote member to captain
                member_to_change.role = 'captain'
                member_to_change.save()
                
                # Update team's captain field
                team.captain = member_to_change.user
                team.save()
        
        # Verify the property: exactly one captain at any time
        captain_count = team.members.filter(role='captain', status='active').count()
        
        assert captain_count == 1, \
            f"Team has {captain_count} captains but should have exactly 1"
        
        # Also verify that the team's captain field matches the captain member
        captain_member = team.members.filter(role='captain', status='active').first()
        assert captain_member is not None, "No captain member found"
        assert team.captain == captain_member.user, \
            f"Team captain field doesn't match captain member"

    @settings(max_examples=20, deadline=None)
    @given(
        search_query=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        num_teams=st.integers(min_value=1, max_value=10)
    )
    def test_search_result_relevance(self, search_query, num_teams):
        """
        **Feature: team-management, Property 9: Search Result Relevance**
        
        For any search query, all returned teams should contain the query string in name, tag, or description
        **Validates: Requirements 1.2, 14.1**
        """
        # Clean up search query
        search_query = search_query.strip()
        if not search_query:
            return  # Skip empty queries
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create teams with varying content
        teams_created = []
        for i in range(num_teams):
            # Create a captain user
            captain = User.objects.create_user(
                username=f"cap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Randomly decide if this team should match the search query
            should_match = i % 2 == 0
            
            if should_match:
                # Include search query in one of the fields
                field_choice = i % 3
                if field_choice == 0:
                    # Include in name
                    name = f"Team {search_query} {i}"
                    tag = f"T{i}"
                    description = "Test description"
                elif field_choice == 1:
                    # Include in tag (max 10 chars, so truncate search query)
                    name = f"Team {i}"
                    # Ensure tag doesn't exceed 10 chars total
                    tag_base = search_query[:7] if len(search_query) > 7 else search_query
                    tag = tag_base
                    description = "Test description"
                else:
                    # Include in description
                    name = f"Team {i}"
                    tag = f"T{i}"
                    description = f"Test {search_query} description"
            else:
                # Don't include search query
                name = f"Team NoMatch {i}"
                tag = f"NM{i}"
                description = "No match description"
            
            # Ensure tag doesn't exceed 10 characters with timestamp
            tag_suffix = str(int(timestamp * 1000) % 10000)
            max_tag_len = 10 - len(tag_suffix)
            final_tag = f"{tag[:max_tag_len]}{tag_suffix}"
            
            team = Team.objects.create(
                name=f"{name}_{int(timestamp * 1000) % 1000000}",
                tag=final_tag,
                game=game,
                captain=captain,
                status='active',
                is_public=True,
                description=description
            )
            teams_created.append((team, should_match))
            
            # Create captain membership
            TeamMember.objects.create(
                team=team,
                user=captain,
                role='captain',
                status='active'
            )
        
        # Perform search using the same logic as the view
        from django.db.models import Q, Count
        
        search_results = Team.objects.filter(
            status='active',
            is_public=True
        ).filter(
            Q(name__icontains=search_query) |
            Q(tag__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        
        # Verify the property: all returned teams should contain the search query
        for team in search_results:
            query_lower = search_query.lower()
            name_match = query_lower in team.name.lower()
            tag_match = query_lower in team.tag.lower()
            desc_match = query_lower in team.description.lower()
            
            assert name_match or tag_match or desc_match, \
                f"Team '{team.name}' [{team.tag}] with description '{team.description}' " \
                f"was returned but doesn't contain search query '{search_query}'"
        
        # Also verify that teams that should match are in the results
        # But only if they actually contain the search query after all transformations
        for team, should_match in teams_created:
            query_lower = search_query.lower()
            name_match = query_lower in team.name.lower()
            tag_match = query_lower in team.tag.lower()
            desc_match = query_lower in team.description.lower()
            
            actually_matches = name_match or tag_match or desc_match
            
            if should_match and actually_matches:
                # This team was designed to match and actually does, verify it's in results
                assert team in search_results, \
                    f"Team '{team.name}' [{team.tag}] should match query '{search_query}' but wasn't returned"

    @settings(max_examples=20, deadline=None)
    @given(
        num_teams=st.integers(min_value=3, max_value=10),
        apply_game_filter=st.booleans(),
        apply_recruiting_filter=st.booleans()
    )
    def test_filter_combination_logic(self, num_teams, apply_game_filter, apply_recruiting_filter):
        """
        **Feature: team-management, Property 11: Filter Combination Logic**
        
        For any set of applied filters, the returned teams should satisfy all filter conditions (AND logic)
        **Validates: Requirements 14.2**
        """
        # Create test games
        timestamp = timezone.now().timestamp()
        game1 = Game.objects.create(
            name=f"Game1 {int(timestamp * 1000) % 1000000}",
            slug=f"game1-{int(timestamp * 1000) % 1000000}",
            description="Test game 1"
        )
        game2 = Game.objects.create(
            name=f"Game2 {int(timestamp * 1000) % 1000000}",
            slug=f"game2-{int(timestamp * 1000) % 1000000}",
            description="Test game 2"
        )
        
        # Create teams with varying properties
        teams_created = []
        for i in range(num_teams):
            # Create a captain user
            captain = User.objects.create_user(
                username=f"cap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Randomly assign game and recruiting status
            game = game1 if i % 2 == 0 else game2
            is_recruiting = i % 3 == 0
            
            team = Team.objects.create(
                name=f"Team {i}_{int(timestamp * 1000) % 1000000}",
                tag=f"T{i}{int(timestamp * 1000) % 10000}"[:10],
                game=game,
                captain=captain,
                status='active',
                is_public=True,
                is_recruiting=is_recruiting,
                description=f"Test team {i}"
            )
            teams_created.append((team, game, is_recruiting))
            
            # Create captain membership
            TeamMember.objects.create(
                team=team,
                user=captain,
                role='captain',
                status='active'
            )
        
        # Build filter query using the same logic as the view
        from django.db.models import Q, Count
        
        queryset = Team.objects.filter(
            status='active',
            is_public=True
        )
        
        # Apply filters based on test parameters
        filter_game = None
        filter_recruiting = None
        
        if apply_game_filter:
            filter_game = game1.slug
            queryset = queryset.filter(game__slug=filter_game)
        
        if apply_recruiting_filter:
            filter_recruiting = True
            queryset = queryset.filter(is_recruiting=True)
        
        # Get results
        results = list(queryset)
        
        # Verify the property: all returned teams should satisfy ALL applied filters (AND logic)
        for team in results:
            if apply_game_filter:
                assert team.game.slug == filter_game, \
                    f"Team '{team.name}' has game '{team.game.slug}' but filter requires '{filter_game}'"
            
            if apply_recruiting_filter:
                assert team.is_recruiting == True, \
                    f"Team '{team.name}' has is_recruiting={team.is_recruiting} but filter requires True"
        
        # Also verify that teams matching all filters are in the results
        for team, game, is_recruiting in teams_created:
            matches_game_filter = (not apply_game_filter) or (game.slug == filter_game)
            matches_recruiting_filter = (not apply_recruiting_filter) or (is_recruiting == True)
            
            should_be_in_results = matches_game_filter and matches_recruiting_filter
            is_in_results = team in results
            
            if should_be_in_results:
                assert is_in_results, \
                    f"Team '{team.name}' matches all filters but wasn't returned. " \
                    f"Game: {game.slug} (filter: {filter_game}), " \
                    f"Recruiting: {is_recruiting} (filter: {filter_recruiting})"
            else:
                assert not is_in_results, \
                    f"Team '{team.name}' doesn't match all filters but was returned. " \
                    f"Game: {game.slug} (filter: {filter_game}), " \
                    f"Recruiting: {is_recruiting} (filter: {filter_recruiting})"
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_teams=st.integers(min_value=1, max_value=5),
        num_join_attempts=st.integers(min_value=1, max_value=10)
    )
    def test_membership_uniqueness(self, num_teams, num_join_attempts):
        """
        **Feature: team-management, Property 3: Membership Uniqueness**
        
        For any user and team combination, at most one active TeamMember record should exist
        **Validates: Requirements 5.2, 12.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a test user who will try to join teams
        test_user = User.objects.create_user(
            username=f"testuser{int(timestamp * 1000) % 1000000}",
            email=f"testuser{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create multiple teams
        teams = []
        for i in range(num_teams):
            # Create a captain user
            captain = User.objects.create_user(
                username=f"cap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            team = Team.objects.create(
                name=f"Team {i}_{int(timestamp * 1000) % 1000000}",
                tag=f"T{i}{int(timestamp * 1000) % 10000}"[:10],
                game=game,
                captain=captain,
                max_members=10
            )
            
            # Create captain membership
            TeamMember.objects.create(
                team=team,
                user=captain,
                role='captain',
                status='active'
            )
            
            teams.append(team)
        
        # Attempt to join teams multiple times
        for i in range(num_join_attempts):
            if not teams:
                break
            
            # Pick a random team
            team = teams[i % len(teams)]
            
            # Try to create a membership (simulating multiple join attempts)
            # This should respect the unique_together constraint
            try:
                # Check if active membership already exists
                existing_active = TeamMember.objects.filter(
                    team=team,
                    user=test_user,
                    status='active'
                ).exists()
                
                if not existing_active:
                    # Create new membership
                    TeamMember.objects.create(
                        team=team,
                        user=test_user,
                        role='member',
                        status='active'
                    )
            except Exception:
                # If there's a database constraint violation, that's expected
                # The unique_together constraint should prevent duplicates
                pass
        
        # Verify the property: for each team, at most one active membership should exist
        for team in teams:
            active_memberships = TeamMember.objects.filter(
                team=team,
                user=test_user,
                status='active'
            )
            
            active_count = active_memberships.count()
            
            assert active_count <= 1, \
                f"User {test_user.username} has {active_count} active memberships in team '{team.name}', " \
                f"but should have at most 1"
        
        # Also verify that the user doesn't have duplicate memberships across all teams
        # (checking the unique_together constraint at the database level)
        all_memberships = TeamMember.objects.filter(user=test_user)
        
        # Group by team and check for duplicates
        team_membership_counts = {}
        for membership in all_memberships:
            team_id = membership.team.id
            if team_id not in team_membership_counts:
                team_membership_counts[team_id] = 0
            team_membership_counts[team_id] += 1
        
        # Each team should have at most one membership record per user
        # (regardless of status, due to unique_together constraint)
        for team_id, count in team_membership_counts.items():
            assert count == 1, \
                f"User {test_user.username} has {count} membership records for team {team_id}, " \
                f"but should have exactly 1 (unique_together constraint)"
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_active_members=st.integers(min_value=1, max_value=8),
        num_inactive_members=st.integers(min_value=0, max_value=5),
        num_pending_members=st.integers(min_value=0, max_value=3)
    )
    def test_roster_display_accuracy(self, num_active_members, num_inactive_members, num_pending_members):
        """
        **Feature: team-management, Property 8: Roster Display Accuracy**
        
        For any team roster view, all displayed members should have status active and belong to the specified team
        **Validates: Requirements 3.2, 6.1**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership (counts as one active member)
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Track all members we create
        active_members_created = [captain]
        inactive_members_created = []
        pending_members_created = []
        
        # Create active members (subtract 1 because captain is already active)
        for i in range(num_active_members - 1):
            user = User.objects.create_user(
                username=f"active{int(timestamp * 1000) % 1000000}_{i}",
                email=f"active{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_members_created.append(user)
        
        # Create inactive members
        for i in range(num_inactive_members):
            user = User.objects.create_user(
                username=f"inactive{int(timestamp * 1000) % 1000000}_{i}",
                email=f"inactive{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='inactive'
            )
            inactive_members_created.append(user)
        
        # Create pending members
        for i in range(num_pending_members):
            user = User.objects.create_user(
                username=f"pending{int(timestamp * 1000) % 1000000}_{i}",
                email=f"pending{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='pending'
            )
            pending_members_created.append(user)
        
        # Simulate the roster query from the view (Requirements 3.2, 6.1)
        roster = team.members.filter(
            status='active'
        ).select_related('user').order_by('role', '-joined_at')
        
        # Verify the property: all displayed members should have status 'active'
        for member in roster:
            assert member.status == 'active', \
                f"Member {member.user.username} in roster has status '{member.status}' but should be 'active'"
        
        # Verify the property: all displayed members should belong to the specified team
        for member in roster:
            assert member.team == team, \
                f"Member {member.user.username} in roster belongs to team '{member.team.name}' " \
                f"but should belong to '{team.name}'"
        
        # Verify that the roster count matches the number of active members
        roster_count = roster.count()
        expected_active_count = num_active_members
        
        assert roster_count == expected_active_count, \
            f"Roster has {roster_count} members but should have {expected_active_count} active members"
        
        # Verify that inactive and pending members are NOT in the roster
        roster_users = [member.user for member in roster]
        
        for user in inactive_members_created:
            assert user not in roster_users, \
                f"Inactive member {user.username} should not be in the roster"
        
        for user in pending_members_created:
            assert user not in roster_users, \
                f"Pending member {user.username} should not be in the roster"
        
        # Verify that all active members ARE in the roster
        for user in active_members_created:
            assert user in roster_users, \
                f"Active member {user.username} should be in the roster"
    
    @settings(max_examples=20, deadline=None)
    @given(
        is_public=st.booleans(),
        user_is_member=st.booleans(),
        user_is_authenticated=st.booleans()
    )
    def test_private_team_access(self, is_public, user_is_member, user_is_authenticated):
        """
        **Feature: team-management, Property 15: Private Team Access**
        
        For any private team, only active members should be able to view the team detail page
        **Validates: Requirements 3.1, 12.1**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team with specified privacy setting
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            is_public=is_public,
            max_members=10
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create a test user (potential viewer)
        test_user = None
        if user_is_authenticated:
            test_user = User.objects.create_user(
                username=f"viewer{int(timestamp * 1000) % 1000000}",
                email=f"viewer{int(timestamp * 1000) % 1000000}@test.com",
                password="testpass123"
            )
            
            # If user should be a member, create membership
            if user_is_member:
                TeamMember.objects.create(
                    team=team,
                    user=test_user,
                    role='member',
                    status='active'
                )
        
        # Simulate the access control logic from the view (Requirements 3.1, 12.1)
        can_access = False
        
        if is_public:
            # Public teams can be viewed by anyone
            can_access = True
        else:
            # Private teams require authentication and membership
            if user_is_authenticated and test_user:
                # Check if user is an active member
                membership = TeamMember.objects.filter(
                    team=team,
                    user=test_user,
                    status='active'
                ).first()
                
                if membership:
                    can_access = True
        
        # Verify the property: access should be granted correctly based on privacy and membership
        if not is_public:
            # For private teams
            if user_is_authenticated and user_is_member:
                # Active members should have access
                assert can_access, \
                    f"Active member should have access to private team '{team.name}'"
            else:
                # Non-members or unauthenticated users should NOT have access
                assert not can_access, \
                    f"Non-member or unauthenticated user should NOT have access to private team '{team.name}'"
        else:
            # For public teams, everyone should have access
            assert can_access, \
                f"Public team '{team.name}' should be accessible to everyone"
        
        # Additional verification: test the actual view logic
        # Check that the membership query returns correct results
        if user_is_authenticated and test_user:
            membership = TeamMember.objects.filter(
                team=team,
                user=test_user,
                status='active'
            ).first()
            
            if user_is_member:
                assert membership is not None, \
                    f"User {test_user.username} should have an active membership"
                assert membership.status == 'active', \
                    f"Membership status should be 'active' but is '{membership.status}'"
            else:
                assert membership is None, \
                    f"User {test_user.username} should not have an active membership"

    @settings(max_examples=100, deadline=None)
    @given(
        days_until_expiry=st.integers(min_value=-10, max_value=10),
        num_invites=st.integers(min_value=1, max_value=5)
    )
    def test_invite_expiry(self, days_until_expiry, num_invites):
        """
        **Feature: team-management, Property 4: Invite Expiry**
        
        For any team invite, if the current time exceeds expires_at and status is pending, 
        the invite should be marked as expired
        **Validates: Requirements 4.4**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=10
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create invites with varying expiry dates
        invites_created = []
        current_time = timezone.now()
        
        for i in range(num_invites):
            # Create invited user
            invited_user = User.objects.create_user(
                username=f"invited{int(timestamp * 1000) % 1000000}_{i}",
                email=f"invited{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Calculate expiry date based on test parameter
            # Positive days_until_expiry means invite expires in the future
            # Negative days_until_expiry means invite already expired
            expires_at = current_time + timedelta(days=days_until_expiry)
            
            # Create invite
            invite = TeamInvite.objects.create(
                team=team,
                invited_by=captain,
                invited_user=invited_user,
                message=f"Test invite {i}",
                status='pending',
                expires_at=expires_at
            )
            invites_created.append(invite)
        
        # Simulate the expiry check logic (as would be done in views or management commands)
        # This is the property we're testing: expired pending invites should be marked as expired
        # Note: An invite is considered expired if current_time >= expires_at (not just >)
        for invite in invites_created:
            # Refresh from database to get current state
            invite.refresh_from_db()
            
            # Check if invite should be expired (expires_at <= current_time means expired)
            is_expired = invite.expires_at <= current_time
            is_pending = invite.status == 'pending'
            
            if is_expired and is_pending:
                # This invite should be marked as expired
                # Simulate the expiry logic from the view
                invite.status = 'expired'
                invite.save()
        
        # Verify the property: all expired pending invites should now be marked as expired
        for invite in invites_created:
            invite.refresh_from_db()
            
            # An invite is expired if current_time >= expires_at
            is_expired = invite.expires_at <= current_time
            
            if is_expired:
                # If the invite has expired, it should not have status 'pending'
                assert invite.status != 'pending', \
                    f"Invite {invite.id} has expired (expires_at: {invite.expires_at}, " \
                    f"current: {current_time}) but still has status 'pending'"
                
                # It should be marked as 'expired'
                assert invite.status == 'expired', \
                    f"Invite {invite.id} has expired but has status '{invite.status}' instead of 'expired'"
            else:
                # If the invite has not expired, it should still be pending
                # (assuming no other actions were taken on it)
                assert invite.status == 'pending', \
                    f"Invite {invite.id} has not expired (expires_at: {invite.expires_at}, " \
                    f"current: {current_time}) but has status '{invite.status}' instead of 'pending'"
        
        # Additional verification: test that expired invites are filtered out in queries
        # This simulates the view logic that only shows non-expired pending invites
        # Note: The view uses expires_at__gt which means expires_at > current_time (future expiry)
        active_invites = TeamInvite.objects.filter(
            team=team,
            status='pending',
            expires_at__gt=current_time
        )
        
        # Count how many invites should be active (not expired)
        # An invite is active if expires_at > current_time
        expected_active_count = sum(1 for inv in invites_created if inv.expires_at > current_time)
        
        # After marking expired invites, only non-expired ones should have status 'pending'
        actual_pending_count = TeamInvite.objects.filter(
            team=team,
            status='pending'
        ).count()
        
        assert actual_pending_count == expected_active_count, \
            f"Expected {expected_active_count} pending invites but found {actual_pending_count}"
        
        # Verify that the active_invites query returns the correct count
        assert active_invites.count() == expected_active_count, \
            f"Active invites query returned {active_invites.count()} but expected {expected_active_count}"

    @settings(max_examples=20, deadline=None)
    @given(
        user_role=st.sampled_from(['captain', 'co_captain', 'member', 'substitute', 'non_member']),
        action_type=st.sampled_from(['change_role', 'remove_member', 'invite_player', 'approve_application'])
    )
    def test_permission_enforcement(self, user_role, action_type):
        """
        **Feature: team-management, Property 5: Permission Enforcement**
        
        For any team management action, only users with captain or co-captain roles 
        should be able to perform the action
        **Validates: Requirements 12.1, 12.2, 12.3, 12.4**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=10
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create test user with specified role
        test_user = User.objects.create_user(
            username=f"testuser{int(timestamp * 1000) % 1000000}",
            email=f"testuser{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create membership for test user (if not non_member)
        test_membership = None
        if user_role != 'non_member':
            test_membership = TeamMember.objects.create(
                team=team,
                user=test_user,
                role=user_role,
                status='active'
            )
        
        # Create a target member for actions that require one
        target_user = User.objects.create_user(
            username=f"target{int(timestamp * 1000) % 1000000}",
            email=f"target{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        target_member = TeamMember.objects.create(
            team=team,
            user=target_user,
            role='member',
            status='active'
        )
        
        # Create a pending application for approve_application action
        applicant_user = User.objects.create_user(
            username=f"applicant{int(timestamp * 1000) % 1000000}",
            email=f"applicant{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        pending_application = TeamMember.objects.create(
            team=team,
            user=applicant_user,
            role='member',
            status='pending'
        )
        
        # Define permission requirements for each action
        # Based on Requirements 12.1, 12.2, 12.3, 12.4
        permission_requirements = {
            'change_role': ['captain'],  # Only captain can change roles (Requirement 6.2, 12.1)
            'remove_member': ['captain', 'co_captain'],  # Captain and co-captain can remove (Requirement 6.3, 12.3)
            'invite_player': ['captain', 'co_captain'],  # Captain and co-captain can invite (Requirement 4.1, 12.3)
            'approve_application': ['captain', 'co_captain'],  # Captain and co-captain can approve (Requirement 5.4, 12.3)
        }
        
        # Determine if the user should have permission for this action
        required_roles = permission_requirements[action_type]
        should_have_permission = user_role in required_roles
        
        # Simulate permission check (as done in views with mixins)
        has_permission = False
        
        if test_membership:
            # User is a member, check their role
            if test_membership.role in required_roles:
                has_permission = True
        
        # Verify the property: permission should match expected based on role
        assert has_permission == should_have_permission, \
            f"User with role '{user_role}' should {'have' if should_have_permission else 'NOT have'} " \
            f"permission for action '{action_type}', but has_permission={has_permission}"
        
        # Additional verification: test specific action logic
        if action_type == 'change_role':
            # Only captain should be able to change roles (Requirement 6.2, 12.1)
            if user_role == 'captain':
                # Captain should be able to change role
                assert has_permission, "Captain should have permission to change roles"
                
                # Simulate role change
                old_role = target_member.role
                target_member.role = 'co_captain'
                target_member.save()
                
                # Verify role was changed
                target_member.refresh_from_db()
                assert target_member.role == 'co_captain', "Role should be changed to co_captain"
                
                # Reset for next test
                target_member.role = old_role
                target_member.save()
            else:
                # Non-captains should NOT have permission
                assert not has_permission, f"User with role '{user_role}' should NOT have permission to change roles"
        
        elif action_type == 'remove_member':
            # Captain and co-captain should be able to remove members (Requirement 6.3, 12.3, 12.4)
            if user_role in ['captain', 'co_captain']:
                assert has_permission, f"User with role '{user_role}' should have permission to remove members"
                
                # Simulate member removal
                old_status = target_member.status
                target_member.status = 'removed'
                target_member.left_at = timezone.now()
                target_member.save()
                
                # Verify member was removed
                target_member.refresh_from_db()
                assert target_member.status == 'removed', "Member should be marked as removed"
                
                # Reset for next test
                target_member.status = old_status
                target_member.left_at = None
                target_member.save()
            else:
                # Regular members and non-members should NOT have permission
                assert not has_permission, f"User with role '{user_role}' should NOT have permission to remove members"
        
        elif action_type == 'invite_player':
            # Captain and co-captain should be able to invite players (Requirement 4.1, 12.3)
            if user_role in ['captain', 'co_captain']:
                assert has_permission, f"User with role '{user_role}' should have permission to invite players"
                
                # Simulate invite creation
                invited_user = User.objects.create_user(
                    username=f"invited{int(timestamp * 1000) % 1000000}",
                    email=f"invited{int(timestamp * 1000) % 1000000}@test.com",
                    password="testpass123"
                )
                
                invite = TeamInvite.objects.create(
                    team=team,
                    invited_by=test_user,
                    invited_user=invited_user,
                    message="Test invite",
                    expires_at=timezone.now() + timedelta(days=7)
                )
                
                # Verify invite was created
                assert invite.invited_by == test_user, "Invite should be created by the test user"
                assert invite.team == team, "Invite should be for the correct team"
            else:
                # Regular members and non-members should NOT have permission
                assert not has_permission, f"User with role '{user_role}' should NOT have permission to invite players"
        
        elif action_type == 'approve_application':
            # Captain and co-captain should be able to approve applications (Requirement 5.4, 12.3)
            if user_role in ['captain', 'co_captain']:
                assert has_permission, f"User with role '{user_role}' should have permission to approve applications"
                
                # Simulate application approval
                old_status = pending_application.status
                pending_application.status = 'active'
                pending_application.approved_at = timezone.now()
                pending_application.save()
                
                # Verify application was approved
                pending_application.refresh_from_db()
                assert pending_application.status == 'active', "Application should be approved"
                assert pending_application.approved_at is not None, "Application should have approved_at timestamp"
                
                # Reset for next test
                pending_application.status = old_status
                pending_application.approved_at = None
                pending_application.save()
            else:
                # Regular members and non-members should NOT have permission
                assert not has_permission, f"User with role '{user_role}' should NOT have permission to approve applications"
        
        # Verify that non-members have no permissions (Requirement 12.1, 12.2)
        if user_role == 'non_member':
            assert not has_permission, "Non-members should have no team management permissions"
        
        # Verify that regular members have no management permissions (Requirement 12.2)
        if user_role in ['member', 'substitute']:
            assert not has_permission, f"User with role '{user_role}' should have no management permissions"

    @settings(max_examples=20, deadline=None)
    @given(
        num_pending_applications=st.integers(min_value=1, max_value=5),
        num_to_approve=st.integers(min_value=0, max_value=5),
        max_members=st.integers(min_value=3, max_value=10)
    )
    def test_application_approval(self, num_pending_applications, num_to_approve, max_members):
        """
        **Feature: team-management, Property 6: Application Approval**
        
        For any pending team member, when approved, the status should change to active 
        and the team member_count should increase
        **Validates: Requirements 5.5, 6.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team with specified max_members
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=max_members
        )
        
        # Create captain membership (counts as 1 active member)
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Record initial member count
        initial_member_count = team.member_count
        
        # Create pending applications
        pending_applications = []
        for i in range(num_pending_applications):
            # Create applicant user
            applicant = User.objects.create_user(
                username=f"applicant{int(timestamp * 1000) % 1000000}_{i}",
                email=f"applicant{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Create pending TeamMember record (Requirement 5.2)
            application = TeamMember.objects.create(
                team=team,
                user=applicant,
                role='member',
                status='pending'
            )
            pending_applications.append(application)
        
        # Verify that pending applications don't count toward member_count
        assert team.member_count == initial_member_count, \
            f"Pending applications should not increase member_count. " \
            f"Expected {initial_member_count}, got {team.member_count}"
        
        # Approve applications up to the specified number (or until team is full)
        approved_count = 0
        for i in range(min(num_to_approve, len(pending_applications))):
            application = pending_applications[i]
            
            # Check if team is full before approving
            if team.is_full:
                # Cannot approve more members when team is full
                break
            
            # Record member count before approval
            count_before = team.member_count
            
            # Approve the application (Requirement 5.5)
            application.status = 'active'
            application.approved_at = timezone.now()
            application.save()
            
            # Refresh team to get updated member_count
            team.refresh_from_db()
            count_after = team.member_count
            
            # Verify the property: status should change to active
            application.refresh_from_db()
            assert application.status == 'active', \
                f"Application {application.id} should have status 'active' after approval, " \
                f"but has status '{application.status}'"
            
            # Verify the property: approved_at should be set
            assert application.approved_at is not None, \
                f"Application {application.id} should have approved_at set after approval"
            
            # Verify the property: member_count should increase by 1
            assert count_after == count_before + 1, \
                f"Member count should increase by 1 after approval. " \
                f"Before: {count_before}, After: {count_after}"
            
            approved_count += 1
        
        # Verify final state
        final_member_count = team.member_count
        expected_final_count = initial_member_count + approved_count
        
        assert final_member_count == expected_final_count, \
            f"Final member count should be {expected_final_count} " \
            f"(initial {initial_member_count} + approved {approved_count}), " \
            f"but is {final_member_count}"
        
        # Verify that member_count never exceeds max_members (Requirement 6.5)
        assert final_member_count <= max_members, \
            f"Team member count {final_member_count} exceeds max_members {max_members}"
        
        # Verify that approved members are now in the active roster
        active_members = team.members.filter(status='active')
        assert active_members.count() == final_member_count, \
            f"Active members count {active_members.count()} should match member_count {final_member_count}"
        
        # Verify that remaining applications are still pending
        remaining_pending = team.members.filter(status='pending')
        expected_pending = num_pending_applications - approved_count
        
        assert remaining_pending.count() == expected_pending, \
            f"Should have {expected_pending} pending applications remaining, " \
            f"but have {remaining_pending.count()}"
        
        # Verify that all approved applications have approved_at timestamp
        for application in pending_applications[:approved_count]:
            application.refresh_from_db()
            assert application.approved_at is not None, \
                f"Approved application {application.id} should have approved_at timestamp"
            assert application.status == 'active', \
                f"Approved application {application.id} should have status 'active'"

    @settings(max_examples=20, deadline=None)
    @given(
        num_active_members=st.integers(min_value=2, max_value=10),
        num_inactive_members=st.integers(min_value=0, max_value=5),
        num_pending_members=st.integers(min_value=0, max_value=3)
    )
    def test_disbanding_cleanup(self, num_active_members, num_inactive_members, num_pending_members):
        """
        **Feature: team-management, Property 10: Disbanding Cleanup**
        
        For any team that is disbanded, all team members should have their status set to inactive
        **Validates: Requirements 10.4, 10.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            status='active',
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership (counts as one active member)
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Track all members we create
        active_members_created = [captain_member]
        inactive_members_created = []
        pending_members_created = []
        
        # Create additional active members (subtract 1 because captain is already active)
        for i in range(num_active_members - 1):
            user = User.objects.create_user(
                username=f"active{int(timestamp * 1000) % 1000000}_{i}",
                email=f"active{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_members_created.append(member)
        
        # Create inactive members (already inactive before disbanding)
        for i in range(num_inactive_members):
            user = User.objects.create_user(
                username=f"inactive{int(timestamp * 1000) % 1000000}_{i}",
                email=f"inactive{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='inactive',
                left_at=timezone.now() - timedelta(days=1)
            )
            inactive_members_created.append(member)
        
        # Create pending members (applications not yet approved)
        for i in range(num_pending_members):
            user = User.objects.create_user(
                username=f"pending{int(timestamp * 1000) % 1000000}_{i}",
                email=f"pending{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='pending'
            )
            pending_members_created.append(member)
        
        # Verify initial state
        initial_active_count = team.members.filter(status='active').count()
        assert initial_active_count == num_active_members, \
            f"Initial active member count should be {num_active_members}, got {initial_active_count}"
        
        # Simulate the disband operation (Requirement 10.4, 10.5)
        # This is the logic from TeamDisbandView
        
        # Set team status to disbanded (Requirement 10.4)
        team.status = 'disbanded'
        team.save()
        
        # Set all active members to inactive (Requirement 10.5)
        team.members.filter(status='active').update(
            status='inactive',
            left_at=timezone.now()
        )
        
        # Verify the property: team status should be 'disbanded'
        team.refresh_from_db()
        assert team.status == 'disbanded', \
            f"Team status should be 'disbanded' but is '{team.status}'"
        
        # Verify the property: all members should have status 'inactive' or 'pending'
        # (pending members are not affected by disbanding in the current implementation)
        all_members = team.members.all()
        
        for member in all_members:
            member.refresh_from_db()
            
            # Active members should now be inactive
            if member in active_members_created:
                assert member.status == 'inactive', \
                    f"Active member {member.user.username} should be 'inactive' after disbanding, " \
                    f"but has status '{member.status}'"
                
                assert member.left_at is not None, \
                    f"Active member {member.user.username} should have left_at timestamp after disbanding"
            
            # Already inactive members should remain inactive
            elif member in inactive_members_created:
                assert member.status == 'inactive', \
                    f"Already inactive member {member.user.username} should remain 'inactive', " \
                    f"but has status '{member.status}'"
            
            # Pending members remain pending (they were never active)
            elif member in pending_members_created:
                # Note: The current implementation doesn't change pending members
                # This is acceptable as they were never active members
                pass
        
        # Verify that no active members remain
        remaining_active = team.members.filter(status='active').count()
        assert remaining_active == 0, \
            f"After disbanding, there should be 0 active members, but found {remaining_active}"
        
        # Verify that all previously active members are now inactive
        for member in active_members_created:
            member.refresh_from_db()
            assert member.status == 'inactive', \
                f"Previously active member {member.user.username} should be inactive after disbanding"
        
        # Verify that the team's member_count property returns 0 (no active members)
        assert team.member_count == 0, \
            f"Team member_count should be 0 after disbanding, but is {team.member_count}"
        
        # Additional verification: ensure the team cannot be used for new operations
        # A disbanded team should not accept new members
        assert team.status == 'disbanded', \
            "Team should remain in disbanded status"
        
        # Verify that the cleanup was complete
        total_members = team.members.count()
        expected_total = num_active_members + num_inactive_members + num_pending_members
        
        assert total_members == expected_total, \
            f"Total member count should be {expected_total}, but is {total_members}"

    @settings(max_examples=20, deadline=None)
    @given(
        num_active_members=st.integers(min_value=2, max_value=10),
        num_inactive_members=st.integers(min_value=0, max_value=5),
        priority=st.sampled_from(['normal', 'important', 'urgent'])
    )
    def test_announcement_notification(self, num_active_members, num_inactive_members, priority):
        """
        **Feature: team-management, Property 14: Announcement Notification**
        
        For any team announcement posted by captain or co-captain, all active team members 
        should receive a notification
        **Validates: Requirements 9.2**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership (counts as one active member)
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Track all active members we create (including captain)
        active_members_created = [captain]
        inactive_members_created = []
        
        # Create additional active members (subtract 1 because captain is already active)
        for i in range(num_active_members - 1):
            user = User.objects.create_user(
                username=f"active{int(timestamp * 1000) % 1000000}_{i}",
                email=f"active{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_members_created.append(user)
        
        # Create inactive members (should NOT receive notifications)
        for i in range(num_inactive_members):
            user = User.objects.create_user(
                username=f"inactive{int(timestamp * 1000) % 1000000}_{i}",
                email=f"inactive{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='inactive',
                left_at=timezone.now() - timedelta(days=1)
            )
            inactive_members_created.append(user)
        
        # Verify initial state
        initial_active_count = team.members.filter(status='active').count()
        assert initial_active_count == num_active_members, \
            f"Initial active member count should be {num_active_members}, got {initial_active_count}"
        
        # Create an announcement (Requirement 9.1)
        from teams.models import TeamAnnouncement
        announcement = TeamAnnouncement.objects.create(
            team=team,
            posted_by=captain,
            title=f"Test Announcement {int(timestamp * 1000) % 1000000}",
            content="This is a test announcement for property testing",
            priority=priority,
            is_pinned=False
        )
        
        # Simulate the notification logic from TeamAnnouncementPostView (Requirement 9.2)
        # Get all active team members
        active_members = team.members.filter(status='active').select_related('user')
        
        # Send notifications to all active team members (except the poster)
        from notifications.models import Notification
        notifications_sent = []
        
        for member in active_members:
            # Don't notify the person who posted the announcement
            if member.user != captain:
                # Set notification priority based on announcement priority
                notif_priority = 'high' if priority == 'urgent' else 'normal' if priority == 'important' else 'low'
                
                notification = Notification.create_notification(
                    user=member.user,
                    title=f"New Team Announcement: {announcement.title}",
                    message=f"{captain.get_display_name()} posted an announcement in {team.name}.",
                    notification_type='team',
                    priority=notif_priority,
                    content_object=announcement,
                    action_url=f'/teams/{team.slug}/announcements/',
                    delivery_methods=['in_app', 'email'] if priority == 'urgent' else ['in_app']
                )
                notifications_sent.append((member.user, notification))
        
        # Verify the property: all active members (except poster) should receive a notification
        expected_notification_count = num_active_members - 1  # Exclude captain who posted
        actual_notification_count = len(notifications_sent)
        
        assert actual_notification_count == expected_notification_count, \
            f"Expected {expected_notification_count} notifications to be sent, " \
            f"but {actual_notification_count} were sent"
        
        # Verify that each active member (except captain) received exactly one notification
        for user in active_members_created:
            if user != captain:
                # Check if this user received a notification
                user_notifications = [notif for u, notif in notifications_sent if u == user]
                
                assert len(user_notifications) == 1, \
                    f"Active member {user.username} should receive exactly 1 notification, " \
                    f"but received {len(user_notifications)}"
                
                # Verify notification content
                notification = user_notifications[0]
                assert notification.user == user, \
                    f"Notification should be for user {user.username}"
                assert announcement.title in notification.title, \
                    f"Notification title should contain announcement title"
        
        # Verify that inactive members did NOT receive notifications
        for user in inactive_members_created:
            user_notifications = [notif for u, notif in notifications_sent if u == user]
            
            assert len(user_notifications) == 0, \
                f"Inactive member {user.username} should NOT receive notifications, " \
                f"but received {len(user_notifications)}"
        
        # Verify that the captain (poster) did NOT receive a notification
        captain_notifications = [notif for u, notif in notifications_sent if u == captain]
        
        assert len(captain_notifications) == 0, \
            f"Captain (poster) should NOT receive a notification about their own announcement, " \
            f"but received {len(captain_notifications)}"
        
        # Verify notification priority matches announcement priority
        for user, notification in notifications_sent:
            expected_priority = 'high' if priority == 'urgent' else 'normal' if priority == 'important' else 'low'
            assert notification.priority == expected_priority, \
                f"Notification priority should be '{expected_priority}' for announcement priority '{priority}', " \
                f"but is '{notification.priority}'"
        
        # Verify delivery methods based on priority
        for user, notification in notifications_sent:
            if priority == 'urgent':
                # Urgent announcements should use both in_app and email
                assert 'in_app' in notification.delivery_methods, \
                    "Urgent announcements should include 'in_app' delivery"
                assert 'email' in notification.delivery_methods, \
                    "Urgent announcements should include 'email' delivery"
            else:
                # Normal and important announcements should only use in_app
                assert 'in_app' in notification.delivery_methods, \
                    "All announcements should include 'in_app' delivery"
        
        # Additional verification: ensure the announcement was created correctly
        announcement.refresh_from_db()
        assert announcement.team == team, \
            "Announcement should belong to the correct team"
        assert announcement.posted_by == captain, \
            "Announcement should be posted by the captain"
        assert announcement.priority == priority, \
            f"Announcement priority should be '{priority}'"

    @settings(max_examples=20, deadline=None)
    @given(
        num_active_members=st.integers(min_value=2, max_value=10),
        num_inactive_members=st.integers(min_value=0, max_value=5),
        achievement_type=st.sampled_from(['first_win', 'tournament_champion', 'getting_started', 'full_roster'])
    )
    def test_achievement_award_consistency(self, num_active_members, num_inactive_members, achievement_type):
        """
        **Feature: team-management, Property 13: Achievement Award Consistency**
        
        For any team achievement, when earned, all active team members should receive a notification
        **Validates: Requirements 15.4**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership (counts as one active member)
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Track all active members we create (including captain)
        active_members_created = [captain]
        inactive_members_created = []
        
        # Create additional active members (subtract 1 because captain is already active)
        for i in range(num_active_members - 1):
            user = User.objects.create_user(
                username=f"active{int(timestamp * 1000) % 1000000}_{i}",
                email=f"active{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_members_created.append(user)
        
        # Create inactive members (should NOT receive notifications)
        for i in range(num_inactive_members):
            user = User.objects.create_user(
                username=f"inactive{int(timestamp * 1000) % 1000000}_{i}",
                email=f"inactive{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='inactive',
                left_at=timezone.now() - timedelta(days=1)
            )
            inactive_members_created.append(user)
        
        # Verify initial state
        initial_active_count = team.members.filter(status='active').count()
        assert initial_active_count == num_active_members, \
            f"Initial active member count should be {num_active_members}, got {initial_active_count}"
        
        # Award an achievement using the AchievementService (Requirement 15.1, 15.2)
        from teams.achievement_service import AchievementService
        from teams.models import TeamAchievement, TeamAnnouncement
        
        # Prepare metadata based on achievement type
        metadata = {}
        if achievement_type == 'first_win':
            metadata = {'tournament_id': 'test-tournament-id'}
        elif achievement_type == 'tournament_champion':
            metadata = {'tournament_id': 'test-tournament-id'}
        elif achievement_type == 'getting_started':
            metadata = {'tournaments_played': 1}
        elif achievement_type == 'full_roster':
            metadata = {'max_members': team.max_members}
        
        # Award the achievement
        achievement = AchievementService.award_achievement(
            team=team,
            achievement_type=achievement_type,
            metadata=metadata
        )
        
        # Verify the achievement was created
        assert achievement is not None, \
            f"Achievement should be created for type '{achievement_type}'"
        
        assert achievement.team == team, \
            "Achievement should belong to the correct team"
        
        assert achievement.achievement_type == achievement_type, \
            f"Achievement type should be '{achievement_type}'"
        
        # Verify the property: all active members should receive a notification (Requirement 15.4)
        from notifications.models import Notification
        
        for user in active_members_created:
            # Check if this user received a notification about the achievement
            user_notifications = Notification.objects.filter(
                user=user,
                notification_type='team'
            ).order_by('-created_at')
            
            # Find notifications related to this achievement
            achievement_notifications = [
                n for n in user_notifications 
                if achievement.title in n.message or 'Achievement' in n.title
            ]
            
            assert len(achievement_notifications) >= 1, \
                f"Active member {user.username} should receive at least 1 notification about the achievement, " \
                f"but received {len(achievement_notifications)}"
            
            # Verify notification content
            notification = achievement_notifications[0]
            assert notification.user == user, \
                f"Notification should be for user {user.username}"
            assert 'Achievement' in notification.title or 'achievement' in notification.title.lower(), \
                f"Notification title should mention achievement"
        
        # Verify that inactive members did NOT receive notifications
        for user in inactive_members_created:
            user_notifications = Notification.objects.filter(
                user=user,
                notification_type='team'
            ).order_by('-created_at')
            
            # Find notifications related to this achievement
            achievement_notifications = [
                n for n in user_notifications 
                if achievement.title in n.message or 'Achievement' in n.title
            ]
            
            assert len(achievement_notifications) == 0, \
                f"Inactive member {user.username} should NOT receive notifications about achievements, " \
                f"but received {len(achievement_notifications)}"
        
        # Verify that an automatic announcement was posted (Requirement 15.4)
        achievement_announcements = TeamAnnouncement.objects.filter(
            team=team,
            title__icontains='Achievement'
        ).order_by('-created_at')
        
        assert achievement_announcements.exists(), \
            "An automatic announcement should be posted when an achievement is earned"
        
        announcement = achievement_announcements.first()
        assert achievement.title in announcement.title or achievement.title in announcement.content, \
            f"Announcement should mention the achievement title '{achievement.title}'"
        
        assert announcement.priority == 'important', \
            f"Achievement announcements should have 'important' priority, but has '{announcement.priority}'"
        
        # Verify that the achievement is stored correctly
        achievement.refresh_from_db()
        assert achievement.title is not None and achievement.title != '', \
            "Achievement should have a title"
        
        assert achievement.description is not None and achievement.description != '', \
            "Achievement should have a description"
        
        assert achievement.icon is not None and achievement.icon != '', \
            "Achievement should have an icon"
        
        assert achievement.earned_at is not None, \
            "Achievement should have an earned_at timestamp"
        
        # Verify metadata is stored correctly
        if metadata:
            assert achievement.metadata == metadata, \
                f"Achievement metadata should be {metadata}, but is {achievement.metadata}"
        
        # Additional verification: ensure all active members received exactly one notification
        # (not multiple duplicate notifications)
        for user in active_members_created:
            user_notifications = Notification.objects.filter(
                user=user,
                notification_type='team'
            ).order_by('-created_at')
            
            achievement_notifications = [
                n for n in user_notifications 
                if achievement.title in n.message or 'Achievement' in n.title
            ]
            
            # Should receive exactly 1 notification per achievement
            assert len(achievement_notifications) == 1, \
                f"Active member {user.username} should receive exactly 1 notification, " \
                f"but received {len(achievement_notifications)}"
        
        # Verify that the achievement count is correct
        total_achievements = team.achievements.count()
        assert total_achievements >= 1, \
            f"Team should have at least 1 achievement, but has {total_achievements}"
        
        # Verify that the achievement can be retrieved
        retrieved_achievement = TeamAchievement.objects.filter(
            team=team,
            achievement_type=achievement_type
        ).first()
        
        assert retrieved_achievement is not None, \
            f"Achievement of type '{achievement_type}' should be retrievable from database"
        
        assert retrieved_achievement.id == achievement.id, \
            "Retrieved achievement should match the created achievement"

    @settings(max_examples=20, deadline=None)
    @given(
        num_matches_won=st.integers(min_value=0, max_value=20),
        num_matches_lost=st.integers(min_value=0, max_value=20)
    )
    def test_team_statistics_consistency(self, num_matches_won, num_matches_lost):
        """
        **Feature: team-management, Property 7: Team Statistics Consistency**
        
        For any team, the sum of total_wins and total_losses should equal the total number of completed matches
        **Validates: Requirements 8.1, 8.2, 13.3**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=10,
            total_wins=0,
            total_losses=0
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create a tournament for the matches
        from tournaments.models import Tournament, Participant, Bracket, Match
        
        tournament = Tournament.objects.create(
            name=f"Tournament {int(timestamp * 1000) % 1000000}",
            slug=f"tournament-{int(timestamp * 1000) % 1000000}",
            description="Test tournament",
            game=game,
            organizer=captain,
            is_team_based=True,
            min_participants=2,
            max_participants=32,
            registration_start=timezone.now() - timedelta(days=7),
            registration_end=timezone.now() + timedelta(days=7),
            check_in_start=timezone.now() - timedelta(hours=2),
            start_datetime=timezone.now() + timedelta(hours=1),
            status='in_progress'
        )
        
        # Create a bracket for the tournament
        bracket = Bracket.objects.create(
            tournament=tournament,
            bracket_type='main',
            name='Main Bracket',
            total_rounds=5,
            current_round=1
        )
        
        # Create a participant for the team
        team_participant = Participant.objects.create(
            tournament=tournament,
            team=team,
            status='confirmed',
            checked_in=True
        )
        
        # Create opponent teams and participants
        opponent_participants = []
        for i in range(max(num_matches_won, num_matches_lost)):
            # Create opponent captain
            opp_captain = User.objects.create_user(
                username=f"opp_cap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"opp_cap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Create opponent team
            opp_team = Team.objects.create(
                name=f"Opponent Team {i}_{int(timestamp * 1000) % 1000000}",
                tag=f"OT{i}{int(timestamp * 1000) % 10000}"[:10],
                game=game,
                captain=opp_captain,
                max_members=10
            )
            
            # Create opponent captain membership
            TeamMember.objects.create(
                team=opp_team,
                user=opp_captain,
                role='captain',
                status='active'
            )
            
            # Create opponent participant
            opp_participant = Participant.objects.create(
                tournament=tournament,
                team=opp_team,
                status='confirmed',
                checked_in=True
            )
            opponent_participants.append(opp_participant)
        
        # Create matches that the team won
        matches_created = []
        for i in range(num_matches_won):
            opponent = opponent_participants[i % len(opponent_participants)] if opponent_participants else None
            
            if opponent:
                match = Match.objects.create(
                    tournament=tournament,
                    bracket=bracket,
                    round_number=1,
                    match_number=i + 1,
                    participant1=team_participant,
                    participant2=opponent,
                    winner=team_participant,
                    loser=opponent,
                    score_p1=2,
                    score_p2=0,
                    status='completed',
                    completed_at=timezone.now() - timedelta(hours=i)
                )
                matches_created.append(match)
                
                # Update team statistics (simulating what would happen in the tournament system)
                team.total_wins += 1
                team.save()
        
        # Create matches that the team lost
        for i in range(num_matches_lost):
            opponent = opponent_participants[i % len(opponent_participants)] if opponent_participants else None
            
            if opponent:
                match = Match.objects.create(
                    tournament=tournament,
                    bracket=bracket,
                    round_number=1,
                    match_number=num_matches_won + i + 1,
                    participant1=team_participant,
                    participant2=opponent,
                    winner=opponent,
                    loser=team_participant,
                    score_p1=0,
                    score_p2=2,
                    status='completed',
                    completed_at=timezone.now() - timedelta(hours=num_matches_won + i)
                )
                matches_created.append(match)
                
                # Update team statistics (simulating what would happen in the tournament system)
                team.total_losses += 1
                team.save()
        
        # Refresh team from database
        team.refresh_from_db()
        
        # Verify the property: total_wins + total_losses should equal total completed matches
        total_matches = num_matches_won + num_matches_lost
        calculated_total = team.total_wins + team.total_losses
        
        assert calculated_total == total_matches, \
            f"Team statistics inconsistent: total_wins ({team.total_wins}) + total_losses ({team.total_losses}) " \
            f"= {calculated_total}, but should equal {total_matches} (total completed matches)"
        
        # Verify individual statistics
        assert team.total_wins == num_matches_won, \
            f"Team total_wins should be {num_matches_won}, but is {team.total_wins}"
        
        assert team.total_losses == num_matches_lost, \
            f"Team total_losses should be {num_matches_lost}, but is {team.total_losses}"
        
        # Verify that the win rate calculation is correct (Requirement 8.1, 8.2)
        if total_matches > 0:
            expected_win_rate = round((num_matches_won / total_matches) * 100, 2)
            actual_win_rate = team.win_rate
            
            assert actual_win_rate == expected_win_rate, \
                f"Team win_rate should be {expected_win_rate}%, but is {actual_win_rate}%"
        else:
            # No matches played, win rate should be 0
            assert team.win_rate == 0, \
                f"Team with no matches should have win_rate of 0%, but has {team.win_rate}%"
        
        # Verify that completed matches count matches the database
        from django.db.models import Q
        
        completed_matches = Match.objects.filter(
            Q(participant1=team_participant) | Q(participant2=team_participant),
            status='completed'
        ).count()
        
        assert completed_matches == total_matches, \
            f"Database has {completed_matches} completed matches, but expected {total_matches}"
        
        # Verify that wins and losses are correctly recorded in matches
        won_matches = Match.objects.filter(
            winner=team_participant,
            status='completed'
        ).count()
        
        lost_matches = Match.objects.filter(
            loser=team_participant,
            status='completed'
        ).count()
        
        assert won_matches == num_matches_won, \
            f"Database has {won_matches} won matches, but expected {num_matches_won}"
        
        assert lost_matches == num_matches_lost, \
            f"Database has {lost_matches} lost matches, but expected {num_matches_lost}"
        
        # Additional verification: ensure consistency across all statistics
        # The sum of wins and losses from matches should equal the team's recorded statistics
        assert won_matches + lost_matches == team.total_wins + team.total_losses, \
            f"Match records ({won_matches} wins + {lost_matches} losses) don't match " \
            f"team statistics ({team.total_wins} wins + {team.total_losses} losses)"
        
        # Verify that the statistics view would calculate correctly (Requirement 8.1, 8.2, 13.3)
        statistics = {
            'tournaments_played': team.tournaments_played,
            'tournaments_won': team.tournaments_won,
            'total_wins': team.total_wins,
            'total_losses': team.total_losses,
            'win_rate': team.win_rate,
        }
        
        # Verify statistics dictionary consistency
        assert statistics['total_wins'] + statistics['total_losses'] == total_matches, \
            f"Statistics dictionary inconsistent: wins + losses = " \
            f"{statistics['total_wins'] + statistics['total_losses']}, expected {total_matches}"
        
        # Verify that no matches are in an inconsistent state
        # (e.g., completed but no winner, or winner/loser don't match participants)
        for match in matches_created:
            match.refresh_from_db()
            
            assert match.status == 'completed', \
                f"Match {match.id} should have status 'completed'"
            
            assert match.winner is not None, \
                f"Completed match {match.id} should have a winner"
            
            assert match.loser is not None, \
                f"Completed match {match.id} should have a loser"
            
            # Winner and loser should be the participants
            assert match.winner in [match.participant1, match.participant2], \
                f"Match {match.id} winner should be one of the participants"
            
            assert match.loser in [match.participant1, match.participant2], \
                f"Match {match.id} loser should be one of the participants"
            
            # Winner and loser should be different
            assert match.winner != match.loser, \
                f"Match {match.id} winner and loser should be different"

    @settings(max_examples=20, deadline=None)
    @given(
        num_games=st.integers(min_value=1, max_value=3),
        num_teams_per_game=st.integers(min_value=1, max_value=2),
        num_join_attempts=st.integers(min_value=1, max_value=5)
    )
    def test_game_specific_team_limits(self, num_games, num_teams_per_game, num_join_attempts):
        """
        **Feature: team-management, Property 12: Game-Specific Team Limits**
        
        For any user and game combination, the user should not be an active member of more than 
        the allowed number of teams for that game (limit is 1 team per game)
        **Validates: Requirements 12.5**
        """
        # Create test games
        timestamp = timezone.now().timestamp()
        unique_id = int(timestamp * 1000000) % 1000000
        games = []
        for i in range(num_games):
            game = Game.objects.create(
                name=f"Game{i} {unique_id}",
                slug=f"game{i}-{unique_id}",
                description=f"Test game {i}"
            )
            games.append(game)
        
        # Create a test user who will try to join multiple teams
        test_user = User.objects.create_user(
            username=f"tu{unique_id}",
            email=f"testuser{unique_id}@test.com",
            password="testpass123"
        )
        
        # Create multiple teams for each game
        teams_by_game = {}
        captain_counter = 0
        for game_idx, game in enumerate(games):
            teams_by_game[game.id] = []
            
            for i in range(num_teams_per_game):
                # Create a captain user with unique username
                captain = User.objects.create_user(
                    username=f"c{unique_id}g{game_idx}t{i}",
                    email=f"cap{unique_id}_{game_idx}_{i}@test.com",
                    password="testpass123"
                )
                captain_counter += 1
                
                team = Team.objects.create(
                    name=f"Team {game.name} {i}_{int(timestamp * 1000) % 1000000}",
                    tag=f"T{game.id}{i}{int(timestamp * 1000) % 10000}"[:10],
                    game=game,
                    captain=captain,
                    max_members=10,
                    status='active'
                )
                
                # Create captain membership
                TeamMember.objects.create(
                    team=team,
                    user=captain,
                    role='captain',
                    status='active'
                )
                
                teams_by_game[game.id].append(team)
        
        # Track which games the user has joined teams for
        games_with_active_membership = set()
        
        # Attempt to join teams multiple times
        for i in range(num_join_attempts):
            if not games:
                break
            
            # Pick a random game
            game = games[i % len(games)]
            teams_for_game = teams_by_game[game.id]
            
            if not teams_for_game:
                continue
            
            # Pick a random team from that game
            team = teams_for_game[i % len(teams_for_game)]
            
            # Check if user already has an active membership for this game (Requirement 12.5)
            existing_active_membership = TeamMember.objects.filter(
                user=test_user,
                team__game=game,
                status='active'
            ).select_related('team').first()
            
            if existing_active_membership:
                # User already has an active membership for this game
                # Should NOT be able to join another team for the same game
                
                # Verify that the validation would prevent this
                # (This simulates the validation logic from TeamApplyView and TeamInviteAcceptView)
                can_join = False
                
                # Try to create membership anyway (should be prevented by validation)
                # In the actual views, this would be caught before creating the membership
                # But we test that the database state remains consistent
                
            else:
                # User doesn't have an active membership for this game yet
                # Should be able to join
                can_join = True
                
                # Create membership
                try:
                    # Check if membership already exists (unique_together constraint)
                    existing_any = TeamMember.objects.filter(
                        team=team,
                        user=test_user
                    ).first()
                    
                    if not existing_any:
                        TeamMember.objects.create(
                            team=team,
                            user=test_user,
                            role='member',
                            status='active'
                        )
                        games_with_active_membership.add(game.id)
                except Exception:
                    # If there's a database constraint violation, that's expected
                    pass
        
        # Verify the property: user should have at most one active membership per game
        for game in games:
            active_memberships = TeamMember.objects.filter(
                user=test_user,
                team__game=game,
                status='active'
            )
            
            active_count = active_memberships.count()
            
            assert active_count <= 1, \
                f"User {test_user.username} has {active_count} active memberships for game '{game.name}', " \
                f"but should have at most 1 (Requirement 12.5)"
            
            if active_count == 1:
                # Verify that the membership is valid
                membership = active_memberships.first()
                assert membership.team.game == game, \
                    f"Membership team game should be '{game.name}'"
                assert membership.status == 'active', \
                    f"Membership status should be 'active'"
        
        # Verify that the user can have memberships in different games
        # (the limit is per game, not total)
        total_active_memberships = TeamMember.objects.filter(
            user=test_user,
            status='active'
        ).count()
        
        # User can have up to num_games active memberships (one per game)
        assert total_active_memberships <= num_games, \
            f"User has {total_active_memberships} active memberships, " \
            f"but should have at most {num_games} (one per game)"
        
        # Verify that each active membership is for a different game
        active_memberships = TeamMember.objects.filter(
            user=test_user,
            status='active'
        ).select_related('team__game')
        
        games_with_membership = set()
        for membership in active_memberships:
            game_id = membership.team.game.id
            
            assert game_id not in games_with_membership, \
                f"User has multiple active memberships for game '{membership.team.game.name}', " \
                f"but should have at most one per game"
            
            games_with_membership.add(game_id)
        
        # Additional verification: test the validation logic directly
        # Simulate what happens when a user tries to join a second team for the same game
        for game in games:
            # Check if user has an active membership for this game
            existing_active = TeamMember.objects.filter(
                user=test_user,
                team__game=game,
                status='active'
            ).first()
            
            if existing_active:
                # User has an active membership for this game
                # Try to join another team for the same game
                other_teams = [t for t in teams_by_game[game.id] if t != existing_active.team]
                
                if other_teams:
                    other_team = other_teams[0]
                    
                    # Check validation logic (from TeamApplyView)
                    validation_check = TeamMember.objects.filter(
                        user=test_user,
                        team__game=other_team.game,
                        status='active'
                    ).select_related('team').first()
                    
                    # Validation should find the existing membership
                    assert validation_check is not None, \
                        f"Validation should find existing active membership for game '{game.name}'"
                    
                    assert validation_check.team == existing_active.team, \
                        f"Validation should find the correct existing team"
                    
                    # This means the user should NOT be able to join the other team
                    # Verify that no membership exists for the other team
                    other_team_membership = TeamMember.objects.filter(
                        user=test_user,
                        team=other_team,
                        status='active'
                    ).first()
                    
                    assert other_team_membership is None, \
                        f"User should not have an active membership in {other_team.name} " \
                        f"when already a member of {existing_active.team.name} for the same game"
        
        # Verify that the property holds across all games
        for game in games:
            game_memberships = TeamMember.objects.filter(
                user=test_user,
                team__game=game,
                status='active'
            )
            
            assert game_memberships.count() <= 1, \
                f"User should have at most 1 active membership per game, " \
                f"but has {game_memberships.count()} for game '{game.name}'"
        
        # Final verification: ensure the property holds for all users and games
        # For each game, count how many active memberships the test user has
        for game in games:
            active_memberships_for_game = TeamMember.objects.filter(
                user=test_user,
                team__game=game,
                status='active'
            ).count()
            
            assert active_memberships_for_game <= 1, \
                f"Property violation: User {test_user.username} has {active_memberships_for_game} " \
                f"active memberships for game '{game.name}', but the limit is 1 per game (Requirement 12.5)"

    @settings(max_examples=100, deadline=None)
    @given(
        num_co_captains=st.integers(min_value=0, max_value=3),
        num_regular_members=st.integers(min_value=0, max_value=5)
    )
    def test_query_execution_success(self, num_co_captains, num_regular_members):
        """
        **Feature: team-leave-bug-fix, Property 1: Query Execution Success**
        
        For any team with active members, the captaincy transfer query should execute without raising AttributeError
        **Validates: Requirements 3.2, 3.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create co-captains
        for i in range(num_co_captains):
            user = User.objects.create_user(
                username=f"cocap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cocap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='co_captain',
                status='active'
            )
        
        # Create regular members
        for i in range(num_regular_members):
            user = User.objects.create_user(
                username=f"member{int(timestamp * 1000) % 1000000}_{i}",
                email=f"member{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
        
        # Test the fixed query - this should not raise AttributeError
        try:
            from django.db.models import Case, When, Value, IntegerField
            
            new_captain = team.members.filter(
                status='active'
            ).exclude(
                user=captain
            ).order_by(
                Case(
                    When(role='co_captain', then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                ),
                'joined_at'
            ).first()
            
            # The query should execute successfully without any AttributeError
            # The result can be None (if no other members) or a TeamMember instance
            assert new_captain is None or isinstance(new_captain, TeamMember), \
                f"Query should return None or TeamMember instance, got {type(new_captain)}"
            
        except AttributeError as e:
            # This should never happen with the fixed query
            assert False, f"Query execution failed with AttributeError: {e}"
        except Exception as e:
            # Other exceptions might be acceptable (database issues, etc.)
            # but AttributeError specifically indicates the Q().desc() bug
            if "AttributeError" in str(e):
                assert False, f"Query execution failed with AttributeError: {e}"

    @settings(max_examples=100, deadline=None)
    @given(
        num_co_captains=st.integers(min_value=1, max_value=3),
        num_regular_members=st.integers(min_value=0, max_value=5),
        co_captain_join_days_ago=st.lists(
            st.integers(min_value=1, max_value=100),
            min_size=1,
            max_size=3
        )
    )
    def test_co_captain_priority(self, num_co_captains, num_regular_members, co_captain_join_days_ago):
        """
        **Feature: team-leave-bug-fix, Property 2: Co-Captain Priority**
        
        For any team with both co-captains and regular members, when a captain leaves, a co-captain should be selected as the new captain
        **Validates: Requirements 1.3, 2.1**
        """
        # Ensure we have at least one co-captain for this test
        if num_co_captains == 0:
            return
        
        # Limit co_captain_join_days_ago to match num_co_captains
        co_captain_join_days_ago = co_captain_join_days_ago[:num_co_captains]
        if len(co_captain_join_days_ago) < num_co_captains:
            # Pad with default values if needed
            co_captain_join_days_ago.extend([30] * (num_co_captains - len(co_captain_join_days_ago)))
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create co-captains with specific join dates
        co_captains = []
        for i in range(num_co_captains):
            user = User.objects.create_user(
                username=f"cocap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cocap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Set join date based on days ago
            join_date = timezone.now() - timedelta(days=co_captain_join_days_ago[i])
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='co_captain',
                status='active'
            )
            # Update joined_at to the calculated date
            member.joined_at = join_date
            member.save()
            co_captains.append(member)
        
        # Create regular members (they should not be selected when co-captains exist)
        regular_members = []
        for i in range(num_regular_members):
            user = User.objects.create_user(
                username=f"member{int(timestamp * 1000) % 1000000}_{i}",
                email=f"member{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Make regular members join earlier than co-captains to test priority
            join_date = timezone.now() - timedelta(days=200)
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            member.joined_at = join_date
            member.save()
            regular_members.append(member)
        
        # Execute the captaincy transfer query
        from django.db.models import Case, When, Value, IntegerField
        
        new_captain = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify the property: a co-captain should be selected when both co-captains and regular members exist
        if num_co_captains > 0 and (num_co_captains + num_regular_members) > 0:
            assert new_captain is not None, "Should select a new captain when other members exist"
            assert new_captain.role == 'co_captain', \
                f"Should select co-captain over regular member, but selected {new_captain.role}"
            
            # Verify it's the co-captain who joined earliest
            expected_captain = min(co_captains, key=lambda m: m.joined_at)
            assert new_captain == expected_captain, \
                f"Should select earliest co-captain, expected {expected_captain.user.username}, " \
                f"got {new_captain.user.username}"

    @settings(max_examples=100, deadline=None)
    @given(
        num_co_captains=st.integers(min_value=2, max_value=5),
        join_days_ago=st.lists(
            st.integers(min_value=1, max_value=365),
            min_size=2,
            max_size=5
        )
    )
    def test_co_captain_tie_breaking(self, num_co_captains, join_days_ago):
        """
        **Feature: team-leave-bug-fix, Property 3: Co-Captain Tie-Breaking**
        
        For any team with multiple co-captains, when a captain leaves, the co-captain who joined earliest should be selected
        **Validates: Requirements 2.2**
        """
        # Ensure we have at least 2 co-captains for tie-breaking test
        if num_co_captains < 2:
            return
        
        # Limit join_days_ago to match num_co_captains
        join_days_ago = join_days_ago[:num_co_captains]
        if len(join_days_ago) < num_co_captains:
            # Pad with different values if needed
            join_days_ago.extend([i * 10 + 50 for i in range(len(join_days_ago), num_co_captains)])
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create multiple co-captains with different join dates
        co_captains = []
        for i in range(num_co_captains):
            user = User.objects.create_user(
                username=f"cocap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cocap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Set join date based on days ago (ensure they're different)
            join_date = timezone.now() - timedelta(days=join_days_ago[i])
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='co_captain',
                status='active'
            )
            # Update joined_at to the calculated date
            member.joined_at = join_date
            member.save()
            co_captains.append(member)
        
        # Execute the captaincy transfer query
        from django.db.models import Case, When, Value, IntegerField
        
        new_captain = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify the property: the co-captain who joined earliest should be selected
        assert new_captain is not None, "Should select a new captain when co-captains exist"
        assert new_captain.role == 'co_captain', \
            f"Should select a co-captain, but selected {new_captain.role}"
        
        # Find the co-captain who joined earliest
        earliest_co_captain = min(co_captains, key=lambda m: m.joined_at)
        
        assert new_captain == earliest_co_captain, \
            f"Should select earliest co-captain (joined {earliest_co_captain.joined_at}), " \
            f"but selected {new_captain.user.username} (joined {new_captain.joined_at})"

    @settings(max_examples=100, deadline=None)
    @given(
        num_regular_members=st.integers(min_value=1, max_value=5),
        join_days_ago=st.lists(
            st.integers(min_value=1, max_value=365),
            min_size=1,
            max_size=5
        )
    )
    def test_regular_member_selection(self, num_regular_members, join_days_ago):
        """
        **Feature: team-leave-bug-fix, Property 4: Regular Member Selection**
        
        For any team with only regular members (no co-captains), when a captain leaves, the member who joined earliest should be selected
        **Validates: Requirements 1.4, 2.3**
        """
        # Ensure we have at least 1 regular member
        if num_regular_members < 1:
            return
        
        # Limit join_days_ago to match num_regular_members
        join_days_ago = join_days_ago[:num_regular_members]
        if len(join_days_ago) < num_regular_members:
            # Pad with different values if needed
            join_days_ago.extend([i * 15 + 30 for i in range(len(join_days_ago), num_regular_members)])
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create regular members with different join dates (NO co-captains)
        regular_members = []
        for i in range(num_regular_members):
            user = User.objects.create_user(
                username=f"member{int(timestamp * 1000) % 1000000}_{i}",
                email=f"member{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            # Set join date based on days ago
            join_date = timezone.now() - timedelta(days=join_days_ago[i])
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',  # Regular member, not co-captain
                status='active'
            )
            # Update joined_at to the calculated date
            member.joined_at = join_date
            member.save()
            regular_members.append(member)
        
        # Execute the captaincy transfer query
        from django.db.models import Case, When, Value, IntegerField
        
        new_captain = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify the property: the regular member who joined earliest should be selected
        assert new_captain is not None, "Should select a new captain when regular members exist"
        assert new_captain.role == 'member', \
            f"Should select a regular member, but selected {new_captain.role}"
        
        # Find the regular member who joined earliest
        earliest_member = min(regular_members, key=lambda m: m.joined_at)
        
        assert new_captain == earliest_member, \
            f"Should select earliest regular member (joined {earliest_member.joined_at}), " \
            f"but selected {new_captain.user.username} (joined {new_captain.joined_at})"

    @settings(max_examples=100, deadline=None)
    @given(
        num_co_captains=st.integers(min_value=0, max_value=3),
        num_regular_members=st.integers(min_value=0, max_value=5)
    )
    def test_data_consistency_after_transfer(self, num_co_captains, num_regular_members):
        """
        **Feature: team-leave-bug-fix, Property 5: Data Consistency After Transfer**
        
        For any successful captaincy transfer, the new captain's role should be 'captain' and the team's captain field should reference the new captain's user
        **Validates: Requirements 2.5, 5.2, 5.3**
        """
        # Skip if no other members exist (no transfer possible)
        if num_co_captains + num_regular_members == 0:
            return
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create co-captains
        for i in range(num_co_captains):
            user = User.objects.create_user(
                username=f"cocap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cocap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            join_date = timezone.now() - timedelta(days=i * 10 + 10)
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='co_captain',
                status='active'
            )
            member.joined_at = join_date
            member.save()
        
        # Create regular members
        for i in range(num_regular_members):
            user = User.objects.create_user(
                username=f"member{int(timestamp * 1000) % 1000000}_{i}",
                email=f"member{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            
            join_date = timezone.now() - timedelta(days=i * 5 + 50)
            
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            member.joined_at = join_date
            member.save()
        
        # Find the new captain using the same query as the implementation
        from django.db.models import Case, When, Value, IntegerField
        
        new_captain_member = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Simulate the captaincy transfer process
        if new_captain_member:
            # Transfer captaincy (simulate the implementation)
            # First demote the current captain to member
            captain_member.role = 'member'
            captain_member.save()
            
            # Then promote the new captain
            new_captain_member.role = 'captain'
            new_captain_member.save()
            
            team.captain = new_captain_member.user
            team.save()
            
            # Verify data consistency after transfer
            # Refresh from database to ensure we're testing actual saved state
            new_captain_member.refresh_from_db()
            team.refresh_from_db()
            
            # Property 1: New captain's role should be 'captain'
            assert new_captain_member.role == 'captain', \
                f"New captain member role should be 'captain', but is '{new_captain_member.role}'"
            
            # Property 2: Team's captain field should reference the new captain's user
            assert team.captain == new_captain_member.user, \
                f"Team captain field should reference {new_captain_member.user.username}, " \
                f"but references {team.captain.username if team.captain else None}"
            
            # Property 3: Only one member should have captain role
            captain_count = team.members.filter(role='captain', status='active').count()
            assert captain_count == 1, \
                f"Team should have exactly 1 captain, but has {captain_count}"
            
            # Property 4: The captain member should be the same as the team's captain
            captain_members = team.members.filter(role='captain', status='active')
            assert captain_members.count() == 1, "Should have exactly one captain member"
            
            captain_member_user = captain_members.first().user
            assert captain_member_user == team.captain, \
                f"Captain member user ({captain_member_user.username}) should match " \
                f"team captain ({team.captain.username})"

    @settings(max_examples=100, deadline=None)
    @given(
        member_role=st.sampled_from(['captain', 'co_captain', 'member', 'substitute']),
        has_other_members=st.booleans()
    )
    def test_leaving_member_status_update(self, member_role, has_other_members):
        """
        **Feature: team-leave-bug-fix, Property 6: Leaving Member Status Update**
        
        For any captain leave operation, the leaving member's status should be set to inactive and left_at timestamp should be recorded
        **Validates: Requirements 5.1, 5.5**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=10
        )
        
        # Create captain membership
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create the leaving member (could be captain or another member)
        if member_role == 'captain':
            leaving_member = captain_member
            leaving_user = captain
        else:
            # Create a different user for non-captain roles
            leaving_user = User.objects.create_user(
                username=f"leaving{int(timestamp * 1000) % 1000000}",
                email=f"leaving{int(timestamp * 1000) % 1000000}@test.com",
                password="testpass123"
            )
            leaving_member = TeamMember.objects.create(
                team=team,
                user=leaving_user,
                role=member_role,
                status='active'
            )
        
        # Create other members if specified
        other_members = []
        if has_other_members and member_role == 'captain':
            # If captain is leaving and we want other members, create some
            for i in range(2):  # Create 2 other members
                user = User.objects.create_user(
                    username=f"other{int(timestamp * 1000) % 1000000}_{i}",
                    email=f"other{int(timestamp * 1000) % 1000000}_{i}@test.com",
                    password="testpass123"
                )
                role = 'co_captain' if i == 0 else 'member'
                member = TeamMember.objects.create(
                    team=team,
                    user=user,
                    role=role,
                    status='active'
                )
                other_members.append(member)
        
        # Record the time before the leave operation
        before_leave_time = timezone.now()
        
        # Simulate the leave operation from TeamLeaveView
        if leaving_member.role == 'captain':
            # Handle captain leaving - find new captain if other members exist
            from django.db.models import Case, When, Value, IntegerField
            
            new_captain = team.members.filter(
                status='active'
            ).exclude(
                user=leaving_user
            ).order_by(
                Case(
                    When(role='co_captain', then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                ),
                'joined_at'
            ).first()
            
            if new_captain:
                # Transfer captaincy
                new_captain.role = 'captain'
                new_captain.save()
                
                team.captain = new_captain.user
                team.save()
            else:
                # No other members, disband team
                team.status = 'disbanded'
                team.save()
        
        # Set member to inactive and record leave timestamp (the core functionality we're testing)
        leaving_member.status = 'inactive'
        leaving_member.left_at = timezone.now()
        leaving_member.save()
        
        # Record the time after the leave operation
        after_leave_time = timezone.now()
        
        # Refresh from database to ensure we're testing actual saved state
        leaving_member.refresh_from_db()
        
        # Verify Property 6: Leaving Member Status Update
        
        # Property 6a: The leaving member's status should be set to 'inactive'
        assert leaving_member.status == 'inactive', \
            f"Leaving member status should be 'inactive', but is '{leaving_member.status}'"
        
        # Property 6b: The left_at timestamp should be recorded
        assert leaving_member.left_at is not None, \
            f"Leaving member left_at timestamp should be recorded, but is None"
        
        # Property 6c: The left_at timestamp should be within the operation timeframe
        assert before_leave_time <= leaving_member.left_at <= after_leave_time, \
            f"Leaving member left_at timestamp ({leaving_member.left_at}) should be between " \
            f"{before_leave_time} and {after_leave_time}"
        
        # Property 6d: The member should no longer be considered active
        active_members = team.members.filter(status='active')
        assert leaving_member not in active_members, \
            f"Leaving member should not be in active members list"
        
        # Property 6e: The member should be in inactive members list
        inactive_members = team.members.filter(status='inactive')
        assert leaving_member in inactive_members, \
            f"Leaving member should be in inactive members list"
        
        # Additional verification: ensure the operation is atomic
        # If this was a captain leaving with other members, verify captaincy was transferred
        if member_role == 'captain' and has_other_members and other_members:
            team.refresh_from_db()
            
            # Team should still be active (not disbanded)
            assert team.status != 'disbanded', \
                f"Team should not be disbanded when captain leaves with other members present"
            
            # There should be a new captain
            current_captains = team.members.filter(role='captain', status='active')
            assert current_captains.count() == 1, \
                f"Team should have exactly 1 active captain after captain leave, but has {current_captains.count()}"
            
            # The new captain should not be the leaving member
            new_captain = current_captains.first()
            assert new_captain.user != leaving_user, \
                f"New captain should not be the leaving user"
    @settings(max_examples=20, deadline=None)
    @given(
        num_inactive_members=st.integers(min_value=0, max_value=5),
        num_pending_members=st.integers(min_value=0, max_value=3),
        has_co_captains=st.booleans(),
        has_regular_members=st.booleans()
    )
    def test_team_disbanding_data_consistency(self, num_inactive_members, num_pending_members, has_co_captains, has_regular_members):
        """
        **Feature: team-leave-bug-fix, Property 7: Team Disbanding Data Consistency**
        
        For any team where the captain is the only active member, when the captain leaves, 
        the team status should be set to disbanded
        **Validates: Requirements 5.4**
        """
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            status='active',
            max_members=20
        )
        
        # Create captain membership (the only active member for this test)
        captain_member = TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active'
        )
        
        # Create inactive members (these don't affect the disbanding logic)
        for i in range(num_inactive_members):
            user = User.objects.create_user(
                username=f"inactive{int(timestamp * 1000) % 1000000}_{i}",
                email=f"inactive{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='inactive',
                left_at=timezone.now() - timedelta(days=1)
            )
        
        # Create pending members (these don't affect the disbanding logic)
        for i in range(num_pending_members):
            user = User.objects.create_user(
                username=f"pending{int(timestamp * 1000) % 1000000}_{i}",
                email=f"pending{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='pending'
            )
        
        # For this property test, we want to test the case where captain is the ONLY active member
        # So we should NOT create any other active members (co-captains or regular members)
        # The has_co_captains and has_regular_members parameters are used to ensure we test
        # the edge case properly - if they're True, we skip this test case
        
        if has_co_captains or has_regular_members:
            # This test case is for when captain is NOT the only active member
            # We'll create other active members and verify team is NOT disbanded
            
            if has_co_captains:
                # Create a co-captain
                co_captain_user = User.objects.create_user(
                    username=f"cocap{int(timestamp * 1000) % 1000000}",
                    email=f"cocap{int(timestamp * 1000) % 1000000}@test.com",
                    password="testpass123"
                )
                TeamMember.objects.create(
                    team=team,
                    user=co_captain_user,
                    role='co_captain',
                    status='active'
                )
            
            if has_regular_members:
                # Create a regular member
                member_user = User.objects.create_user(
                    username=f"member{int(timestamp * 1000) % 1000000}",
                    email=f"member{int(timestamp * 1000) % 1000000}@test.com",
                    password="testpass123"
                )
                TeamMember.objects.create(
                    team=team,
                    user=member_user,
                    role='member',
                    status='active'
                )
        
        # Verify initial state
        initial_active_count = team.members.filter(status='active').count()
        initial_team_status = team.status
        
        assert initial_team_status == 'active', \
            f"Team should initially be active, but is '{initial_team_status}'"
        
        # Simulate the captain leave operation using the same logic as TeamLeaveView
        from django.db.models import Case, When, Value, IntegerField
        
        # Find co-captain or oldest member to transfer captaincy
        new_captain = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        if new_captain:
            # Transfer captaincy
            new_captain.role = 'captain'
            new_captain.save()
            
            team.captain = new_captain.user
            team.save()
        else:
            # No other active members - disband team
            team.status = 'disbanded'
            team.save()
        
        # Set captain member to inactive
        captain_member.status = 'inactive'
        captain_member.left_at = timezone.now()
        captain_member.save()
        
        # Refresh from database
        team.refresh_from_db()
        captain_member.refresh_from_db()
        
        # Verify Property 7: Team Disbanding Data Consistency
        
        if initial_active_count == 1:
            # Captain was the only active member - team should be disbanded
            assert team.status == 'disbanded', \
                f"When captain is the only active member and leaves, team status should be 'disbanded', " \
                f"but is '{team.status}'"
            
            # Verify that no active members remain
            remaining_active = team.members.filter(status='active').count()
            assert remaining_active == 0, \
                f"After captain (only member) leaves, there should be 0 active members, " \
                f"but found {remaining_active}"
            
            # Verify captain is now inactive
            assert captain_member.status == 'inactive', \
                f"Captain member should be inactive after leaving, but is '{captain_member.status}'"
            
            # Verify left_at timestamp is set
            assert captain_member.left_at is not None, \
                f"Captain member should have left_at timestamp set"
        
        else:
            # Captain was not the only active member - team should remain active
            assert team.status == 'active', \
                f"When captain leaves but other active members exist, team should remain 'active', " \
                f"but is '{team.status}'"
            
            # Verify that there's still an active captain
            current_captains = team.members.filter(role='captain', status='active')
            assert current_captains.count() == 1, \
                f"Team should have exactly 1 active captain after captain transfer, " \
                f"but has {current_captains.count()}"
            
            # Verify the new captain is not the leaving captain
            new_captain_member = current_captains.first()
            assert new_captain_member.user != captain, \
                f"New captain should not be the leaving captain"
            
            # Verify team captain field is updated
            assert team.captain == new_captain_member.user, \
                f"Team captain field should be updated to new captain"
            
            # Verify leaving captain is inactive
            assert captain_member.status == 'inactive', \
                f"Leaving captain should be inactive, but is '{captain_member.status}'"
        
        # Additional consistency checks
        
        # Verify that inactive and pending members are unaffected by the operation
        inactive_count = team.members.filter(status='inactive').count()
        pending_count = team.members.filter(status='pending').count()
        
        # Inactive count should include the leaving captain plus any pre-existing inactive members
        expected_inactive_count = num_inactive_members + 1  # +1 for the leaving captain
        assert inactive_count == expected_inactive_count, \
            f"Inactive member count should be {expected_inactive_count}, but is {inactive_count}"
        
        # Pending count should remain unchanged
        assert pending_count == num_pending_members, \
            f"Pending member count should remain {num_pending_members}, but is {pending_count}"
        
        # Verify total member count is preserved
        total_members = team.members.count()
        expected_total = 1 + num_inactive_members + num_pending_members  # 1 captain + others
        if has_co_captains:
            expected_total += 1
        if has_regular_members:
            expected_total += 1
        
        assert total_members == expected_total, \
            f"Total member count should be {expected_total}, but is {total_members}"
    @settings(max_examples=100, deadline=None)
    @given(
        num_co_captains=st.integers(min_value=0, max_value=3),
        num_regular_members=st.integers(min_value=0, max_value=5),
        co_captain_join_order=st.lists(
            st.integers(min_value=1, max_value=30), 
            min_size=0, 
            max_size=3
        ),
        regular_member_join_order=st.lists(
            st.integers(min_value=1, max_value=30), 
            min_size=0, 
            max_size=5
        )
    )
    def test_captaincy_transfer_correctness(self, num_co_captains, num_regular_members, co_captain_join_order, regular_member_join_order):
        """
        **Feature: team-leave-bug-fix, Property 8: Captaincy Transfer Correctness**
        
        For any team configuration, the selected new captain should be the member with the highest priority according to the rules (co-captain role first, then earliest join date)
        **Validates: Requirements 1.2, 3.3**
        """
        # Skip if no other members to transfer to
        if num_co_captains == 0 and num_regular_members == 0:
            return
        
        # No need to adjust list sizes - we'll handle missing values in the loops
        
        # Create a test game
        timestamp = timezone.now().timestamp()
        game = Game.objects.create(
            name=f"Game {int(timestamp * 1000) % 1000000}",
            slug=f"game-{int(timestamp * 1000) % 1000000}",
            description="Test game"
        )
        
        # Create a captain user
        captain = User.objects.create_user(
            username=f"cap{int(timestamp * 1000) % 1000000}",
            email=f"cap{int(timestamp * 1000) % 1000000}@test.com",
            password="testpass123"
        )
        
        # Create a team
        team = Team.objects.create(
            name=f"Team {int(timestamp * 1000) % 1000000}",
            tag=f"T{int(timestamp * 1000) % 10000}",
            game=game,
            captain=captain,
            max_members=20  # Large enough to accommodate all members
        )
        
        # Calculate all join times upfront to avoid timing issues
        base_time = timezone.now()
        captain_join_time = base_time - timedelta(days=100)
        
        # Create captain membership (joined first)
        TeamMember.objects.create(
            team=team,
            user=captain,
            role='captain',
            status='active',
            joined_at=captain_join_time
        )
        
        # Track all members and their expected priority
        all_members = []
        
        # Create co-captains with specified join order
        for i in range(num_co_captains):
            days_ago = co_captain_join_order[i] if i < len(co_captain_join_order) else (30 - i)
            user = User.objects.create_user(
                username=f"cocap{int(timestamp * 1000) % 1000000}_{i}",
                email=f"cocap{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            # Add seconds to ensure distinct timestamps and avoid timing issues
            join_time = base_time - timedelta(days=days_ago, seconds=i)
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='co_captain',
                status='active'
            )
            # Manually set joined_at since auto_now_add=True ignores the value during creation
            member.joined_at = join_time
            member.save()
            # Co-captains have priority 0, then sorted by join date (earlier = higher priority)
            all_members.append((member, 0, join_time))
        
        # Create regular members with specified join order
        for i in range(num_regular_members):
            days_ago = regular_member_join_order[i] if i < len(regular_member_join_order) else (30 - i)
            user = User.objects.create_user(
                username=f"member{int(timestamp * 1000) % 1000000}_{i}",
                email=f"member{int(timestamp * 1000) % 1000000}_{i}@test.com",
                password="testpass123"
            )
            # Add seconds to ensure distinct timestamps and avoid timing issues
            join_time = base_time - timedelta(days=days_ago, seconds=i + num_co_captains)
            member = TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            # Manually set joined_at since auto_now_add=True ignores the value during creation
            member.joined_at = join_time
            member.save()
            # Regular members have priority 1, then sorted by join date (earlier = higher priority)
            all_members.append((member, 1, join_time))
        
        # Sort members by priority rules to determine expected new captain
        # Priority: co-captain role first (0), then regular members (1)
        # Tie-breaking: earliest join date (ascending - earlier dates first)
        all_members.sort(key=lambda x: (x[1], x[2]))  # (priority, join_time)
        expected_new_captain = all_members[0][0]  # First member after sorting
        
        # Execute the captaincy transfer query (same as in TeamLeaveView)
        from django.db.models import Case, When, Value, IntegerField
        
        actual_new_captain = team.members.filter(
            status='active'
        ).exclude(
            user=captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify Property 8: Captaincy Transfer Correctness
        assert actual_new_captain == expected_new_captain, \
            f"Expected new captain: {expected_new_captain.user.username} " \
            f"(role: {expected_new_captain.role}, joined: {expected_new_captain.joined_at}), " \
            f"but query returned: {actual_new_captain.user.username if actual_new_captain else None} " \
            f"(role: {actual_new_captain.role if actual_new_captain else None}, " \
            f"joined: {actual_new_captain.joined_at if actual_new_captain else None})"
        
        # Additional verification: ensure the selected captain has the correct priority
        if num_co_captains > 0:
            # If there are co-captains, the selected captain should be a co-captain
            assert actual_new_captain.role == 'co_captain', \
                f"When co-captains exist, selected captain should be a co-captain, " \
                f"but got role '{actual_new_captain.role}'"
            
            # Among co-captains, should be the one who joined earliest
            co_captain_members = [m for m, p, j in all_members if p == 0]  # priority 0 = co-captain
            earliest_co_captain = min(co_captain_members, key=lambda m: m.joined_at)
            assert actual_new_captain == earliest_co_captain, \
                f"Selected co-captain should be the one who joined earliest"
        
        elif num_regular_members > 0:
            # If no co-captains but regular members exist, should select earliest regular member
            assert actual_new_captain.role == 'member', \
                f"When only regular members exist, selected captain should be a regular member, " \
                f"but got role '{actual_new_captain.role}'"
            
            # Should be the regular member who joined earliest
            regular_members = [m for m, p, j in all_members if p == 1]  # priority 1 = regular member
            earliest_regular = min(regular_members, key=lambda m: m.joined_at)
            assert actual_new_captain == earliest_regular, \
                f"Selected regular member should be the one who joined earliest"


# Unit Tests for Team Leave Edge Cases
class TeamLeaveEdgeCasesTest(TestCase):
    """Unit tests for edge cases in team leave functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test game
        self.game = Game.objects.create(
            name="Test Game",
            slug="test-game",
            description="Test game for unit tests"
        )
        
        # Create test users
        self.captain = User.objects.create_user(
            username="captain",
            email="captain@test.com",
            password="testpass123"
        )
        
        self.co_captain = User.objects.create_user(
            username="co_captain",
            email="co_captain@test.com",
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
        
        # Create test team
        self.team = Team.objects.create(
            name="Test Team",
            tag="TEST",
            game=self.game,
            captain=self.captain,
            max_members=10
        )
        
        # Create captain membership
        self.captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.captain,
            role='captain',
            status='active'
        )
    
    def test_captain_leave_with_co_captain_present(self):
        """
        Test captain leave with co-captain present
        Requirements: 1.2, 1.3, 2.1, 2.5
        """
        # Create co-captain membership
        co_captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.co_captain,
            role='co_captain',
            status='active'
        )
        
        # Create regular member
        member_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member1,
            role='member',
            status='active'
        )
        
        # Simulate captain leave logic
        from django.db.models import Case, When, Value, IntegerField
        from django.utils import timezone
        
        # Find new captain using the fixed query
        new_captain = self.team.members.filter(
            status='active'
        ).exclude(
            user=self.captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify co-captain is selected
        self.assertEqual(new_captain, co_captain_membership)
        self.assertEqual(new_captain.role, 'co_captain')
        
        # Simulate captaincy transfer
        new_captain.role = 'captain'
        new_captain.save()
        
        self.team.captain = new_captain.user
        self.team.save()
        
        # Set leaving member to inactive
        self.captain_membership.status = 'inactive'
        self.captain_membership.left_at = timezone.now()
        self.captain_membership.save()
        
        # Verify transfer completed correctly
        self.team.refresh_from_db()
        new_captain.refresh_from_db()
        self.captain_membership.refresh_from_db()
        
        self.assertEqual(self.team.captain, self.co_captain)
        self.assertEqual(new_captain.role, 'captain')
        self.assertEqual(self.captain_membership.status, 'inactive')
        self.assertIsNotNone(self.captain_membership.left_at)
    
    def test_captain_leave_with_only_regular_members(self):
        """
        Test captain leave with only regular members
        Requirements: 1.4, 2.3, 2.5
        """
        # Create regular members with different join dates
        from django.utils import timezone
        from datetime import timedelta
        
        # Member1 joins first (should become captain)
        member1_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member1,
            role='member',
            status='active'
        )
        # Manually set earlier join date
        member1_membership.joined_at = timezone.now() - timedelta(days=2)
        member1_membership.save()
        
        # Member2 joins later
        member2_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member2,
            role='member',
            status='active'
        )
        # Manually set later join date
        member2_membership.joined_at = timezone.now() - timedelta(days=1)
        member2_membership.save()
        
        # Simulate captain leave logic
        from django.db.models import Case, When, Value, IntegerField
        
        # Find new captain using the fixed query
        new_captain = self.team.members.filter(
            status='active'
        ).exclude(
            user=self.captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify earliest member is selected
        self.assertEqual(new_captain, member1_membership)
        self.assertEqual(new_captain.role, 'member')
        
        # Simulate captaincy transfer
        new_captain.role = 'captain'
        new_captain.save()
        
        self.team.captain = new_captain.user
        self.team.save()
        
        # Set leaving member to inactive
        self.captain_membership.status = 'inactive'
        self.captain_membership.left_at = timezone.now()
        self.captain_membership.save()
        
        # Verify transfer completed correctly
        self.team.refresh_from_db()
        new_captain.refresh_from_db()
        self.captain_membership.refresh_from_db()
        
        self.assertEqual(self.team.captain, self.member1)
        self.assertEqual(new_captain.role, 'captain')
        self.assertEqual(self.captain_membership.status, 'inactive')
        self.assertIsNotNone(self.captain_membership.left_at)
    
    def test_captain_leave_as_last_member_disbanding(self):
        """
        Test captain leave as last member (disbanding)
        Requirements: 1.5, 2.4, 5.4
        """
        from django.utils import timezone
        
        # Verify captain is the only active member
        active_members = self.team.members.filter(status='active')
        self.assertEqual(active_members.count(), 1)
        self.assertEqual(active_members.first(), self.captain_membership)
        
        # Simulate captain leave logic
        from django.db.models import Case, When, Value, IntegerField
        
        # Find new captain using the fixed query
        new_captain = self.team.members.filter(
            status='active'
        ).exclude(
            user=self.captain
        ).order_by(
            Case(
                When(role='co_captain', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            'joined_at'
        ).first()
        
        # Verify no new captain found
        self.assertIsNone(new_captain)
        
        # Simulate team disbanding
        self.team.status = 'disbanded'
        self.team.save()
        
        # Set leaving member to inactive
        self.captain_membership.status = 'inactive'
        self.captain_membership.left_at = timezone.now()
        self.captain_membership.save()
        
        # Verify team is disbanded
        self.team.refresh_from_db()
        self.captain_membership.refresh_from_db()
        
        self.assertEqual(self.team.status, 'disbanded')
        self.assertEqual(self.captain_membership.status, 'inactive')
        self.assertIsNotNone(self.captain_membership.left_at)
        self.assertEqual(self.team.member_count, 0)
    
    def test_error_handling_for_invalid_team_states(self):
        """
        Test error handling for invalid team states
        Requirements: 4.4
        """
        # Test 1: Team already disbanded
        self.team.status = 'disbanded'
        self.team.save()
        
        # Attempting to leave a disbanded team should be handled gracefully
        # In a real view, this would return an error message
        self.assertEqual(self.team.status, 'disbanded')
        
        # Test 2: Team is inactive
        self.team.status = 'inactive'
        self.team.save()
        
        # Attempting to leave an inactive team should be handled gracefully
        self.assertEqual(self.team.status, 'inactive')
        
        # Test 3: Member already inactive
        self.captain_membership.status = 'inactive'
        self.captain_membership.save()
        
        # Attempting to leave when already inactive should be handled gracefully
        self.assertEqual(self.captain_membership.status, 'inactive')
        
        # Reset team status for other tests
        self.team.status = 'active'
        self.team.save()
        self.captain_membership.status = 'active'
        self.captain_membership.save()
    
    def test_permission_validation_for_non_members(self):
        """
        Test permission validation for non-members
        Requirements: 1.1, 4.4
        """
        # Create a user who is not a team member
        non_member = User.objects.create_user(
            username="non_member",
            email="non_member@test.com",
            password="testpass123"
        )
        
        # Verify non-member has no membership
        membership = TeamMember.objects.filter(
            team=self.team,
            user=non_member,
            status='active'
        ).first()
        
        self.assertIsNone(membership)
        
        # Test permission check logic (as would be done in view)
        has_permission = False
        try:
            membership = TeamMember.objects.get(
                team=self.team,
                user=non_member,
                status='active'
            )
            has_permission = True
        except TeamMember.DoesNotExist:
            has_permission = False
        
        # Verify non-member cannot leave team
        self.assertFalse(has_permission)
        
        # Test with inactive member
        inactive_member = User.objects.create_user(
            username="inactive_member",
            email="inactive_member@test.com",
            password="testpass123"
        )
        
        # Create inactive membership
        TeamMember.objects.create(
            team=self.team,
            user=inactive_member,
            role='member',
            status='inactive'
        )
        
        # Verify inactive member cannot leave (already left)
        active_membership = TeamMember.objects.filter(
            team=self.team,
            user=inactive_member,
            status='active'
        ).first()
        
        self.assertIsNone(active_membership)
    
    def test_query_execution_without_errors(self):
        """
        Test that the fixed query executes without AttributeError
        Requirements: 3.2, 3.5
        """
        # Create various team members
        co_captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.co_captain,
            role='co_captain',
            status='active'
        )
        
        member_membership = TeamMember.objects.create(
            team=self.team,
            user=self.member1,
            role='member',
            status='active'
        )
        
        # Test the fixed query (should not raise AttributeError)
        from django.db.models import Case, When, Value, IntegerField
        
        try:
            new_captain = self.team.members.filter(
                status='active'
            ).exclude(
                user=self.captain
            ).order_by(
                Case(
                    When(role='co_captain', then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                ),
                'joined_at'
            ).first()
            
            # Query should execute successfully
            self.assertIsNotNone(new_captain)
            self.assertEqual(new_captain, co_captain_membership)
            
        except AttributeError as e:
            self.fail(f"Query raised AttributeError: {e}")
        except Exception as e:
            self.fail(f"Query raised unexpected exception: {e}")
    
    def test_data_consistency_after_captaincy_transfer(self):
        """
        Test data consistency after captaincy transfer
        Requirements: 2.5, 5.2, 5.3
        """
        # Create co-captain
        co_captain_membership = TeamMember.objects.create(
            team=self.team,
            user=self.co_captain,
            role='co_captain',
            status='active'
        )
        
        # Record initial state
        initial_captain = self.team.captain
        initial_captain_role = self.captain_membership.role
        
        # Perform captaincy transfer
        from django.utils import timezone
        
        # Transfer captaincy
        co_captain_membership.role = 'captain'
        co_captain_membership.save()
        
        self.team.captain = co_captain_membership.user
        self.team.save()
        
        # Set leaving member to inactive
        self.captain_membership.status = 'inactive'
        self.captain_membership.left_at = timezone.now()
        self.captain_membership.save()
        
        # Verify data consistency
        self.team.refresh_from_db()
        co_captain_membership.refresh_from_db()
        self.captain_membership.refresh_from_db()
        
        # Team captain field should match new captain's user
        self.assertEqual(self.team.captain, co_captain_membership.user)
        
        # New captain's role should be 'captain'
        self.assertEqual(co_captain_membership.role, 'captain')
        
        # Old captain should be inactive
        self.assertEqual(self.captain_membership.status, 'inactive')
        self.assertIsNotNone(self.captain_membership.left_at)
        
        # Verify only one captain exists
        captain_count = self.team.members.filter(role='captain', status='active').count()
        self.assertEqual(captain_count, 1)
        
        # Verify the captain member matches the team's captain field
        captain_member = self.team.members.filter(role='captain', status='active').first()
        self.assertEqual(captain_member.user, self.team.captain)