from django.urls import path
from . import views

app_name = 'statistics_and_insights'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('mood-analytics/', views.mood_analytics, name='mood_analytics'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
]