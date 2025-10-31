# Manual migration to add missing Apple integration fields to Reminder model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminder_and_goals', '0003_add_missing_fields_to_goal'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='apple_reminder_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='apple_calendar_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='is_synced_with_apple',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reminder',
            name='last_sync_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

