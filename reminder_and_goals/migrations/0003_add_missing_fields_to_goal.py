# Manual migration to add missing fields to Goal model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminder_and_goals', '0002_goalsuggestion_journal'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='is_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='goal',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

