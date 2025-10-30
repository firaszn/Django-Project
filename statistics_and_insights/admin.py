from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import EntryAnalytics, UserStatistics, MoodTrend, WeeklyInsight, CustomReport, AIGeneratedReport, AIReportLog, BackofficeDashboard

class StatisticsAdminSite(admin.AdminSite):
    site_header = "Statistics & Insights Backoffice"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backoffice/', self.admin_view(self.backoffice_dashboard_view), name='backoffice_dashboard_admin'),
            path('backoffice/ai-reports/', self.admin_view(self.backoffice_ai_reports_view), name='backoffice_ai_reports_admin'),
            path('backoffice/ai-reports/<int:pk>/', self.admin_view(self.backoffice_ai_report_detail_view), name='backoffice_ai_report_detail_admin'),
        ]
        return custom_urls + urls

    def backoffice_dashboard_view(self, request):
        # Logique pour le dashboard backoffice
        total_users = UserStatistics.objects.values('user').distinct().count()
        total_reports = CustomReport.objects.count()
        total_ai_reports = AIGeneratedReport.objects.count()
        
        context = dict(
            self.each_context(request),
            total_users=total_users,
            total_reports=total_reports,
            total_ai_reports=total_ai_reports,
            title="Statistics & Insights Backoffice",
        )
        return TemplateResponse(request, "statistics_and_insights/backoffice_dashboard.html", context)

    def backoffice_ai_reports_view(self, request):
        # Logique pour la liste des rapports IA
        ai_reports = AIGeneratedReport.objects.all().select_related('user')
        
        context = dict(
            self.each_context(request),
            ai_reports=ai_reports,
            title="AI Reports Management",
        )
        return TemplateResponse(request, "statistics_and_insights/backoffice_ai_reports.html", context)

    def backoffice_ai_report_detail_view(self, request, pk):
        # Logique pour le détail d'un rapport IA
        ai_report = AIGeneratedReport.objects.get(pk=pk)
        
        context = dict(
            self.each_context(request),
            ai_report=ai_report,
            title=f"AI Report: {ai_report.title}",
        )
        return TemplateResponse(request, "statistics_and_insights/backoffice_ai_report_detail.html", context)

# Configuration admin standard pour les modèles
@admin.register(EntryAnalytics)
class EntryAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'entry', 'sentiment', 'mood_score', 'word_count', 'reading_time', 'created_at']
    list_filter = ['sentiment', 'created_at']
    search_fields = ['user__username', 'entry__title']

@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_entries', 'current_streak', 'average_mood', 'writing_consistency']

@admin.register(MoodTrend)
class MoodTrendAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'average_mood', 'entry_count', 'dominant_emotion']

@admin.register(WeeklyInsight)
class WeeklyInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start', 'week_end']

@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'date_range_start', 'date_range_end', 'is_shared', 'created_at']
    list_filter = ['report_type', 'is_shared', 'created_at']
    search_fields = ['title', 'user__username', 'description']

@admin.register(AIGeneratedReport)
class AIGeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'period_start', 'period_end', 'ai_model_used', 'confidence_score', 'created_at']
    list_filter = ['report_type', 'ai_model_used', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['ai_insights', 'trends_analysis', 'recommendations', 'psychological_insights']
    
    def has_add_permission(self, request):
        return False  # Empêcher l'ajout manuel

@admin.register(AIReportLog)
class AIReportLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'status', 'ai_model', 'processing_time', 'created_at']
    list_filter = ['status', 'report_type', 'created_at']
    search_fields = ['user__username']

@admin.register(BackofficeDashboard)
class BackofficeDashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']

# Instance de l'admin personnalisé
statistics_admin_site = StatisticsAdminSite(name='statistics_admin')