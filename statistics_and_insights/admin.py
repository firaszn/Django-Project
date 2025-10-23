from django.contrib import admin
from .models import EntryAnalytics, UserStatistics, MoodTrend, WeeklyInsight

@admin.register(EntryAnalytics)
class EntryAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'entry', 'sentiment', 'mood_score', 'word_count']
    list_filter = ['sentiment', 'created_at']

@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_entries', 'current_streak', 'average_mood']

@admin.register(MoodTrend)
class MoodTrendAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'average_mood', 'entry_count']

@admin.register(WeeklyInsight)
class WeeklyInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start', 'week_end']