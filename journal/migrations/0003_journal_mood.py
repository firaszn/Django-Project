# Generated migration for mood field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0002_journal_entry_date_journal_hidden_journal_location_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='mood',
            field=models.CharField(blank=True, choices=[('happy', 'Happy'), ('sad', 'Sad'), ('neutral', 'Neutral')], help_text='AI-detected mood from entry content', max_length=20, null=True),
        ),
    ]
