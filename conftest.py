"""
Shared pytest fixtures for all EYTGaming test suites.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def player_user(db):
    """Create a standard player user (verified)."""
    return User.objects.create_user(
        email='player@test.com',
        username='testplayer',
        password='testpass123',
        role='player',
        is_verified=True,
    )


@pytest.fixture
def unverified_player_user(db):
    """Create an unverified player user."""
    return User.objects.create_user(
        email='unverified@test.com',
        username='unverifiedplayer',
        password='testpass123',
        role='player',
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        email='admin@test.com',
        password='adminpass123',
    )


@pytest.fixture
def organizer_user(db):
    """Create an organizer user."""
    return User.objects.create_user(
        email='organizer@test.com',
        username='testorganizer',
        password='testpass123',
        role='organizer',
    )


@pytest.fixture
def coach_user(db):
    """Create a coach user."""
    return User.objects.create_user(
        email='coach@test.com',
        username='testcoach',
        password='testpass123',
        role='coach',
    )


@pytest.fixture
def client_logged_in_player(client, player_user):
    """Return an authenticated client for a player user."""
    client.force_login(player_user)
    return client


@pytest.fixture
def client_logged_in_admin(client, admin_user):
    """Return an authenticated client for an admin user."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def client_logged_in_organizer(client, organizer_user):
    """Return an authenticated client for an organizer user."""
    client.force_login(organizer_user)
    return client
