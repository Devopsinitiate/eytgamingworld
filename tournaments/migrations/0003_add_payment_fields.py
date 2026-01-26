from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='has_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='participant',
            name='amount_paid',
            field=models.DecimalField(default=0.0, max_digits=10, decimal_places=2),
        ),
    ]
