# Generated manually for EYTGaming push notification Device model
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subscription_info', models.JSONField(help_text='Push subscription object from browser (endpoint, keys, etc.)')),
                ('user_agent', models.TextField(blank=True, help_text='Browser user agent string')),
                ('device_name', models.CharField(blank=True, help_text="Friendly device name (e.g., 'Chrome on Windows')", max_length=200)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this subscription is still valid')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_used_at', models.DateTimeField(blank=True, help_text='Last time push was sent to this device', null=True)),
                ('user', models.ForeignKey(help_text='User who owns this device', on_delete=django.db.models.deletion.CASCADE, related_name='push_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Push Device',
                'verbose_name_plural': 'Push Devices',
                'db_table': 'push_devices',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['user', 'is_active'], name='push_devices_user_id_is_active_idx'),
        ),
    ]
