"""
Property-based tests for recommendation dismissal functionality.

This module tests the recommendation dismissal persistence property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.utils import timezone
from datetime import timedelta
from core.models import User
from dashboard.models import Recommendation, Achievement
from dashboard.services import RecommendationService
from django.contrib.contenttypes.models import ContentType
import uuid


@pytest.mark.django_db
class TestRecommendationDismissal:
    """
    **Feature: user-profile-dashboard, Property 15: Recommendation dismissal persistence**
    
    For any recommendation, when dismissed, it should remain dismissed and not reappear.
    
    **Validates: Requirements 13.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_recommendations=st.integers(min_value=1, max_value=10),
        num_to_dismiss=st.integers(min_value=0, max_value=10)
    )
    def test_recommendation_dismissal_persistence(self, num_recommendations, num_to_dismiss):
        """Property: Dismissed recommendations remain dismissed"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create achievements to recommend (simpler than tournaments)
        achievements = []
        for i in range(num_recommendations):
            achievement = Achievement.objects.create(
                name=f'Achievement {i} {unique_id}',
                slug=f'achievement-{i}-{unique_id}',
                description=f'Test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            achievements.append(achievement)
        
        # Create recommendations
        content_type = ContentType.objects.get_for_model(Achievement)
        recommendations = []
        for i, achievement in enumerate(achievements):
            rec = Recommendation.objects.create(
                user=user,
                recommendation_type='tournament',
                content_type=content_type,
                object_id=achievement.id,
                score=float(100 - i * 5),
                reason=f'Matches your skill level',
                expires_at=timezone.now() + timedelta(hours=24)
            )
            recommendations.append(rec)
        
        # Dismiss some recommendations
        num_to_dismiss = min(num_to_dismiss, num_recommendations)
        dismissed_ids = []
        for i in range(num_to_dismiss):
            RecommendationService.dismiss_recommendation(user.id, recommendations[i].id)
            dismissed_ids.append(recommendations[i].id)
        
        # Verify dismissed recommendations are marked as dismissed
        for rec_id in dismissed_ids:
            rec = Recommendation.objects.get(id=rec_id)
            assert rec.is_dismissed is True, \
                f"Recommendation {rec_id} should be marked as dismissed"
            assert rec.dismissed_at is not None, \
                f"Recommendation {rec_id} should have dismissed_at timestamp"
        
        # Verify non-dismissed recommendations are not marked as dismissed
        non_dismissed_ids = [rec.id for rec in recommendations[num_to_dismiss:]]
        for rec_id in non_dismissed_ids:
            rec = Recommendation.objects.get(id=rec_id)
            assert rec.is_dismissed is False, \
                f"Recommendation {rec_id} should not be marked as dismissed"
            assert rec.dismissed_at is None, \
                f"Recommendation {rec_id} should not have dismissed_at timestamp"
        
        # Property: Count of dismissed recommendations should match
        dismissed_count = Recommendation.objects.filter(
            user=user,
            is_dismissed=True
        ).count()
        assert dismissed_count == num_to_dismiss, \
            f"Expected {num_to_dismiss} dismissed recommendations, got {dismissed_count}"
        
        # Cleanup
        for achievement in achievements:
            achievement.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_recommendations=st.integers(min_value=2, max_value=10)
    )
    def test_dismissal_does_not_affect_other_recommendations(self, num_recommendations):
        """Property: Dismissing one recommendation doesn't affect others"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create achievements
        achievements = []
        content_type = ContentType.objects.get_for_model(Achievement)
        recommendations = []
        for i in range(num_recommendations):
            achievement = Achievement.objects.create(
                name=f'Achievement {i} {unique_id}',
                slug=f'achievement-{i}-{unique_id}',
                description=f'Test achievement {i}',
                achievement_type='platform',
                rarity='common',
                is_active=True
            )
            achievements.append(achievement)
            
            rec = Recommendation.objects.create(
                user=user,
                recommendation_type='tournament',
                content_type=content_type,
                object_id=achievement.id,
                score=float(100 - i * 5),
                reason='Matches your skill level',
                expires_at=timezone.now() + timedelta(hours=24)
            )
            recommendations.append(rec)
        
        # Dismiss the first recommendation
        RecommendationService.dismiss_recommendation(user.id, recommendations[0].id)
        
        # Verify only the first is dismissed
        first_rec = Recommendation.objects.get(id=recommendations[0].id)
        assert first_rec.is_dismissed is True
        
        # Verify all others are not dismissed
        for rec in recommendations[1:]:
            other_rec = Recommendation.objects.get(id=rec.id)
            assert other_rec.is_dismissed is False, \
                f"Recommendation {rec.id} should not be dismissed"
        
        # Property: Exactly 1 recommendation should be dismissed
        dismissed_count = Recommendation.objects.filter(
            user=user,
            is_dismissed=True
        ).count()
        assert dismissed_count == 1, \
            f"Expected exactly 1 dismissed recommendation, got {dismissed_count}"
        
        # Cleanup
        for achievement in achievements:
            achievement.delete()
        user.delete()
    
    def test_dismissal_timestamp_is_set(self):
        """Property: Dismissed recommendations have a timestamp"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create an achievement
        achievement = Achievement.objects.create(
            name=f'Achievement {unique_id}',
            slug=f'achievement-{unique_id}',
            description='Test achievement',
            achievement_type='platform',
            rarity='common',
            is_active=True
        )
        
        # Create recommendation
        content_type = ContentType.objects.get_for_model(Achievement)
        rec = Recommendation.objects.create(
            user=user,
            recommendation_type='tournament',
            content_type=content_type,
            object_id=achievement.id,
            score=100.0,
            reason='Matches your skill level',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Record time before dismissal
        before_dismissal = timezone.now()
        
        # Dismiss recommendation
        RecommendationService.dismiss_recommendation(user.id, rec.id)
        
        # Record time after dismissal
        after_dismissal = timezone.now()
        
        # Verify dismissed_at is set and within expected range
        rec.refresh_from_db()
        assert rec.dismissed_at is not None, \
            "dismissed_at should be set"
        assert before_dismissal <= rec.dismissed_at <= after_dismissal, \
            f"dismissed_at should be between {before_dismissal} and {after_dismissal}"
        
        # Cleanup
        achievement.delete()
        user.delete()
    
    def test_cannot_dismiss_other_users_recommendation(self):
        """Property: Users cannot dismiss recommendations belonging to other users"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create two users
        user1 = User.objects.create_user(
            email=f'test1_{unique_id}@example.com',
            username=f'testuser1_{unique_id}',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            email=f'test2_{unique_id}@example.com',
            username=f'testuser2_{unique_id}',
            password='testpass123'
        )
        
        # Create an achievement
        achievement = Achievement.objects.create(
            name=f'Achievement {unique_id}',
            slug=f'achievement-{unique_id}',
            description='Test achievement',
            achievement_type='platform',
            rarity='common',
            is_active=True
        )
        
        # Create recommendation for user1
        content_type = ContentType.objects.get_for_model(Achievement)
        rec = Recommendation.objects.create(
            user=user1,
            recommendation_type='tournament',
            content_type=content_type,
            object_id=achievement.id,
            score=100.0,
            reason='Matches your skill level',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Try to dismiss user1's recommendation as user2
        with pytest.raises(ValueError, match="Recommendation does not belong to this user"):
            RecommendationService.dismiss_recommendation(user2.id, rec.id)
        
        # Verify recommendation is not dismissed
        rec.refresh_from_db()
        assert rec.is_dismissed is False, \
            "Recommendation should not be dismissed"
        
        # Cleanup
        achievement.delete()
        user1.delete()
        user2.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_dismissals=st.integers(min_value=1, max_value=5)
    )
    def test_multiple_dismissals_are_idempotent(self, num_dismissals):
        """Property: Dismissing the same recommendation multiple times is idempotent"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create an achievement
        achievement = Achievement.objects.create(
            name=f'Achievement {unique_id}',
            slug=f'achievement-{unique_id}',
            description='Test achievement',
            achievement_type='platform',
            rarity='common',
            is_active=True
        )
        
        # Create recommendation
        content_type = ContentType.objects.get_for_model(Achievement)
        rec = Recommendation.objects.create(
            user=user,
            recommendation_type='tournament',
            content_type=content_type,
            object_id=achievement.id,
            score=100.0,
            reason='Matches your skill level',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Dismiss multiple times
        first_dismissed_at = None
        for i in range(num_dismissals):
            RecommendationService.dismiss_recommendation(user.id, rec.id)
            rec.refresh_from_db()
            
            if i == 0:
                first_dismissed_at = rec.dismissed_at
            
            # Verify it's still dismissed
            assert rec.is_dismissed is True, \
                f"Recommendation should be dismissed after dismissal {i+1}"
        
        # Property: dismissed_at should not change after first dismissal
        rec.refresh_from_db()
        # Allow small time difference due to database precision
        time_diff = abs((rec.dismissed_at - first_dismissed_at).total_seconds())
        assert time_diff < 1, \
            f"dismissed_at should remain the same after multiple dismissals"
        
        # Cleanup
        achievement.delete()
        user.delete()
