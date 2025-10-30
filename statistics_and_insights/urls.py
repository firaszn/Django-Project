# statistics_and_insights/urls.py
from django.urls import path
from . import views
from .admin import statistics_admin_site

app_name = 'statistics_and_insights'

urlpatterns = [
    # URLs de base
    path('', views.dashboard_view, name='dashboard'),
    path('mood-analytics/', views.mood_analytics, name='mood_analytics'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
    path('api/advanced-statistics/', views.advanced_statistics_api, name='advanced_statistics_api'),
    path('api/real-time-analysis/', views.real_time_analysis_api, name='real_time_analysis'),
    
    # CRUD URLs for Custom Reports
    path('reports/', views.custom_report_list, name='report_list'),
    path('reports/create/', views.custom_report_create, name='report_create'),
    path('reports/<int:pk>/', views.custom_report_detail, name='report_detail'),
    path('reports/<int:pk>/update/', views.custom_report_update, name='report_update'),
    path('reports/<int:pk>/delete/', views.custom_report_delete, name='report_delete'),
    path('reports/<int:pk>/share/', views.custom_report_share, name='report_share'),
    path('shared/<str:share_token>/', views.shared_report_view, name='shared_report'),
    
    # URLs pour rapports IA
    path('ai-reports/generate/', views.generate_ai_report, name='generate_ai_report'),
    path('ai-reports/', views.ai_reports_list, name='ai_reports_list'),
    path('ai-reports/<int:pk>/', views.ai_report_detail, name='ai_report_detail'),
    path('ai-reports/<int:pk>/update/', views.ai_report_update, name='ai_report_update'),
    path('ai-reports/<int:pk>/delete/', views.ai_report_delete, name='ai_report_delete'),

    # URLs Gemini
    path('test-gemini/', views.test_gemini, name='test_gemini'),
    path('generate-gemini-report/', views.generate_gemini_report, name='generate_gemini_report'),
    path('generate-gemini-report-debug/', views.generate_gemini_report_debug, name='generate_gemini_report_debug'),
    path('test-gemini-detailed/', views.test_gemini_detailed, name='test_gemini_detailed'),

    
    # URLs BACKOFFICE
    path('admin/backoffice/', views.backoffice_dashboard, name='backoffice_dashboard'),
    path('admin/backoffice/ai-reports/', views.backoffice_ai_reports, name='backoffice_ai_reports'),
    path('admin/backoffice/ai-reports/<int:pk>/', views.backoffice_ai_report_detail, name='backoffice_ai_report_detail'),

]