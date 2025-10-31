# Generated manually to add missing fields to existing tables

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics_and_insights', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='entryanalytics',
            name='reading_time',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='entryanalytics',
            name='keywords',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='entryanalytics',
            name='themes',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='userstatistics',
            name='total_words_written',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userstatistics',
            name='favorite_topics',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='userstatistics',
            name='writing_consistency',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='moodtrend',
            name='dominant_emotion',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='moodtrend',
            name='mood_volatility',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='weeklyinsight',
            name='achievements',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='weeklyinsight',
            name='challenges',
            field=models.JSONField(default=list),
        ),
    ]

