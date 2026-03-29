"""
Sitemaps for EYTGaming — covers all public-facing pages.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tournaments.models import Tournament
from venues.models import Venue
from coaching.models import CoachProfile
from teams.models import Team
from store.models import Product


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return [
            'home',
            'about',
            'privacy',
            'terms',
        ]

    def location(self, item):
        return reverse(item)


class CoreStaticSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return [
            'core:leaderboard',
            'tournaments:list',
            'teams:list',
            'coaching:coach_list',
            'store:product_list',
            'venues:list',
        ]

    def location(self, item):
        return reverse(item)


class TournamentSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Tournament.objects.filter(
            is_public=True,
            status__in=['registration', 'check_in', 'in_progress', 'completed']
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class VenueSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Venue.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CoachSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return CoachProfile.objects.filter(
            status='active',
            accepting_students=True
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class TeamSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Team.objects.filter(
            is_public=True,
            status='active'
        ).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Product.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('store:product_detail', kwargs={'slug': obj.slug})


sitemaps = {
    'static': StaticViewSitemap,
    'core': CoreStaticSitemap,
    'tournaments': TournamentSitemap,
    'venues': VenueSitemap,
    'coaches': CoachSitemap,
    'teams': TeamSitemap,
    'products': ProductSitemap,
}
