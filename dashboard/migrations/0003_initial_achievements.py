# Generated data migration for initial achievement definitions

from django.db import migrations
from django.utils.text import slugify
import uuid


def create_initial_achievements(apps, schema_editor):
    """Create initial achievement definitions"""
    Achievement = apps.get_model('dashboard', 'Achievement')
    
    achievements = [
        {
            'name': 'First Tournament Win',
            'slug': 'first-tournament-win',
            'description': 'Win your first tournament and claim victory!',
            'achievement_type': 'tournament',
            'rarity': 'uncommon',
            'is_progressive': False,
            'target_value': 1,
            'points_reward': 50,
            'is_active': True,
            'is_hidden': False,
        },
        {
            'name': '10 Tournaments Participated',
            'slug': 'ten-tournaments',
            'description': 'Participate in 10 tournaments and show your dedication to competitive gaming.',
            'achievement_type': 'tournament',
            'rarity': 'common',
            'is_progressive': True,
            'target_value': 10,
            'points_reward': 30,
            'is_active': True,
            'is_hidden': False,
        },
        {
            'name': 'Top 3 Finish',
            'slug': 'top-three-finish',
            'description': 'Finish in the top 3 of any tournament and prove your skills.',
            'achievement_type': 'tournament',
            'rarity': 'uncommon',
            'is_progressive': False,
            'target_value': 1,
            'points_reward': 40,
            'is_active': True,
            'is_hidden': False,
        },
        {
            'name': 'Join First Team',
            'slug': 'first-team',
            'description': 'Join your first team and start your journey in team competitions.',
            'achievement_type': 'social',
            'rarity': 'common',
            'is_progressive': False,
            'target_value': 1,
            'points_reward': 20,
            'is_active': True,
            'is_hidden': False,
        },
        {
            'name': 'Profile Complete',
            'slug': 'profile-complete',
            'description': 'Complete your profile 100% and unlock all platform features.',
            'achievement_type': 'platform',
            'rarity': 'common',
            'is_progressive': False,
            'target_value': 1,
            'points_reward': 50,
            'is_active': True,
            'is_hidden': False,
        },
    ]
    
    for achievement_data in achievements:
        Achievement.objects.create(
            id=uuid.uuid4(),
            **achievement_data
        )


def remove_initial_achievements(apps, schema_editor):
    """Remove initial achievement definitions"""
    Achievement = apps.get_model('dashboard', 'Achievement')
    
    slugs = [
        'first-tournament-win',
        'ten-tournaments',
        'top-three-finish',
        'first-team',
        'profile-complete',
    ]
    
    Achievement.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_profilecompleteness_userreport'),
    ]

    operations = [
        migrations.RunPython(create_initial_achievements, remove_initial_achievements),
    ]
