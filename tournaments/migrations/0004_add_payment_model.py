from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0003_add_payment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('provider', models.CharField(choices=[('stripe', 'Stripe'), ('paystack', 'Paystack'), ('local', 'Local/Manual')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('charged', 'Charged'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('provider_transaction_id', models.CharField(blank=True, max_length=200, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('participant', models.ForeignKey(on_delete=models.CASCADE, related_name='payments', to='tournaments.participant')),
            ],
            options={
                'db_table': 'tournament_payments',
                'ordering': ['-created_at'],
            },
        ),
    ]
