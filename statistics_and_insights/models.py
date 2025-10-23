from django.db import models
from django.conf import settings
from django.utils import timezone

class EntryAnalytics(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← CORRIGÉ
        on_delete=models.CASCADE
    )
    entry = models.OneToOneField(
        'journal.Journal',  # ← CORRIGÉ (Journal au lieu de Entry)
        on_delete=models.CASCADE
    )
    mood_score = models.FloatField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, choices=[
        ('very_negative', 'Très Négatif'),
        ('negative', 'Négatif'),
        ('neutral', 'Neutre'),
        ('positive', 'Positif'),
        ('very_positive', 'Très Positif'),
    ], default='neutral')
    word_count = models.IntegerField(default=0)
    emotions = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics for {self.entry.title}"

class UserStatistics(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ← CORRIGÉ
        on_delete=models.CASCADE
    )
    total_entries = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    average_mood = models.FloatField(default=0)
    average_word_count = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.user.username}"

class MoodTrend(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← CORRIGÉ
        on_delete=models.CASCADE
    )
    date = models.DateField()
    average_mood = models.FloatField()
    entry_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Mood {self.date} - {self.user.username}"

class WeeklyInsight(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← CORRIGÉ
        on_delete=models.CASCADE
    )
    week_start = models.DateField()
    week_end = models.DateField()
    insights = models.JSONField(default=dict)
    patterns = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Weekly Insight {self.week_start} - {self.user.username}"