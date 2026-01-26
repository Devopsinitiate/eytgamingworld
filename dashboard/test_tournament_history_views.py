"""
Tests for tournament history views.

**Validates: Requirements 5.1, 5.2, 5.3, 5.5**
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import User, Game
from tournaments.models import Tournament, Participant, Match, Bracket
from teams.models import Team


@pytest.mark.django_db
class TestTournamentHistoryView:
    """Test tournament_history view."""
    
    def test_tournament_history_view_requires_login(self, client):
        """Test that tournament history view requires authentication."""
        url = reverse('dashboard:tournament_history')
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login
        assert '/accounts/login/' in response.url
    
    def test_tournament_history_view_displays_participations(self, client, django_user_model):
        """Test that tournament history view displays user's tournament participations."""
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')
        
        # Create game
        game = Game.objects.create(
            name='Test Game',
            slug='test-game',
            description='Test game description'
        )
        
        # Create tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=game,
            organizer=user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status='registration'
        )
        
        # Create participation
        participation = Participant.objects.create(
            tournament=tournament,
            user=user,
            status='confirmed',
            final_placement=1,
            prize_won=100.00
        )
        
        # Get tournament history
        url = reverse('dashboard:tournament_history')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'participations' in response.context
        assert 'total_tournaments' in response.context
        assert response.context['total_tournaments'] == 1
        assert tournament.name in response.content.decode()
    
    def test_tournament_history_filtering_by_game(self, client, django_user_model):
        """Test filtering tournament history by game."""
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')
        
        # Create games
        game1 = Game.objects.create(name='Game 1', slug='game-1', description='Game 1')
        game2 = Game.objects.create(name='Game 2', slug='game-2', description='Game 2')
        
        # Create tournaments
        tournament1 = Tournament.objects.create(
            name='Tournament 1',
            slug='tournament-1',
            game=game1,
            organizer=user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status='registration'
        )
        
        tournament2 = Tournament.objects.create(
            name='Tournament 2',
            slug='tournament-2',
            game=game2,
            organizer=user,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=2),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status='registration'
        )
        
        # Create participations
        Participant.objects.create(tournament=tournament1, user=user, status='confirmed')
        Participant.objects.create(tournament=tournament2, user=user, status='confirmed')
        
        # Filter by game1
        url = reverse('dashboard:tournament_history')
        response = client.get(url, {'game': str(game1.id)})
        
        assert response.status_code == 200
        assert len(response.context['participations']) == 1
        assert response.context['participations'][0].tournament.game == game1
    
    def test_tournament_history_pagination(self, client, django_user_model):
        """Test that tournament history implements pagination (20 per page)."""
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')
        
        # Create game
        game = Game.objects.create(name='Test Game', slug='test-game', description='Test')
        
        # Create 25 tournaments
        for i in range(25):
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{i}',
                game=game,
                organizer=user,
                format='single_elimination',
                max_participants=16,
                start_datetime=timezone.now() + timedelta(days=i),
                registration_deadline=timezone.now() + timedelta(hours=12),
                status='registration'
            )
            Participant.objects.create(tournament=tournament, user=user, status='confirmed')
        
        # Get first page
        url = reverse('dashboard:tournament_history')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'page_obj' in response.context
        assert len(response.context['participations']) == 20  # First page has 20 items
        assert response.context['page_obj'].has_next()
        
        # Get second page
        response = client.get(url, {'page': 2})
        assert response.status_code == 200
        assert len(response.context['participations']) == 5  # Second page has remaining 5 items


@pytest.mark.django_db
class TestTournamentDetailHistoryView:
    """Test tournament_detail_history view."""
    
    def test_tournament_detail_history_requires_login(self, client):
        """Test that tournament detail history view requires authentication."""
        # Create a dummy UUID for testing
        import uuid
        tournament_id = uuid.uuid4()
        url = reverse('dashboard:tournament_detail_history', args=[tournament_id])
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login
        assert '/accounts/login/' in response.url
    
    def test_tournament_detail_history_displays_matches(self, client, django_user_model):
        """Test that tournament detail history displays match details."""
        # Create users
        user1 = django_user_model.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = django_user_model.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        client.login(username='user1', password='testpass123')
        
        # Create game
        game = Game.objects.create(name='Test Game', slug='test-game', description='Test')
        
        # Create tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=game,
            organizer=user1,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status='in_progress'
        )
        
        # Create participations
        participant1 = Participant.objects.create(
            tournament=tournament,
            user=user1,
            status='confirmed'
        )
        participant2 = Participant.objects.create(
            tournament=tournament,
            user=user2,
            status='confirmed'
        )
        
        # Create bracket
        bracket = Bracket.objects.create(
            tournament=tournament,
            name='Main Bracket',
            bracket_type='single_elimination'
        )
        
        # Create match
        match = Match.objects.create(
            tournament=tournament,
            bracket=bracket,
            participant1=participant1,
            participant2=participant2,
            round_number=1,
            match_number=1,
            score_p1=2,
            score_p2=1,
            winner=participant1,
            status='completed',
            started_at=timezone.now(),
            completed_at=timezone.now()
        )
        
        # Get tournament detail history
        url = reverse('dashboard:tournament_detail_history', args=[tournament.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'tournament' in response.context
        assert 'participation' in response.context
        assert 'match_details' in response.context
        assert response.context['total_matches'] == 1
        assert response.context['matches_won'] == 1
        assert response.context['matches_lost'] == 0
    
    def test_tournament_detail_history_non_participant_redirect(self, client, django_user_model):
        """Test that non-participants are redirected with error message."""
        # Create users
        user1 = django_user_model.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = django_user_model.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Login as user2 (non-participant)
        client.login(username='user2', password='testpass123')
        
        # Create game
        game = Game.objects.create(name='Test Game', slug='test-game', description='Test')
        
        # Create tournament
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            game=game,
            organizer=user1,
            format='single_elimination',
            max_participants=16,
            start_datetime=timezone.now() + timedelta(days=1),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status='registration'
        )
        
        # Create participation for user1 only
        Participant.objects.create(
            tournament=tournament,
            user=user1,
            status='confirmed'
        )
        
        # Try to access as user2 (non-participant)
        url = reverse('dashboard:tournament_detail_history', args=[tournament.id])
        response = client.get(url)
        
        # Should redirect to tournament history with error message
        assert response.status_code == 302
        assert response.url == reverse('dashboard:tournament_history')
