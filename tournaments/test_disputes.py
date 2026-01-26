"""
Unit Tests for Match Dispute Functionality

Feature: tournament-system
Tests dispute creation, evidence upload, and admin resolution.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

from core.models import User, Game
from tournaments.models import Tournament, Participant, Match, Bracket, MatchDispute


class MatchDisputeTests(TestCase):
    """Unit tests for match dispute filing"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create game
        self.game = Game.objects.create(
            name="Test Game",
            slug="test-game",
            genre='fps'
        )
        
        # Create organizer
        self.organizer = User.objects.create(
            email="organizer@test.com",
            username="organizer",
            role='organizer'
        )
        
        # Create tournament
        now = timezone.now()
        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            slug="test-tournament",
            description="Test Description",
            game=self.game,
            format='single_elim',
            status='in_progress',
            organizer=self.organizer,
            max_participants=16,
            min_participants=4,
            registration_start=now - timedelta(days=10),
            registration_end=now - timedelta(days=5),
            check_in_start=now - timedelta(days=4),
            start_datetime=now - timedelta(days=3),
            is_public=True
        )
        
        # Create bracket
        self.bracket = Bracket.objects.create(
            tournament=self.tournament,
            bracket_type='main',
            name='Main Bracket',
            total_rounds=2,
            current_round=1
        )
        
        # Create participants
        self.user1 = User.objects.create(
            email="participant1@test.com",
            username="participant1"
        )
        self.participant1 = Participant.objects.create(
            tournament=self.tournament,
            user=self.user1,
            status='confirmed',
            checked_in=True
        )
        
        self.user2 = User.objects.create(
            email="participant2@test.com",
            username="participant2"
        )
        self.participant2 = Participant.objects.create(
            tournament=self.tournament,
            user=self.user2,
            status='confirmed',
            checked_in=True
        )
        
        # Create match
        self.match = Match.objects.create(
            tournament=self.tournament,
            bracket=self.bracket,
            round_number=1,
            match_number=1,
            participant1=self.participant1,
            participant2=self.participant2,
            status='completed',
            score_p1=2,
            score_p2=1,
            winner=self.participant1
        )
    
    def test_dispute_creation(self):
        """Test that a dispute can be created successfully"""
        # Log in as participant
        self.client.force_login(self.user1)
        
        # File dispute
        response = self.client.post(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk}),
            {
                'reason': 'The opponent was cheating during the match.',
            }
        )
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Check dispute was created
        dispute = MatchDispute.objects.filter(match=self.match).first()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute.reporter, self.user1)
        self.assertEqual(dispute.reason, 'The opponent was cheating during the match.')
        self.assertEqual(dispute.status, 'open')
    
    def test_dispute_with_evidence_upload(self):
        """Test dispute creation with evidence file upload"""
        # Log in as participant
        self.client.force_login(self.user2)
        
        # Create a fake file
        evidence_file = SimpleUploadedFile(
            "evidence.txt",
            b"This is evidence content",
            content_type="text/plain"
        )
        
        # File dispute with evidence
        response = self.client.post(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk}),
            {
                'reason': 'Score was recorded incorrectly.',
                'evidence': evidence_file
            }
        )
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Check dispute was created with evidence
        dispute = MatchDispute.objects.filter(match=self.match).first()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute.reporter, self.user2)
        self.assertTrue(dispute.evidence)
    
    def test_dispute_requires_reason(self):
        """Test that dispute filing requires a reason"""
        # Log in as participant
        self.client.force_login(self.user1)
        
        # Try to file dispute without reason
        response = self.client.post(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk}),
            {
                'reason': '',  # Empty reason
            }
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check no dispute was created
        dispute_count = MatchDispute.objects.filter(match=self.match).count()
        self.assertEqual(dispute_count, 0)
    
    def test_dispute_form_display(self):
        """Test that the dispute form displays correctly"""
        # Log in as participant
        self.client.force_login(self.user1)
        
        # Get dispute form
        response = self.client.get(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk})
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'File Match Dispute')
        self.assertContains(response, self.match.participant1.display_name)
        self.assertContains(response, self.match.participant2.display_name)
        self.assertContains(response, 'Reason for Dispute')
    
    def test_admin_can_resolve_dispute(self):
        """Test that admin can resolve a dispute"""
        # Create admin user
        admin = User.objects.create(
            email="admin@test.com",
            username="admin",
            role='admin'
        )
        
        # Create a dispute
        dispute = MatchDispute.objects.create(
            match=self.match,
            reporter=self.user1,
            reason='Test dispute',
            status='open'
        )
        
        # Admin resolves dispute
        dispute.status = 'resolved'
        dispute.resolved_by = admin
        dispute.resolution = 'Dispute reviewed and resolved in favor of participant 1'
        dispute.resolved_at = timezone.now()
        dispute.save()
        
        # Check dispute was resolved
        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'resolved')
        self.assertEqual(dispute.resolved_by, admin)
        self.assertIsNotNone(dispute.resolution)
        self.assertIsNotNone(dispute.resolved_at)
    
    def test_multiple_disputes_for_same_match(self):
        """Test that multiple users can file disputes for the same match"""
        # User 1 files dispute
        self.client.force_login(self.user1)
        self.client.post(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk}),
            {'reason': 'Dispute from user 1'}
        )
        
        # User 2 files dispute
        self.client.force_login(self.user2)
        self.client.post(
            reverse('tournaments:match_dispute', kwargs={'pk': self.match.pk}),
            {'reason': 'Dispute from user 2'}
        )
        
        # Check both disputes exist
        dispute_count = MatchDispute.objects.filter(match=self.match).count()
        self.assertEqual(dispute_count, 2)
        
        # Check reporters are different
        disputes = MatchDispute.objects.filter(match=self.match)
        reporters = [d.reporter for d in disputes]
        self.assertIn(self.user1, reporters)
        self.assertIn(self.user2, reporters)
    
    def test_dispute_admin_notes(self):
        """Test that admin can add notes to a dispute"""
        # Create a dispute
        dispute = MatchDispute.objects.create(
            match=self.match,
            reporter=self.user1,
            reason='Test dispute',
            status='investigating'
        )
        
        # Admin adds notes
        dispute.admin_notes = 'Reviewed evidence. Need more information from both parties.'
        dispute.save()
        
        # Check notes were saved
        dispute.refresh_from_db()
        self.assertEqual(
            dispute.admin_notes,
            'Reviewed evidence. Need more information from both parties.'
        )
    
    def test_dispute_dismissal(self):
        """Test that admin can dismiss a dispute"""
        # Create admin user
        admin = User.objects.create(
            email="admin@test.com",
            username="admin",
            role='admin'
        )
        
        # Create a dispute
        dispute = MatchDispute.objects.create(
            match=self.match,
            reporter=self.user1,
            reason='Frivolous dispute',
            status='open'
        )
        
        # Admin dismisses dispute
        dispute.status = 'dismissed'
        dispute.resolved_by = admin
        dispute.resolution = 'Dispute dismissed - no evidence of wrongdoing'
        dispute.resolved_at = timezone.now()
        dispute.save()
        
        # Check dispute was dismissed
        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'dismissed')
        self.assertIsNotNone(dispute.resolution)
