from django.urls import path
from . import views
from .admin import custom_admin_site

urlpatterns = [
    path('reminders/', views.ReminderListView.as_view(), name='reminder_list'),
    path('reminders/new/', views.ReminderCreateView.as_view(), name='reminder_create'),
    path('reminders/<int:pk>/edit/', views.ReminderUpdateView.as_view(), name='reminder_edit'),
    path('reminders/<int:pk>/delete/', views.ReminderDeleteView.as_view(), name='reminder_delete'),

    path('goals/', views.GoalListView.as_view(), name='goal_list'),
    path('goals/new/', views.GoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:pk>/edit/', views.GoalUpdateView.as_view(), name='goal_edit'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal_delete'),

    # Suggestions
    path('goals/suggestions/', views.GoalSuggestionListView.as_view(), name='goal_suggestions'),
    path('goals/suggestions/<int:suggestion_id>/accept/', views.AcceptGoalSuggestionView.as_view(), name='goal_suggestion_accept'),
    # API endpoints
    path('api/goals/suggestions/', views.api_list_goal_suggestions, name='api_goal_suggestions'),
    path('api/goals/suggestions/<int:suggestion_id>/accept/', views.api_accept_goal_suggestion, name='api_goal_suggestion_accept'),

     # Admin URLs - access through the custom admin site
    path('admin/reminders/', custom_admin_site.reminder_list_view, name='reminder_list_admin'),
    path('admin/goals/', custom_admin_site.goal_list_view, name='goal_list_admin'),


    path('connect-apple/', views.connect_apple_account, name='connect_apple'),




]