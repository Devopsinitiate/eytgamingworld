# Generated migration to add landing page fields to Game model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_product_newsarticle_player_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='category',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text='Game category (Fighting, FPS, Sports, Mobile)'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='key_art',
            field=models.ImageField(
                upload_to='games/key_art/',
                null=True,
                blank=True,
                help_text='Key art for landing page display'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='display_order',
            field=models.IntegerField(
                default=0,
                help_text='Order in landing page display'
            ),
        ),
    ]
