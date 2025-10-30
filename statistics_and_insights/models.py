from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import secrets

class EntryAnalytics(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry = models.OneToOneField('journal.Journal', on_delete=models.CASCADE)
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
    
    # Nouveaux champs
    reading_time = models.IntegerField(default=0)
    keywords = models.JSONField(default=list)
    themes = models.JSONField(default=list)
    
    def __str__(self):
        return f"Analytics for {self.entry.title}"

class UserStatistics(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_entries = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    average_mood = models.FloatField(default=0)
    average_word_count = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Nouveaux champs
    total_words_written = models.IntegerField(default=0)
    favorite_topics = models.JSONField(default=list)
    writing_consistency = models.FloatField(default=0)
    
    def calculate_consistency(self):
        """Calcule la consistance d'écriture"""
        # Implémentation simplifiée
        if self.total_entries > 0:
            return min(1.0, self.current_streak / 30.0)
        return 0.0
    
    def __str__(self):
        return f"Stats for {self.user.username}"

class MoodTrend(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    average_mood = models.FloatField()
    entry_count = models.IntegerField(default=0)
    
    # Nouveaux champs
    dominant_emotion = models.CharField(max_length=50, blank=True)
    mood_volatility = models.FloatField(default=0)
    
    def __str__(self):
        return f"Mood {self.date} - {self.user.username}"

class WeeklyInsight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    insights = models.JSONField(default=dict)
    patterns = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Nouveaux champs
    achievements = models.JSONField(default=list)
    challenges = models.JSONField(default=list)
    
    def __str__(self):
        return f"Weekly Insight {self.week_start} - {self.user.username}"

class CustomReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=[
        ('mood_analysis', 'Mood Analysis'),
        ('writing_habits', 'Writing Habits'),
        ('productivity', 'Productivity Insights'),
        ('custom', 'Custom Report'),
    ])
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    filters = models.JSONField(default=dict)
    data = models.JSONField(default=dict)
    is_shared = models.BooleanField(default=False)
    share_token = models.CharField(max_length=50, blank=True)
    
    # Champs de base
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_share_token(self):
        import secrets
        self.share_token = secrets.token_urlsafe(16)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

# NOUVEAUX MODÈLES POUR L'IA
class AIGeneratedReport(models.Model):
    """Rapports générés automatiquement par l'IA"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=[
        ('weekly_auto', 'Rapport Hebdomadaire Automatique'),
        ('monthly_auto', 'Rapport Mensuel Automatique'), 
        ('mood_analysis', 'Analyse d Humeur IA'),
        ('writing_insights', 'Insights Écriture IA'),
    ], default='weekly_auto')
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Données générées par l'IA
    ai_insights = models.JSONField(default=dict)
    trends_analysis = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    psychological_insights = models.JSONField(default=list)
    
    # Métadonnées
    ai_model_used = models.CharField(max_length=100, default='huggingface')
    confidence_score = models.FloatField(default=0.0)
    is_ai_generated = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rapport IA {self.title} - {self.user.username}"

class BackofficeDashboard(models.Model):
    """Tableau de bord backoffice"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class AIReportLog(models.Model):
    """Journal des générations de rapports IA"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('fallback', 'Fallback Utilisé'),
    ])
    ai_model = models.CharField(max_length=100)
    processing_time = models.FloatField(default=0)  # en secondes
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log {self.report_type} - {self.user.username} - {self.status}"