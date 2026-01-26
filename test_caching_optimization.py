#!/usr/bin/env python
"""
Test script for caching and optimization features.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tournaments.cache_utils import TournamentCache
from tournaments.models import Tournament
from django.core.cache import cache

def test_tournament_cache():
    """Test tournament caching functionality"""
    print("Testing Tournament Cache...")
    
    # Test cache key generation
    tournament_id = "test-tournament-123"
    
    # Test setting and getting stats
    test_stats = {
        'participants': {'registered': 10, 'capacity': 32},
        'engagement': {'views': 150, 'shares': 5}
    }
    
    TournamentCache.set_tournament_stats(tournament_id, test_stats)
    cached_stats = TournamentCache.get_tournament_stats(tournament_id)
    
    if cached_stats == test_stats:
        print("✓ Tournament stats caching works correctly")
    else:
        print("✗ Tournament stats caching failed")
        print(f"Expected: {test_stats}")
        print(f"Got: {cached_stats}")
    
    # Test cache invalidation
    TournamentCache.invalidate_tournament_cache(tournament_id)
    invalidated_stats = TournamentCache.get_tournament_stats(tournament_id)
    
    if invalidated_stats is None:
        print("✓ Cache invalidation works correctly")
    else:
        print("✗ Cache invalidation failed")
    
    print("Tournament cache tests completed.\n")

def test_image_optimization():
    """Test image optimization utilities"""
    print("Testing Image Optimization...")
    
    from tournaments.image_utils import ImageOptimizer
    
    # Test responsive sizes configuration
    sizes = ImageOptimizer.RESPONSIVE_SIZES
    expected_sizes = ['thumbnail', 'small', 'medium', 'large', 'hero']
    
    if all(size in sizes for size in expected_sizes):
        print("✓ Responsive image sizes configured correctly")
    else:
        print("✗ Responsive image sizes configuration incomplete")
    
    # Test media query generation
    media_query = ImageOptimizer._get_media_query_for_size('large')
    if media_query == '(min-width: 1200px)':
        print("✓ Media query generation works correctly")
    else:
        print("✗ Media query generation failed")
    
    print("Image optimization tests completed.\n")

def test_api_endpoints():
    """Test API endpoint imports"""
    print("Testing API Endpoints...")
    
    try:
        from tournaments.api_views import (
            tournament_stats_api,
            tournament_participants_api,
            tournament_matches_api
        )
        print("✓ API endpoints imported successfully")
    except ImportError as e:
        print(f"✗ API endpoint import failed: {e}")
    
    print("API endpoint tests completed.\n")

def test_lazy_loading():
    """Test lazy loading utilities"""
    print("Testing Lazy Loading...")
    
    # Check if lazy loader JavaScript exists
    lazy_loader_path = "static/js/modules/lazy-loader.js"
    if os.path.exists(lazy_loader_path):
        print("✓ Lazy loader JavaScript file exists")
    else:
        print("✗ Lazy loader JavaScript file missing")
    
    # Check if modular JavaScript exists
    modules = [
        "static/js/modules/tournament-stats.js",
        "static/js/modules/participant-list.js"
    ]
    
    for module in modules:
        if os.path.exists(module):
            print(f"✓ Module {module} exists")
        else:
            print(f"✗ Module {module} missing")
    
    print("Lazy loading tests completed.\n")

def main():
    """Run all tests"""
    print("=== Caching and Optimization Tests ===\n")
    
    test_tournament_cache()
    test_image_optimization()
    test_api_endpoints()
    test_lazy_loading()
    
    print("=== All Tests Completed ===")

if __name__ == "__main__":
    main()