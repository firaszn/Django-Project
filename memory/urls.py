from django.urls import path
from . import views

app_name = 'memory'

urlpatterns = [
    path('', views.memory_management, name='memory_management'),
    path('add/', views.memory_create, name='memory_create'),
    path('<int:pk>/edit/', views.memory_edit, name='memory_edit'),
    path('<int:pk>/', views.memory_detail, name='memory_detail'),
    path('<int:pk>/delete/', views.memory_delete, name='memory_delete'),
    path('<int:pk>/photo/<int:photo_pk>/delete/', views.memory_photo_delete, name='memory_photo_delete'),
    path('ai-suggest/', views.memory_ai_suggest, name='memory_ai_suggest'),
]
