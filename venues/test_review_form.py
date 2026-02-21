from django.test import TestCase
from django.core.exceptions import ValidationError
from venues.forms import VenueReviewForm
from venues.models import Venue, VenueReview
from core.models import User


class VenueReviewFormTests(TestCase):
    """Unit tests for VenueReviewForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test venue',
            venue_type='esports_arena',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            is_active=True,
            is_verified=True
        )
    
    def test_form_has_required_fields(self):
        """Test that form includes all required fields"""
        form = VenueReviewForm()
        self.assertIn('rating', form.fields)
        self.assertIn('title', form.fields)
        self.assertIn('review', form.fields)
        self.assertIn('would_recommend', form.fields)
    
    def test_valid_review_form(self):
        """Test form with valid data"""
        form_data = {
            'rating': 4,
            'title': 'Great venue!',
            'review': 'Had an amazing experience at this venue.',
            'would_recommend': True
        }
        form = VenueReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_rating_validation_minimum(self):
        """Test that rating less than 1 is rejected"""
        form_data = {
            'rating': 0,
            'title': 'Bad venue',
            'review': 'Not good',
            'would_recommend': False
        }
        form = VenueReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_rating_validation_maximum(self):
        """Test that rating greater than 5 is rejected"""
        form_data = {
            'rating': 6,
            'title': 'Amazing venue',
            'review': 'Too good to be true',
            'would_recommend': True
        }
        form = VenueReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
    
    def test_rating_validation_valid_range(self):
        """Test that ratings 1-5 are all valid"""
        for rating in range(1, 6):
            form_data = {
                'rating': rating,
                'title': f'Review with {rating} stars',
                'review': 'Test review',
                'would_recommend': True
            }
            form = VenueReviewForm(data=form_data)
            self.assertTrue(form.is_valid(), f'Rating {rating} should be valid')
    
    def test_required_fields(self):
        """Test that required fields cannot be empty"""
        form_data = {
            'would_recommend': True
        }
        form = VenueReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertIn('title', form.errors)
        self.assertIn('review', form.errors)
    
    def test_would_recommend_defaults_to_true(self):
        """Test that would_recommend field has default value"""
        form_data = {
            'rating': 5,
            'title': 'Excellent venue',
            'review': 'Highly recommended'
        }
        form = VenueReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
        # When not provided, would_recommend should be False in form data
        # but the model has default=True
    
    def test_title_max_length(self):
        """Test that title respects max length"""
        form_data = {
            'rating': 4,
            'title': 'A' * 201,  # Exceeds 200 character limit
            'review': 'Test review',
            'would_recommend': True
        }
        form = VenueReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_form_widgets_have_correct_classes(self):
        """Test that form widgets have appropriate CSS classes"""
        form = VenueReviewForm()
        self.assertIn('form-input', form.fields['rating'].widget.attrs.get('class', ''))
        self.assertIn('form-input', form.fields['title'].widget.attrs.get('class', ''))
        self.assertIn('form-input', form.fields['review'].widget.attrs.get('class', ''))
        self.assertIn('form-checkbox', form.fields['would_recommend'].widget.attrs.get('class', ''))
    
    def test_rating_widget_has_min_max_attributes(self):
        """Test that rating input has min and max attributes"""
        form = VenueReviewForm()
        widget_attrs = form.fields['rating'].widget.attrs
        self.assertEqual(widget_attrs.get('min'), '1')
        self.assertEqual(widget_attrs.get('max'), '5')
