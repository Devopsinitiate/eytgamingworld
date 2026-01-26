"""
Property-based tests for achievement showcase functionality.

This module tests the achievement showcase limit property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from core.models import User
from dashboard.models import Achievement, UserAchievement
from dashboard.services import AchievementService
import uuid


@pytest.mark.django_db
class TestAchievementShowcaseLimit:
    """
    **Feature: user-profile-dashboard, Property 10: Achievement showcase limit**
    
    For any user, the number of achievements in showcase must not exceed 6.
    
    **Validates: Requirements 7.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_achievements=st.integers(min_value=0, max_value=20),
        num_to_showcase=st.integers(min_value=0, max_value=20)
    )
    def test_achievement_showcase_limit(self, num_achievements, num_to_showcase):
        """Property: User can have at most 6 achievements in showcase"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create achievements
        achievements = []
        for i in range(num_achievements):
            achievement = Achievement.objects.create(
                name=f'Achievement {i} {unique_id}',
                slug=f'achievement-{i}-{unique_id}',
                description=f'Test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            achievements.append(achievement)
        
        # Award achievements to user
        achievement_ids = []
        for achievement in achievements:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_completed=True,
                earned_at=timezone.now()
            )
            achievement_ids.append(achievement.id)
        
        # Try to set achievements to showcase using the service method
        # Limit to the number of achievements we actually have
        num_to_showcase = min(num_to_showcase, num_achievements)
        
        if num_to_showcase > 0:
            # Get the achievement IDs to showcase
            showcase_ids = achievement_ids[:num_to_showcase]
            
            if num_to_showcase <= 6:
                # Should succeed - use the service method
                AchievementService.update_showcase(user.id, showcase_ids)
                expected_showcased = num_to_showcase
            else:
                # Should raise ValueError for more than 6 achievements
                with pytest.raises(ValueError, match="Cannot showcase more than 6 achievements"):
                    AchievementService.update_showcase(user.id, showcase_ids)
                # After the exception, no achievements should be showcased
                expected_showcased = 0
        else:
            # No achievements to showcase
            expected_showcased = 0
        
        # Query achievements in showcase
        showcased = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        # Property 1: Number of showcased achievements must not exceed 6
        assert showcased <= 6, \
            f"User has {showcased} achievements in showcase, which exceeds the limit of 6"
        
        # Property 2: Showcased count should match expected
        assert showcased == expected_showcased, \
            f"Expected {expected_showcased} showcased achievements, got {showcased}"
        
        # Cleanup
        for achievement in achievements:
            achievement.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_achievements=st.integers(min_value=7, max_value=20)
    )
    def test_showcase_limit_enforcement_with_service(self, num_achievements):
        """Property: Showcase limit is enforced when using update_showcase method"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create and award achievements
        achievement_ids = []
        for i in range(num_achievements):
            achievement = Achievement.objects.create(
                name=f'Achievement {i} {unique_id}',
                slug=f'achievement-{i}-{unique_id}',
                description=f'Test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_completed=True,
                earned_at=timezone.now()
            )
            
            achievement_ids.append(achievement.id)
        
        # Try to showcase all achievements (more than 6) - should raise ValueError
        with pytest.raises(ValueError, match="Cannot showcase more than 6 achievements"):
            AchievementService.update_showcase(user.id, achievement_ids)
        
        # Verify no achievements are showcased after the failed attempt
        showcased_count = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        assert showcased_count == 0, \
            f"Expected 0 achievements in showcase after failed attempt, got {showcased_count}"
        
        # Now try with exactly 6 achievements - should succeed
        AchievementService.update_showcase(user.id, achievement_ids[:6])
        
        # Verify exactly 6 achievements are showcased
        showcased_count = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        assert showcased_count == 6, \
            f"Expected exactly 6 achievements in showcase, got {showcased_count}"
        
        # Property: Showcase order should be 1-6 (service uses 1-based ordering)
        showcase_orders = list(UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).values_list('showcase_order', flat=True).order_by('showcase_order'))
        
        assert showcase_orders == [1, 2, 3, 4, 5, 6], \
            f"Expected showcase orders [1, 2, 3, 4, 5, 6], got {showcase_orders}"
        
        # Cleanup
        Achievement.objects.filter(id__in=achievement_ids).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        initial_showcase_count=st.integers(min_value=0, max_value=6),
        additional_achievements=st.integers(min_value=1, max_value=10)
    )
    def test_showcase_limit_when_adding_more(self, initial_showcase_count, additional_achievements):
        """Property: Adding more achievements to showcase respects the 6 limit"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create initial achievements
        initial_achievement_ids = []
        for i in range(initial_showcase_count):
            achievement = Achievement.objects.create(
                name=f'Initial Achievement {i} {unique_id}',
                slug=f'initial-achievement-{i}-{unique_id}',
                description=f'Initial test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_completed=True,
                earned_at=timezone.now()
            )
            initial_achievement_ids.append(achievement.id)
        
        # Set initial showcase using service method
        if initial_showcase_count > 0:
            AchievementService.update_showcase(user.id, initial_achievement_ids)
        
        # Create additional achievements
        additional_achievement_ids = []
        for i in range(additional_achievements):
            achievement = Achievement.objects.create(
                name=f'Additional Achievement {i} {unique_id}',
                slug=f'additional-achievement-{i}-{unique_id}',
                description=f'Additional test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_completed=True,
                earned_at=timezone.now()
            )
            additional_achievement_ids.append(achievement.id)
        
        # Try to showcase initial + additional achievements
        all_achievement_ids = initial_achievement_ids + additional_achievement_ids
        total_requested = len(all_achievement_ids)
        
        if total_requested <= 6:
            # Should succeed
            AchievementService.update_showcase(user.id, all_achievement_ids)
            expected_showcased = total_requested
        else:
            # Should fail - trying to showcase more than 6
            with pytest.raises(ValueError, match="Cannot showcase more than 6 achievements"):
                AchievementService.update_showcase(user.id, all_achievement_ids)
            # After failure, should still have the initial showcase
            expected_showcased = initial_showcase_count
        
        # Verify total showcase count
        total_showcased = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        # Property 1: Total showcased must not exceed 6
        assert total_showcased <= 6, \
            f"Total showcased {total_showcased} exceeds limit of 6"
        
        # Property 2: Total showcased should match expected
        assert total_showcased == expected_showcased, \
            f"Expected {expected_showcased} showcased achievements, got {total_showcased}"
        
        # Cleanup
        user.delete()
    
    def test_showcase_limit_edge_case_exactly_six(self):
        """Edge case: Exactly 6 achievements should all be showcaseable"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create exactly 6 achievements
        achievement_ids = []
        for i in range(6):
            achievement = Achievement.objects.create(
                name=f'Achievement {i} {unique_id}',
                slug=f'achievement-{i}-{unique_id}',
                description=f'Test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                is_completed=True,
                earned_at=timezone.now()
            )
            achievement_ids.append(achievement.id)
        
        # Showcase all 6 using service method
        AchievementService.update_showcase(user.id, achievement_ids)
        
        # Verify all 6 are showcased
        showcased_count = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        assert showcased_count == 6, \
            f"Expected exactly 6 achievements in showcase, got {showcased_count}"
        
        # Cleanup
        user.delete()
    
    def test_showcase_limit_edge_case_zero(self):
        """Edge case: User with no achievements should have 0 in showcase"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with no achievements
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Verify no achievements in showcase
        showcased_count = UserAchievement.objects.filter(
            user=user,
            in_showcase=True
        ).count()
        
        assert showcased_count == 0, \
            f"Expected 0 achievements in showcase for user with no achievements, got {showcased_count}"
        
        # Cleanup
        user.delete()
