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

     # Admin URLs - access through the custom admin site
    path('admin/reminders/', custom_admin_site.reminder_list_view, name='reminder_list_admin'),
    path('admin/goals/', custom_admin_site.goal_list_view, name='goal_list_admin'),


]