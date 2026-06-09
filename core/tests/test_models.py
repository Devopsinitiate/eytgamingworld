# core/tests/test_models.py
"""Tests for core app models: User, Game, UserGameProfile, SiteSettings, Player, Video, NewsArticle, Product."""

import pytest
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.models import Game, UserGameProfile, SiteSettings, Player, Video, NewsArticle, Product

User = get_user_model()


class CoreModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.game = Game.objects.create(name="League of Legends", slug="lol")

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertFalse(self.user.is_staff)

    def test_user_display_name_falls_back_to_username(self):
        self.assertEqual(self.user.get_display_name(), "testuser")

    def test_user_get_full_name_falls_back(self):
        self.assertEqual(self.user.get_full_name(), "testuser")

    def test_user_get_full_name_with_first_last(self):
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.assertEqual(self.user.get_full_name(), "John Doe")

    def test_user_get_short_name(self):
        self.user.first_name = "John"
        self.assertEqual(self.user.get_short_name(), "John")

    def test_user_roles(self):
        self.assertFalse(self.user.can_organize_tournaments())
        self.assertFalse(self.user.can_coach())
        self.user.role = 'organizer'
        self.assertTrue(self.user.can_organize_tournaments())
        self.user.role = 'coach'
        self.assertTrue(self.user.can_coach())

    def test_add_points_and_level_up(self):
        self.assertEqual(self.user.level, 1)
        self.user.add_points(199)
        self.assertEqual(self.user.level, 2)
        self.user.add_points(1)
        self.assertEqual(self.user.level, 3)

    def test_update_level_no_change(self):
        result = self.user.update_level()
        self.assertFalse(result)

    def test_age_no_dob(self):
        self.assertIsNone(self.user.age())

    def test_age_with_dob(self):
        from dateutil.relativedelta import relativedelta
        self.user.date_of_birth = timezone.now().date() - relativedelta(years=20)
        self.assertEqual(self.user.age(), 20)

    def test_requires_parental_consent_under_18(self):
        from dateutil.relativedelta import relativedelta
        self.user.date_of_birth = timezone.now().date() - relativedelta(years=16)
        self.assertTrue(self.user.requires_parental_consent())

    def test_requires_parental_consent_over_18(self):
        from dateutil.relativedelta import relativedelta
        self.user.date_of_birth = timezone.now().date() - relativedelta(years=20)
        self.assertFalse(self.user.requires_parental_consent())

    def test_verify_email(self):
        self.user.verify_email()
        self.assertTrue(self.user.is_verified)
        self.assertIsNotNone(self.user.email_verified_at)

    def test_lock_account(self):
        self.user.lock_account("Suspicious activity")
        self.assertTrue(self.user.account_locked)
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.account_locked_reason, "Suspicious activity")

    def test_unlock_account(self):
        self.user.lock_account("test")
        self.user.unlock_account()
        self.assertFalse(self.user.account_locked)
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_record_failed_login(self):
        for i in range(4):
            self.user.record_failed_login()
        self.assertEqual(self.user.failed_login_attempts, 4)
        self.assertTrue(self.user.is_active)

    def test_record_failed_login_locks_at_5(self):
        for i in range(5):
            self.user.record_failed_login()
        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertFalse(self.user.is_active)

    def test_reset_failed_logins(self):
        self.user.failed_login_attempts = 3
        self.user.save()
        self.user.reset_failed_logins()
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_check_profile_completeness_incomplete(self):
        self.assertFalse(self.user.check_profile_completeness())

    def test_check_profile_completeness_complete(self):
        from dateutil.relativedelta import relativedelta
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.user.date_of_birth = timezone.now().date() - relativedelta(years=20)
        self.user.country = "US"
        self.assertTrue(self.user.check_profile_completeness())

    def test_game_creation(self):
        game = Game.objects.get(slug="lol")
        self.assertEqual(game.name, "League of Legends")

    def test_game_str(self):
        self.assertEqual(str(self.game), "League of Legends")

    def test_user_game_profile_creation(self):
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game,
            rank="Gold",
            mmr=1500,
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.game, self.game)
        self.assertEqual(profile.rank, "Gold")
        self.assertEqual(profile.mmr, 1500)

    def test_user_game_profile_str(self):
        profile = UserGameProfile.objects.create(user=self.user, game=self.game)
        self.assertIn("testuser", str(profile))
        self.assertIn("League of Legends", str(profile))

    def test_win_rate_zero_matches(self):
        profile = UserGameProfile.objects.create(user=self.user, game=self.game)
        self.assertEqual(profile.win_rate, 0)

    def test_win_rate_calculation(self):
        profile = UserGameProfile.objects.create(
            user=self.user, game=self.game,
            matches_played=10, matches_won=7,
        )
        self.assertEqual(profile.win_rate, 70.0)

    def test_main_game_uniqueness(self):
        profile1 = UserGameProfile.objects.create(
            user=self.user, game=self.game, is_main_game=True,
        )
        game2 = Game.objects.create(name="Valorant", slug="valorant")
        profile2 = UserGameProfile.objects.create(
            user=self.user, game=game2, is_main_game=True,
        )
        profile1.refresh_from_db()
        self.assertFalse(profile1.is_main_game)
        self.assertTrue(profile2.is_main_game)

    def test_site_settings_singleton(self):
        settings1 = SiteSettings.objects.create(site_name="EYTGaming")
        settings2 = SiteSettings.load()
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(settings2.site_name, "EYTGaming")

    def test_site_settings_maintenance_mode(self):
        settings = SiteSettings.load()
        settings.maintenance_mode = True
        settings.save()
        loaded = SiteSettings.load()
        self.assertTrue(loaded.maintenance_mode)

    def test_player_creation(self):
        player = Player.objects.create(
            gamer_tag="ProGamer",
            role="Mid Laner",
            game=self.game,
            country_flag="US",
            image="players/test.jpg",
            rank="Challenger",
        )
        self.assertEqual(player.gamer_tag, "ProGamer")
        self.assertIn("ProGamer", str(player))

    def test_video_creation(self):
        video = Video.objects.create(
            title="Best Moments",
            thumbnail="videos/test.jpg",
            video_url="https://youtube.com/watch?v=test",
            duration=timedelta(seconds=120),
        )
        self.assertEqual(video.title, "Best Moments")
        self.assertEqual(video.duration_formatted, "2:00")

    def test_video_is_published_default(self):
        video = Video.objects.create(
            title="Test", thumbnail="videos/t.jpg",
            video_url="https://example.com", duration=timedelta(seconds=60),
        )
        self.assertTrue(video.is_published)

    def test_news_article_creation(self):
        article = NewsArticle.objects.create(
            title="Big News",
            slug="big-news",
            excerpt="Exciting update",
            content="Full article content here",
            image="news/test.jpg",
            category="announcement",
        )
        self.assertEqual(article.title, "Big News")
        self.assertEqual(str(article), "Big News")

    def test_news_article_defaults(self):
        article = NewsArticle.objects.create(
            title="Test", slug="test-article",
            excerpt="Excerpt", content="Content",
            image="news/t.jpg",
        )
        self.assertTrue(article.is_published)
        self.assertEqual(article.category, "announcement")

    def test_product_creation(self):
        prod = Product.objects.create(
            name="Gaming T-Shirt",
            slug="gaming-tshirt",
            description="Cool shirt",
            image="products/test.jpg",
            price=29.99,
        )
        self.assertEqual(prod.name, "Gaming T-Shirt")
        self.assertTrue(prod.is_available)
        self.assertEqual(str(prod), "Gaming T-Shirt")

    def test_product_negative_price_invalid(self):
        prod = Product(
            name="Bad", slug="bad", image="products/b.jpg",
            price=-10.00,
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()
