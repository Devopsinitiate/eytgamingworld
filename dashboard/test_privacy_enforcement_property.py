"""
Property-based tests for privacy enforcement functionality.

This module tests the privacy enforcement property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User
from dashboard.services import PrivacyService
import uuid


@pytest.mark.django_db
class TestPrivacyEnforcement:
    """
    **Feature: user-profile-dashboard, Property 8: Privacy enforcement**
    
    For any user with privacy settings, those settings must be enforced correctly.
    
    **Validates: Requirements 2.5, 10.2, 10.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        online_status_visible=st.booleans(),
        activity_visible=st.booleans(),
        statistics_visible=st.booleans()
    )
    def test_privacy_settings_are_enforced(self, online_status_visible, activity_visible, statistics_visible):
        """Property: Privacy settings control what viewers can see"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create profile owner with specific privacy settings
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.online_status_visible = online_status_visible
        owner.activity_visible = activity_visible
        owner.statistics_visible = statistics_visible
        owner.save()
        
        # Create a viewer (not the owner)
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Test statistics visibility
        can_view_stats = PrivacyService.can_view_statistics(viewer, owner)
        assert can_view_stats == statistics_visible, \
            f"Statistics visibility should be {statistics_visible}, got {can_view_stats}"
        
        # Test activity visibility
        can_view_activity = PrivacyService.can_view_activity(viewer, owner)
        assert can_view_activity == activity_visible, \
            f"Activity visibility should be {activity_visible}, got {can_view_activity}"
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    def test_owner_can_always_view_own_profile(self):
        """Property: Users can always view their own profile data"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user with all privacy settings disabled
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        user.online_status_visible = False
        user.activity_visible = False
        user.statistics_visible = False
        user.save()
        
        # Owner should always be able to view their own data
        assert PrivacyService.can_view_profile(user, user) is True
        assert PrivacyService.can_view_statistics(user, user) is True
        assert PrivacyService.can_view_activity(user, user) is True
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        statistics_visible=st.booleans()
    )
    def test_statistics_visibility_enforcement(self, statistics_visible):
        """Property: Statistics visibility setting is enforced"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create owner
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.statistics_visible = statistics_visible
        owner.save()
        
        # Create viewer
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Test that statistics visibility matches setting
        can_view = PrivacyService.can_view_statistics(viewer, owner)
        assert can_view == statistics_visible, \
            f"Expected statistics visibility to be {statistics_visible}, got {can_view}"
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        activity_visible=st.booleans()
    )
    def test_activity_visibility_enforcement(self, activity_visible):
        """Property: Activity visibility setting is enforced"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create owner
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.activity_visible = activity_visible
        owner.save()
        
        # Create viewer
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Test that activity visibility matches setting
        can_view = PrivacyService.can_view_activity(viewer, owner)
        assert can_view == activity_visible, \
            f"Expected activity visibility to be {activity_visible}, got {can_view}"
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    def test_anonymous_users_respect_privacy(self):
        """Property: Anonymous users can only see public data"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user with private settings
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        user.online_status_visible = False
        user.activity_visible = False
        user.statistics_visible = False
        user.save()
        
        # Anonymous user (None) should not be able to view private data
        assert PrivacyService.can_view_statistics(None, user) is False
        assert PrivacyService.can_view_activity(None, user) is False
        assert PrivacyService.can_view_profile(None, user) is False
        
        # Cleanup
        user.delete()
    
    def test_public_profile_is_viewable_by_all(self):
        """Property: Public profiles are viewable by all authenticated users"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user with all public settings
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.online_status_visible = True
        owner.activity_visible = True
        owner.statistics_visible = True
        owner.save()
        
        # Create viewer
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Viewer should be able to see everything
        assert PrivacyService.can_view_profile(viewer, owner) is True
        assert PrivacyService.can_view_statistics(viewer, owner) is True
        assert PrivacyService.can_view_activity(viewer, owner) is True
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        online_status_visible=st.booleans(),
        activity_visible=st.booleans(),
        statistics_visible=st.booleans()
    )
    def test_filter_profile_data_respects_privacy(self, online_status_visible, activity_visible, statistics_visible):
        """Property: Filtered profile data respects privacy settings"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create owner with specific privacy settings
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.online_status_visible = online_status_visible
        owner.activity_visible = activity_visible
        owner.statistics_visible = statistics_visible
        owner.save()
        
        # Create viewer
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Create profile data with all fields
        profile_data = {
            'user': owner,
            'statistics': {'win_rate': 75.0},
            'activity_feed': [{'type': 'tournament_completed'}],
            'is_online': True,
            'achievements': [],
            'teams': []
        }
        
        # Filter data based on privacy settings
        filtered_data = PrivacyService.filter_profile_data(viewer, profile_data)
        
        # Verify statistics are included only if visible
        if statistics_visible:
            assert 'statistics' in filtered_data, \
                "Statistics should be included when statistics_visible is True"
        else:
            assert 'statistics' not in filtered_data, \
                "Statistics should not be included when statistics_visible is False"
        
        # Verify activity is included only if visible
        if activity_visible:
            assert 'activity_feed' in filtered_data, \
                "Activity feed should be included when activity_visible is True"
        else:
            assert 'activity_feed' not in filtered_data, \
                "Activity feed should not be included when activity_visible is False"
        
        # Verify online status is included only if visible
        if online_status_visible:
            assert 'is_online' in filtered_data, \
                "Online status should be included when online_status_visible is True"
        else:
            assert 'is_online' not in filtered_data, \
                "Online status should not be included when online_status_visible is False"
        
        # Basic info should always be included
        assert 'username' in filtered_data
        assert 'display_name' in filtered_data
        
        # Public data should always be included
        assert 'achievements' in filtered_data
        assert 'teams' in filtered_data
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    def test_privacy_settings_update_correctly(self):
        """Property: Privacy settings can be updated and are persisted"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user with default settings
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Update privacy settings
        new_settings = {
            'online_status_visible': False,
            'activity_visible': False,
            'statistics_visible': False
        }
        PrivacyService.update_privacy_settings(user.id, new_settings)
        
        # Verify settings were updated
        user.refresh_from_db()
        assert user.online_status_visible is False
        assert user.activity_visible is False
        assert user.statistics_visible is False
        
        # Update again with different settings
        new_settings = {
            'online_status_visible': True,
            'activity_visible': True,
            'statistics_visible': True
        }
        PrivacyService.update_privacy_settings(user.id, new_settings)
        
        # Verify settings were updated again
        user.refresh_from_db()
        assert user.online_status_visible is True
        assert user.activity_visible is True
        assert user.statistics_visible is True
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_viewers=st.integers(min_value=1, max_value=5),
        statistics_visible=st.booleans()
    )
    def test_privacy_enforced_for_multiple_viewers(self, num_viewers, statistics_visible):
        """Property: Privacy settings are enforced consistently for all viewers"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create owner
        owner = User.objects.create_user(
            email=f'owner_{unique_id}@example.com',
            username=f'owner_{unique_id}',
            password='testpass123'
        )
        owner.statistics_visible = statistics_visible
        owner.save()
        
        # Create multiple viewers
        viewers = []
        for i in range(num_viewers):
            viewer = User.objects.create_user(
                email=f'viewer{i}_{unique_id}@example.com',
                username=f'viewer{i}_{unique_id}',
                password='testpass123'
            )
            viewers.append(viewer)
        
        # All viewers should get the same result
        for viewer in viewers:
            can_view = PrivacyService.can_view_statistics(viewer, owner)
            assert can_view == statistics_visible, \
                f"All viewers should get consistent result: {statistics_visible}"
        
        # Cleanup
        owner.delete()
        for viewer in viewers:
            viewer.delete()
