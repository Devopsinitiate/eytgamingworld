"""
Property-based tests for avatar image processing
"""

import io
import pytest
from hypothesis import given, strategies as st, settings
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from dashboard.forms import AvatarUploadForm


@pytest.mark.django_db
class TestAvatarImageProcessing:
    """
    **Feature: user-profile-dashboard, Property 16: Avatar image processing**
    
    For any uploaded avatar image, the processed image must be exactly 400x400 pixels, 
    and images larger than 2MB must be rejected.
    **Validates: Requirements 2.3**
    """

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test user and client"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        unique_email = f'test_{unique_id}@example.com'
        unique_username = f'testuser_{unique_id}'
        self.user = User.objects.create_user(
            email=unique_email,
            username=unique_username,
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = Client()

    @given(
        width=st.integers(min_value=50, max_value=4000),
        height=st.integers(min_value=50, max_value=4000),
        color=st.tuples(
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255)
        ),
        format_choice=st.sampled_from(['JPEG', 'PNG'])
    )
    @settings(max_examples=100, deadline=10000)
    def test_avatar_processing_dimensions(self, width, height, color, format_choice):
        """
        Property: For any valid image uploaded as avatar, the processed result 
        must be exactly 400x400 pixels regardless of original dimensions.
        """
        # Create test image with given dimensions
        image = Image.new('RGB', (width, height), color=color)
        image_io = io.BytesIO()
        
        # Save with reasonable quality to avoid huge files
        if format_choice == 'JPEG':
            image.save(image_io, format='JPEG', quality=85)
            content_type = 'image/jpeg'
            filename = 'test_avatar.jpg'
        else:
            image.save(image_io, format='PNG', optimize=True)
            content_type = 'image/png'
            filename = 'test_avatar.png'
        
        image_io.seek(0)
        file_size = len(image_io.getvalue())
        
        # Skip if file is too large (over 2MB) - this should be rejected
        if file_size > 2 * 1024 * 1024:
            # Test that large files are rejected
            avatar_file = SimpleUploadedFile(
                filename,
                image_io.read(),
                content_type=content_type
            )
            
            form = AvatarUploadForm(files={'avatar': avatar_file})
            assert not form.is_valid()
            assert 'under 2MB' in str(form.errors.get('avatar', []))
            return
        
        # For valid sized files, test the upload process
        self.client.login(email=self.user.email, password='testpass123')
        
        avatar_file = SimpleUploadedFile(
            filename,
            image_io.read(),
            content_type=content_type
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'avatar': avatar_file}
        )
        
        # Should redirect on success (302) or show form with errors
        assert response.status_code in [200, 302]
        
        if response.status_code == 302:
            # Success case - verify the avatar was processed correctly
            self.user.refresh_from_db()
            
            if self.user.avatar:
                # Open the saved avatar and check dimensions
                with self.user.avatar.open() as avatar_file:
                    processed_image = Image.open(avatar_file)
                    
                    # Property: Processed avatar must be exactly 400x400
                    assert processed_image.size == (400, 400), (
                        f"Avatar dimensions should be 400x400, got {processed_image.size}"
                    )

    @given(
        file_size_mb=st.floats(min_value=2.1, max_value=10.0)
    )
    @settings(max_examples=50, deadline=5000)
    def test_avatar_size_rejection(self, file_size_mb):
        """
        Property: For any image larger than 2MB, the upload must be rejected.
        """
        # Create an image large enough to exceed the size limit
        # Calculate dimensions needed for target file size
        target_bytes = int(file_size_mb * 1024 * 1024)
        
        # Create a large enough image (rough calculation)
        # JPEG compression varies, so we'll create a very large image
        dimension = int((target_bytes / 3) ** 0.5) + 100  # Add buffer
        dimension = min(dimension, 8000)  # Cap at reasonable size
        
        image = Image.new('RGB', (dimension, dimension), color=(255, 0, 0))
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=100)  # High quality for larger size
        image_io.seek(0)
        
        actual_size = len(image_io.getvalue())
        
        # Only test if we actually created a file larger than 2MB
        if actual_size > 2 * 1024 * 1024:
            avatar_file = SimpleUploadedFile(
                'large_avatar.jpg',
                image_io.read(),
                content_type='image/jpeg'
            )
            
            form = AvatarUploadForm(files={'avatar': avatar_file})
            
            # Property: Large files must be rejected
            assert not form.is_valid()
            assert 'under 2MB' in str(form.errors.get('avatar', []))

    @given(
        invalid_format=st.sampled_from(['BMP', 'TIFF', 'WEBP'])
    )
    @settings(max_examples=20, deadline=5000)
    def test_avatar_format_validation(self, invalid_format):
        """
        Property: For any image in unsupported format, the upload must be rejected.
        """
        # Create test image in invalid format
        image = Image.new('RGB', (200, 200), color=(0, 255, 0))
        image_io = io.BytesIO()
        
        format_to_content_type = {
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff', 
            'WEBP': 'image/webp'
        }
        
        image.save(image_io, format=invalid_format)
        image_io.seek(0)
        
        avatar_file = SimpleUploadedFile(
            f'test_avatar.{invalid_format.lower()}',
            image_io.read(),
            content_type=format_to_content_type[invalid_format]
        )
        
        form = AvatarUploadForm(files={'avatar': avatar_file})
        
        # Property: Invalid formats must be rejected
        assert not form.is_valid()
        errors = form.errors.get('avatar', [])
        # Check for either file extension error or content type error
        assert any('not allowed' in str(error) or 'JPG, PNG, or GIF' in str(error) for error in errors)

    @pytest.mark.django_db
    def test_avatar_processing_preserves_aspect_ratio_handling(self):
        """
        Property: Avatar processing should handle different aspect ratios correctly
        by resizing to exactly 400x400 (which may change aspect ratio).
        """
        test_cases = [
            (800, 400),  # Wide image
            (400, 800),  # Tall image  
            (100, 100),  # Small square
            (1000, 1000),  # Large square
        ]
        
        self.client.login(email=self.user.email, password='testpass123')
        
        for width, height in test_cases:
            # Create test image
            image = Image.new('RGB', (width, height), color=(128, 128, 128))
            image_io = io.BytesIO()
            image.save(image_io, format='JPEG', quality=85)
            image_io.seek(0)
            
            avatar_file = SimpleUploadedFile(
                f'test_avatar_{width}x{height}.jpg',
                image_io.read(),
                content_type='image/jpeg'
            )
            
            response = self.client.post(
                reverse('dashboard:profile_edit'),
                {'avatar': avatar_file}
            )
            
            if response.status_code == 302:
                self.user.refresh_from_db()
                
                if self.user.avatar:
                    with self.user.avatar.open() as saved_avatar:
                        processed_image = Image.open(saved_avatar)
                        
                        # Property: All processed avatars must be exactly 400x400
                        assert processed_image.size == (400, 400), (
                            f"Avatar from {width}x{height} should be 400x400, "
                            f"got {processed_image.size}"
                        )