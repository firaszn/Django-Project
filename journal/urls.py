from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='journal_home'),
    path('journals', views.journal_list, name='journal_list'),  # List all journals

    path('journals/<int:journal_id>/', views.journal_detail, name='journal_detail'),  # Single journal

    path('journals/new/', views.journal_create, name='journal_create'),
    path('journals/<int:journal_id>/', views.journal_detail, name='journal_detail'),  # Single journal
    path('journals/<int:journal_id>/edit/', views.journal_update, name='journal_update'),
    path('journals/<int:journal_id>/delete/', views.journal_delete, name='journal_delete'),
    path('journals/deleted/', views.journal_deleted_list, name='journal_deleted_list'),
    path('journals/<int:journal_id>/restore/', views.journal_restore, name='journal_restore'),
    path('journals/<int:journal_id>/permanent-delete/', views.journal_permanent_delete, name='journal_permanent_delete'),
    path('journals/<int:journal_id>/hide/', views.journal_toggle_hide, name='journal_toggle_hide'),
    path('journals/hidden/', views.journal_hidden, name='journal_hidden'),
    path('journals/places/', views.place_suggest, name='journal_place_suggest'),
    path('journals/content_suggest/', views.content_suggest, name='journal_content_suggest'),
    path('journals/detect-mood/', views.detect_mood, name='journal_detect_mood'),
    # Calendar JSON endpoint
    path('journals/calendar-data/', views.journal_calendar_data, name='journal_calendar_data'),
    path('journals/calendar-data/', views.journal_calendar_data, name='journal_calendar_data'),
    # AI prompts and nudges
    path('journals/ai-prompts/', views.ai_prompts, name='journal_ai_prompts'),
    path('journals/ai-nudge/', views.ai_nudge, name='journal_ai_nudge'),
    # Garden visualization
    path('journals/garden/', views.journal_garden, name='journal_garden'),
    path('journals/garden-data/', views.journal_garden_data, name='journal_garden_data'),
    path('journals/garden-3d/', views.journal_garden_3d, name='journal_garden_3d'),

]
