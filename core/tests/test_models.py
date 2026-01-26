# core/tests/test_models.py
"""Basic unit tests for core app models.
These tests verify that the core data models can be instantiated and saved correctly.
They serve as a foundation for increasing test coverage in the short‑term sprint.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Game, UserGameProfile, SiteSettings

User = get_user_model()


class CoreModelsTestCase(TestCase):
    def setUp(self):
        # Create a sample user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        # Create a game entry
        self.game = Game.objects.create(name="League of Legends", slug="lol")

    def test_user_creation(self):
        """User model should store basic fields correctly."""
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertFalse(self.user.is_staff)

    def test_game_creation(self):
        """Game model should be creatable and retrievable."""
        game = Game.objects.get(slug="lol")
        self.assertEqual(game.name, "League of Legends")

    def test_user_game_profile_creation(self):
        """UserGameProfile links a user to a game with stats."""
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

    def test_site_settings_singleton(self):
        """SiteSettings should behave as a singleton model."""
        settings1 = SiteSettings.objects.create(site_name="EYTGaming")
        # Verify singleton behavior by loading the existing instance
        settings2 = SiteSettings.load()
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(settings2.site_name, "EYTGaming")
        self.assertEqual(settings2.site_name, "EYTGaming")
