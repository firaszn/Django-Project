from django.urls import path
from . import views

urlpatterns = [
    # Profile URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    
    # AI Features
    path('profile/generate-bio-ai/', views.generate_bio_ai, name='generate_bio_ai'),
    
    # Admin Dashboard URLs
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/users/', views.admin_users_list, name='admin_users_list'),
    path('dashboard/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('dashboard/users/<int:user_id>/toggle-status/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    
]
