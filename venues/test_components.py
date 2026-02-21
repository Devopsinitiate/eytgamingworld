"""
Tests for Venue component templates
"""
from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from .models import Venue, VenueReview

User = get_user_model()


class ReviewCardComponentTests(TestCase):
    """
    Test review_card.html component rendering.
    
    Validates:
    - Requirements 6.2: Display rating, title, review text, author, and date
    - Requirements 6.3: Display would_recommend indicator
    - Task 8.7: Gaming design with gunmetal background and neon cyan badge
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='Test venue description',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
        
        self.review = VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=5,
            title='Amazing venue!',
            review='This is a great gaming venue with excellent facilities.',
            would_recommend=True
        )
    
    def test_review_card_renders_all_required_fields(self):
        """Test that review card displays all required information"""
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check that all required fields are present
        self.assertIn('Amazing venue!', rendered)  # Title
        self.assertIn('This is a great gaming venue', rendered)  # Review text
        self.assertIn('testuser', rendered)  # Author name (username since display_name not set)
        self.assertIn('review-card', rendered)  # Component class
        
    def test_review_card_displays_star_rating(self):
        """Test that review card displays correct star rating"""
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check for star icons
        self.assertIn('material-symbols-outlined', rendered)
        self.assertIn('star', rendered)
        self.assertIn('text-electric-red', rendered)  # Filled stars
        
    def test_review_card_displays_recommend_badge(self):
        """Test that review card displays recommendation badge when would_recommend is True"""
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check for recommendation badge
        self.assertIn('recommend-badge', rendered)
        self.assertIn('Recommends', rendered)
        self.assertIn('thumb_up', rendered)
        
    def test_review_card_hides_recommend_badge_when_false(self):
        """Test that review card hides recommendation badge when would_recommend is False"""
        self.review.would_recommend = False
        self.review.save()
        
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check that recommendation badge is not present
        self.assertNotIn('recommend-badge', rendered)
        self.assertNotIn('Recommends', rendered)
        
    def test_review_card_displays_date(self):
        """Test that review card displays the review date"""
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check that date is formatted and displayed
        date_str = self.review.created_at.strftime("%b %d, %Y")
        self.assertIn(date_str, rendered)
        
    def test_review_card_applies_gaming_design(self):
        """Test that review card applies gaming design classes"""
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Check for gaming design classes
        self.assertIn('review-card', rendered)  # Gunmetal background
        self.assertIn('font-barlow', rendered)  # Gaming font
        self.assertIn('font-inter', rendered)  # Body font
        self.assertIn('star-glow', rendered)  # Star glow effect
        
    def test_review_card_with_low_rating(self):
        """Test that review card correctly displays low ratings"""
        self.review.rating = 2
        self.review.save()
        
        template = Template(
            "{% load static %}"
            "{% include 'venues/components/review_card.html' with review=review %}"
        )
        context = Context({'review': self.review})
        rendered = template.render(context)
        
        # Should have both filled and empty stars
        self.assertIn('text-electric-red', rendered)  # Filled stars
        self.assertIn('text-gray-600', rendered)  # Empty stars
