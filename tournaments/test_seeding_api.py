"""
Tests for manual seeding management API endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from core.models import Game
from .models import Tournament, Participant
import json

User = get_user_model()


class SeedingAPITestCase(TestCase):
    """Test case for seeding API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create a game
        self.game = Game.objects.create(
            name='Test Game',
            slug='test-game',
            genre='other'
        )
        
        # Create organizer user
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='testpass123',
            username='organizer'
        )
        self.organizer.role = 'organizer'
        self.organizer.save()
        
        # Create non-organizer user
        self.player = User.objects.create_user(
            email='player@example.com',
            password='testpass123',
            username='player'
        )
        
        # Create tournament with manual seeding
        now = timezone.now()
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            description='A test tournament',
            game=self.game,
            format='single_elim',
            status='registration',
            organizer=self.organizer,
            seeding_method='manual',
            registration_start=now - timezone.timedelta(days=1),
            registration_end=now + timezone.timedelta(days=7),
            check_in_start=now + timezone.timedelta(days=8),
            start_datetime=now + timezone.timedelta(days=9),
        )
        
        # Create participants
        self.participant1 = Participant.objects.create(
            tournament=self.tournament,
            user=self.player,
            status='confirmed'
        )
        
        self.participant2 = Participant.objects.create(
            tournament=self.tournament,
            user=self.organizer,
            status='confirmed'
        )
        
        self.client = Client()
    
    def test_seed_assignment_requires_authentication(self):
        """Test that seed assignment requires authentication"""
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        response = self.client.post(
            url,
            data=json.dumps({'seeds': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_seed_assignment_requires_organizer_permission(self):
        """Test that only organizers can assign seeds"""
        self.client.login(email='player@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        response = self.client.post(
            url,
            data=json.dumps({'seeds': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Permission denied', data['error'])
    
    def test_seed_assignment_rejects_started_tournament(self):
        """Test that seed assignment is rejected for started tournaments"""
        self.tournament.status = 'in_progress'
        self.tournament.save()
        
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        response = self.client.post(
            url,
            data=json.dumps({'seeds': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already started', data['error'])
    
    def test_seed_assignment_requires_manual_seeding_method(self):
        """Test that seed assignment requires manual seeding method"""
        self.tournament.seeding_method = 'random'
        self.tournament.save()
        
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        response = self.client.post(
            url,
            data=json.dumps({'seeds': []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Manual seeding is not enabled', data['error'])
    
    def test_seed_assignment_validates_positive_integers(self):
        """Test that seed values must be positive integers"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        
        # Test negative seed
        response = self.client.post(
            url,
            data=json.dumps({
                'seeds': [
                    {'participant_id': str(self.participant1.id), 'seed': -1}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid seed value', data['error'])
        
        # Test zero seed
        response = self.client.post(
            url,
            data=json.dumps({
                'seeds': [
                    {'participant_id': str(self.participant1.id), 'seed': 0}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_seed_assignment_success(self):
        """Test successful seed assignment"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        
        response = self.client.post(
            url,
            data=json.dumps({
                'seeds': [
                    {'participant_id': str(self.participant1.id), 'seed': 1},
                    {'participant_id': str(self.participant2.id), 'seed': 2}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Seeds updated successfully')
        
        # Verify seeds were updated
        self.participant1.refresh_from_db()
        self.participant2.refresh_from_db()
        self.assertEqual(self.participant1.seed, 1)
        self.assertEqual(self.participant2.seed, 2)
    
    def test_auto_seed_requires_authentication(self):
        """Test that auto-seed requires authentication"""
        url = reverse('tournaments:api_auto_seed', kwargs={'slug': self.tournament.slug})
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 401)
    
    def test_auto_seed_requires_organizer_permission(self):
        """Test that only organizers can auto-seed"""
        self.client.login(email='player@example.com', password='testpass123')
        url = reverse('tournaments:api_auto_seed', kwargs={'slug': self.tournament.slug})
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 403)
    
    def test_auto_seed_assigns_by_registration_order(self):
        """Test that auto-seed assigns seeds by registration order"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_auto_seed', kwargs={'slug': self.tournament.slug})
        
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('2 participants seeded', data['message'])
        
        # Verify seeds were assigned by registration order
        self.participant1.refresh_from_db()
        self.participant2.refresh_from_db()
        
        # participant1 was created first, so should have seed 1
        self.assertEqual(self.participant1.seed, 1)
        self.assertEqual(self.participant2.seed, 2)
    
    def test_seed_assignment_accepts_null_values(self):
        """Test that seed assignment accepts null values"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        
        # First assign a seed
        self.participant1.seed = 5
        self.participant1.save()
        
        # Then set it to null
        response = self.client.post(
            url,
            data=json.dumps({
                'seeds': [
                    {'participant_id': str(self.participant1.id), 'seed': None}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify seed was set to null
        self.participant1.refresh_from_db()
        self.assertIsNone(self.participant1.seed)

    def test_seed_assignment_creates_audit_log(self):
        """Test that seed assignment creates audit log entries"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_seed_participants', kwargs={'slug': self.tournament.slug})
        
        # Clear any existing log entries
        LogEntry.objects.all().delete()
        
        # Assign seeds
        response = self.client.post(
            url,
            data=json.dumps({
                'seeds': [
                    {'participant_id': str(self.participant1.id), 'seed': 1},
                    {'participant_id': str(self.participant2.id), 'seed': 2}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify audit log entries were created
        log_entries = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Participant)
        )
        self.assertEqual(log_entries.count(), 2)
        
        # Verify log entry content
        log1 = log_entries.filter(object_id=str(self.participant1.id)).first()
        self.assertIsNotNone(log1)
        self.assertEqual(log1.user_id, self.organizer.id)
        self.assertIn('Tournament:', log1.change_message)
        self.assertIn('Participant:', log1.change_message)
        self.assertIn('Seed changed from', log1.change_message)
        self.assertIn(self.tournament.name, log1.change_message)
        self.assertIn(self.participant1.display_name, log1.change_message)
    
    def test_auto_seed_creates_audit_log(self):
        """Test that auto-seed creates audit log entries"""
        self.client.login(email='organizer@example.com', password='testpass123')
        url = reverse('tournaments:api_auto_seed', kwargs={'slug': self.tournament.slug})
        
        # Clear any existing log entries
        LogEntry.objects.all().delete()
        
        # Auto-seed
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify audit log entries were created
        log_entries = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Participant)
        )
        self.assertEqual(log_entries.count(), 2)
        
        # Verify log entry content
        log1 = log_entries.filter(object_id=str(self.participant1.id)).first()
        self.assertIsNotNone(log1)
        self.assertEqual(log1.user_id, self.organizer.id)
        self.assertIn('Tournament:', log1.change_message)
        self.assertIn('Participant:', log1.change_message)
        self.assertIn('Auto-seeded', log1.change_message)
        self.assertIn(self.tournament.name, log1.change_message)
        self.assertIn(self.participant1.display_name, log1.change_message)
