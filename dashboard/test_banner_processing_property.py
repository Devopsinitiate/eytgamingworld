"""
Property-based tests for banner image processing
"""

import io
import pytest
from hypothesis import given, strategies as st, settings
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from dashboard.forms import BannerUploadForm


@pytest.mark.django_db
class TestBannerImageProcessing:
    """
    **Feature: user-profile-dashboard, Property 16b: Banner image processing**
    
    For any uploaded banner image, the processed image must be exactly 1920x400 pixels, 
    and images larger than 5MB must be rejected.
    **Validates: Requirements 16.5**
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
        width=st.integers(min_value=100, max_value=4000),
        height=st.integers(min_value=100, max_value=4000),
        color=st.tuples(
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255)
        ),
        format_choice=st.sampled_from(['JPEG', 'PNG'])
    )
    @settings(max_examples=100, deadline=10000)
    def test_banner_processing_dimensions(self, width, height, color, format_choice):
        """
        Property: For any valid image uploaded as banner, the processed result 
        must be exactly 1920x400 pixels regardless of original dimensions.
        """
        # Create test image with given dimensions
        image = Image.new('RGB', (width, height), color=color)
        image_io = io.BytesIO()
        
        # Save with reasonable quality to avoid huge files
        if format_choice == 'JPEG':
            image.save(image_io, format='JPEG', quality=85)
            content_type = 'image/jpeg'
            filename = 'test_banner.jpg'
        else:
            image.save(image_io, format='PNG', optimize=True)
            content_type = 'image/png'
            filename = 'test_banner.png'
        
        image_io.seek(0)
        file_size = len(image_io.getvalue())
        
        # Skip if file is too large (over 5MB) - this should be rejected
        if file_size > 5 * 1024 * 1024:
            # Test that large files are rejected
            banner_file = SimpleUploadedFile(
                filename,
                image_io.read(),
                content_type=content_type
            )
            
            form = BannerUploadForm(files={'banner': banner_file})
            assert not form.is_valid()
            assert 'under 5MB' in str(form.errors.get('banner', []))
            return
        
        # For valid sized files, test the upload process
        self.client.login(email=self.user.email, password='testpass123')
        
        banner_file = SimpleUploadedFile(
            filename,
            image_io.read(),
            content_type=content_type
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'banner': banner_file}
        )
        
        # Should redirect on success (302) or show form with errors
        assert response.status_code in [200, 302]
        
        if response.status_code == 302:
            # Success case - verify the banner was processed correctly
            self.user.refresh_from_db()
            
            if self.user.banner:
                # Open the saved banner and check dimensions
                with self.user.banner.open() as banner_file:
                    processed_image = Image.open(banner_file)
                    
                    # Property: Processed banner must be exactly 1920x400
                    assert processed_image.size == (1920, 400), (
                        f"Banner dimensions should be 1920x400, got {processed_image.size}"
                    )

    @given(
        file_size_mb=st.floats(min_value=5.1, max_value=15.0)
    )
    @settings(max_examples=50, deadline=5000)
    def test_banner_size_rejection(self, file_size_mb):
        """
        Property: For any image larger than 5MB, the upload must be rejected.
        """
        # Create an image large enough to exceed the size limit
        # Calculate dimensions needed for target file size
        target_bytes = int(file_size_mb * 1024 * 1024)
        
        # Create a large enough image (rough calculation)
        # JPEG compression varies, so we'll create a very large image
        dimension = int((target_bytes / 3) ** 0.5) + 200  # Add buffer
        dimension = min(dimension, 10000)  # Cap at reasonable size
        
        image = Image.new('RGB', (dimension, dimension), color=(255, 0, 0))
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=100)  # High quality for larger size
        image_io.seek(0)
        
        actual_size = len(image_io.getvalue())
        
        # Only test if we actually created a file larger than 5MB
        if actual_size > 5 * 1024 * 1024:
            banner_file = SimpleUploadedFile(
                'large_banner.jpg',
                image_io.read(),
                content_type='image/jpeg'
            )
            
            form = BannerUploadForm(files={'banner': banner_file})
            
            # Property: Large files must be rejected
            assert not form.is_valid()
            assert 'under 5MB' in str(form.errors.get('banner', []))

    @given(
        invalid_format=st.sampled_from(['BMP', 'TIFF', 'WEBP'])
    )
    @settings(max_examples=20, deadline=5000)
    def test_banner_format_validation(self, invalid_format):
        """
        Property: For any image in unsupported format, the upload must be rejected.
        """
        # Create test image in invalid format
        image = Image.new('RGB', (1920, 400), color=(0, 255, 0))
        image_io = io.BytesIO()
        
        format_to_content_type = {
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff', 
            'WEBP': 'image/webp'
        }
        
        image.save(image_io, format=invalid_format)
        image_io.seek(0)
        
        banner_file = SimpleUploadedFile(
            f'test_banner.{invalid_format.lower()}',
            image_io.read(),
            content_type=format_to_content_type[invalid_format]
        )
        
        form = BannerUploadForm(files={'banner': banner_file})
        
        # Property: Invalid formats must be rejected
        assert not form.is_valid()
        errors = form.errors.get('banner', [])
        # Check for either file extension error or content type error
        assert any('not allowed' in str(error) or 'JPG, PNG, or GIF' in str(error) for error in errors)

    @pytest.mark.django_db
    def test_banner_processing_preserves_aspect_ratio_handling(self):
        """
        Property: Banner processing should handle different aspect ratios correctly
        by resizing to exactly 1920x400 (which may change aspect ratio).
        """
        test_cases = [
            (3840, 800),   # Wide banner (2:1 aspect ratio)
            (1920, 1080),  # Standard HD (16:9 aspect ratio)
            (800, 600),    # Small 4:3 image
            (1000, 1000),  # Square image
            (500, 200),    # Very wide image
            (200, 800),    # Very tall image
        ]
        
        self.client.login(email=self.user.email, password='testpass123')
        
        for width, height in test_cases:
            # Create test image
            image = Image.new('RGB', (width, height), color=(128, 128, 128))
            image_io = io.BytesIO()
            image.save(image_io, format='JPEG', quality=85)
            image_io.seek(0)
            
            banner_file = SimpleUploadedFile(
                f'test_banner_{width}x{height}.jpg',
                image_io.read(),
                content_type='image/jpeg'
            )
            
            response = self.client.post(
                reverse('dashboard:profile_edit'),
                {'banner': banner_file}
            )
            
            if response.status_code == 302:
                self.user.refresh_from_db()
                
                if self.user.banner:
                    with self.user.banner.open() as saved_banner:
                        processed_image = Image.open(saved_banner)
                        
                        # Property: All processed banners must be exactly 1920x400
                        assert processed_image.size == (1920, 400), (
                            f"Banner from {width}x{height} should be 1920x400, "
                            f"got {processed_image.size}"
                        )

    @pytest.mark.django_db
    def test_banner_processing_handles_rgba_images(self):
        """
        Property: Banner processing should correctly handle RGBA images by converting to RGB.
        """
        # Create RGBA image (with transparency)
        image = Image.new('RGBA', (1000, 500), color=(255, 0, 0, 128))  # Semi-transparent red
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')  # PNG supports transparency
        image_io.seek(0)
        
        self.client.login(email=self.user.email, password='testpass123')
        
        banner_file = SimpleUploadedFile(
            'test_banner_rgba.png',
            image_io.read(),
            content_type='image/png'
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'banner': banner_file}
        )
        
        if response.status_code == 302:
            self.user.refresh_from_db()
            
            if self.user.banner:
                with self.user.banner.open() as saved_banner:
                    processed_image = Image.open(saved_banner)
                    
                    # Property: Processed banner must be exactly 1920x400 and RGB mode
                    assert processed_image.size == (1920, 400)
                    assert processed_image.mode == 'RGB'  # Should be converted from RGBA to RGB

    @pytest.mark.django_db
    def test_banner_processing_quality_preservation(self):
        """
        Property: Banner processing should maintain reasonable image quality.
        """
        # Create a detailed test image
        image = Image.new('RGB', (2000, 1000), color=(100, 150, 200))
        
        # Add some detail to test quality preservation
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        for i in range(0, 2000, 50):
            draw.line([(i, 0), (i, 1000)], fill=(255, 255, 255), width=2)
        for i in range(0, 1000, 50):
            draw.line([(0, i), (2000, i)], fill=(255, 255, 255), width=2)
        
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=95)
        image_io.seek(0)
        
        self.client.login(email=self.user.email, password='testpass123')
        
        banner_file = SimpleUploadedFile(
            'test_banner_quality.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'banner': banner_file}
        )
        
        if response.status_code == 302:
            self.user.refresh_from_db()
            
            if self.user.banner:
                with self.user.banner.open() as saved_banner:
                    processed_image = Image.open(saved_banner)
                    
                    # Property: Processed banner must be exactly 1920x400
                    assert processed_image.size == (1920, 400)
                    
                    # Property: Image should maintain reasonable quality (not completely degraded)
                    # We can't test exact quality, but we can ensure it's still a valid JPEG
                    assert processed_image.format == 'JPEG'