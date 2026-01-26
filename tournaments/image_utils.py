"""
Image optimization utilities for tournament media.
Provides WebP format support and responsive image generation.
"""

import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """
    Handles image optimization and format conversion for tournament media.
    Supports WebP format with fallbacks and responsive image generation.
    """
    
    # Image quality settings
    WEBP_QUALITY = 85
    JPEG_QUALITY = 90
    
    # Responsive image sizes
    RESPONSIVE_SIZES = {
        'thumbnail': (300, 200),
        'small': (600, 400),
        'medium': (1200, 800),
        'large': (1920, 1280),
        'hero': (2560, 1440)
    }
    
    @classmethod
    def optimize_tournament_image(cls, image_file, image_type='banner'):
        """
        Optimize tournament image and generate multiple formats and sizes.
        
        Args:
            image_file: Django UploadedFile object
            image_type: Type of image ('banner', 'thumbnail', 'social')
        
        Returns:
            dict: Dictionary with optimized image paths
        """
        try:
            # Open and process the image
            with Image.open(image_file) as img:
                # Convert to RGB if necessary (for WebP compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Auto-orient based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Generate optimized versions
                optimized_images = {}
                
                # Generate different sizes based on image type
                if image_type == 'banner':
                    sizes_to_generate = ['thumbnail', 'small', 'medium', 'large', 'hero']
                elif image_type == 'thumbnail':
                    sizes_to_generate = ['thumbnail', 'small']
                elif image_type == 'social':
                    sizes_to_generate = ['medium', 'large']
                else:
                    sizes_to_generate = ['small', 'medium']
                
                for size_name in sizes_to_generate:
                    if size_name in cls.RESPONSIVE_SIZES:
                        target_size = cls.RESPONSIVE_SIZES[size_name]
                        
                        # Generate WebP version
                        webp_path = cls._generate_webp_image(img, target_size, image_file.name, size_name)
                        if webp_path:
                            optimized_images[f'{size_name}_webp'] = webp_path
                        
                        # Generate JPEG fallback
                        jpeg_path = cls._generate_jpeg_image(img, target_size, image_file.name, size_name)
                        if jpeg_path:
                            optimized_images[f'{size_name}_jpeg'] = jpeg_path
                
                return optimized_images
                
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return {}
    
    @classmethod
    def _generate_webp_image(cls, img, target_size, original_name, size_name):
        """Generate WebP format image"""
        try:
            # Resize image maintaining aspect ratio
            img_resized = cls._resize_image(img, target_size)
            
            # Generate filename
            base_name = os.path.splitext(original_name)[0]
            webp_filename = f"{base_name}_{size_name}.webp"
            
            # Convert to WebP
            webp_buffer = BytesIO()
            img_resized.save(
                webp_buffer,
                format='WEBP',
                quality=cls.WEBP_QUALITY,
                optimize=True
            )
            webp_buffer.seek(0)
            
            # Save to storage
            webp_file = ContentFile(webp_buffer.getvalue(), name=webp_filename)
            webp_path = default_storage.save(f"tournaments/optimized/{webp_filename}", webp_file)
            
            return webp_path
            
        except Exception as e:
            logger.warning(f"WebP generation failed for {size_name}: {e}")
            return None
    
    @classmethod
    def _generate_jpeg_image(cls, img, target_size, original_name, size_name):
        """Generate JPEG format image as fallback"""
        try:
            # Resize image maintaining aspect ratio
            img_resized = cls._resize_image(img, target_size)
            
            # Generate filename
            base_name = os.path.splitext(original_name)[0]
            jpeg_filename = f"{base_name}_{size_name}.jpg"
            
            # Convert to JPEG
            jpeg_buffer = BytesIO()
            img_resized.save(
                jpeg_buffer,
                format='JPEG',
                quality=cls.JPEG_QUALITY,
                optimize=True
            )
            jpeg_buffer.seek(0)
            
            # Save to storage
            jpeg_file = ContentFile(jpeg_buffer.getvalue(), name=jpeg_filename)
            jpeg_path = default_storage.save(f"tournaments/optimized/{jpeg_filename}", jpeg_file)
            
            return jpeg_path
            
        except Exception as e:
            logger.warning(f"JPEG generation failed for {size_name}: {e}")
            return None
    
    @classmethod
    def _resize_image(cls, img, target_size):
        """Resize image maintaining aspect ratio"""
        # Calculate the aspect ratio
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            # Image is wider than target ratio
            new_width = target_size[0]
            new_height = int(target_size[0] / img_ratio)
        else:
            # Image is taller than target ratio
            new_height = target_size[1]
            new_width = int(target_size[1] * img_ratio)
        
        # Resize the image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # If the resized image is smaller than target, pad it
        if new_width < target_size[0] or new_height < target_size[1]:
            # Create a new image with target size and paste the resized image
            padded_img = Image.new('RGB', target_size, (255, 255, 255))
            paste_x = (target_size[0] - new_width) // 2
            paste_y = (target_size[1] - new_height) // 2
            padded_img.paste(img_resized, (paste_x, paste_y))
            return padded_img
        
        return img_resized
    
    @classmethod
    def generate_responsive_image_html(cls, image_paths, alt_text="", css_class=""):
        """
        Generate HTML for responsive images with WebP support and fallbacks.
        
        Args:
            image_paths: Dictionary of image paths from optimize_tournament_image
            alt_text: Alt text for accessibility
            css_class: CSS classes to apply
        
        Returns:
            str: HTML picture element with sources
        """
        if not image_paths:
            return ""
        
        html_parts = [f'<picture class="{css_class}">']
        
        # Add WebP sources for different screen sizes
        webp_sources = []
        jpeg_sources = []
        
        # Collect available sizes
        for key, path in image_paths.items():
            if key.endswith('_webp'):
                size_name = key.replace('_webp', '')
                webp_sources.append((size_name, path))
            elif key.endswith('_jpeg'):
                size_name = key.replace('_jpeg', '')
                jpeg_sources.append((size_name, path))
        
        # Sort by size (largest first for media queries)
        size_order = ['hero', 'large', 'medium', 'small', 'thumbnail']
        webp_sources.sort(key=lambda x: size_order.index(x[0]) if x[0] in size_order else 999)
        jpeg_sources.sort(key=lambda x: size_order.index(x[0]) if x[0] in size_order else 999)
        
        # Generate WebP sources with media queries
        for size_name, path in webp_sources:
            media_query = cls._get_media_query_for_size(size_name)
            if media_query:
                html_parts.append(f'  <source media="{media_query}" srcset="{settings.MEDIA_URL}{path}" type="image/webp">')
            else:
                html_parts.append(f'  <source srcset="{settings.MEDIA_URL}{path}" type="image/webp">')
        
        # Generate JPEG sources with media queries
        for size_name, path in jpeg_sources:
            media_query = cls._get_media_query_for_size(size_name)
            if media_query:
                html_parts.append(f'  <source media="{media_query}" srcset="{settings.MEDIA_URL}{path}" type="image/jpeg">')
        
        # Fallback img tag (use medium or small JPEG)
        fallback_path = None
        for size_name in ['medium', 'small', 'thumbnail']:
            fallback_key = f'{size_name}_jpeg'
            if fallback_key in image_paths:
                fallback_path = image_paths[fallback_key]
                break
        
        if fallback_path:
            html_parts.append(f'  <img src="{settings.MEDIA_URL}{fallback_path}" alt="{alt_text}" loading="lazy">')
        
        html_parts.append('</picture>')
        
        return '\n'.join(html_parts)
    
    @classmethod
    def _get_media_query_for_size(cls, size_name):
        """Get appropriate media query for image size"""
        media_queries = {
            'hero': '(min-width: 1920px)',
            'large': '(min-width: 1200px)',
            'medium': '(min-width: 768px)',
            'small': '(min-width: 480px)',
            'thumbnail': None  # Default, no media query
        }
        return media_queries.get(size_name)
    
    @classmethod
    def cleanup_old_images(cls, image_paths_to_keep):
        """
        Clean up old optimized images that are no longer needed.
        
        Args:
            image_paths_to_keep: List of image paths that should be preserved
        """
        try:
            # This would implement cleanup logic for old optimized images
            # For now, we'll just log the intent
            logger.info(f"Would clean up old images, keeping: {len(image_paths_to_keep)} files")
        except Exception as e:
            logger.error(f"Image cleanup failed: {e}")


def optimize_tournament_banner(sender, instance, **kwargs):
    """
    Signal handler to automatically optimize tournament banners on save.
    """
    if instance.banner and hasattr(instance.banner, 'file'):
        try:
            # Generate optimized versions
            optimized_images = ImageOptimizer.optimize_tournament_image(
                instance.banner.file, 
                image_type='banner'
            )
            
            # Store optimized image paths in a JSON field or related model
            # For now, we'll just log the success
            logger.info(f"Optimized banner for tournament {instance.id}: {len(optimized_images)} versions created")
            
        except Exception as e:
            logger.error(f"Banner optimization failed for tournament {instance.id}: {e}")


def optimize_tournament_thumbnail(sender, instance, **kwargs):
    """
    Signal handler to automatically optimize tournament thumbnails on save.
    """
    if instance.thumbnail and hasattr(instance.thumbnail, 'file'):
        try:
            # Generate optimized versions
            optimized_images = ImageOptimizer.optimize_tournament_image(
                instance.thumbnail.file, 
                image_type='thumbnail'
            )
            
            # Store optimized image paths
            logger.info(f"Optimized thumbnail for tournament {instance.id}: {len(optimized_images)} versions created")
            
        except Exception as e:
            logger.error(f"Thumbnail optimization failed for tournament {instance.id}: {e}")