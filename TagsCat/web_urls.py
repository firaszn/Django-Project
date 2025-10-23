from django.urls import path
from . import web_views

app_name = 'TagsCat'

urlpatterns = [
    # Dashboard
    path('', web_views.dashboard, name='dashboard'),
    
    # Categories
    path('categories/', web_views.category_list, name='category_list'),
    path('categories/create/', web_views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', web_views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', web_views.category_delete, name='category_delete'),
    
    # Tags
    path('tags/', web_views.tag_list, name='tag_list'),
    path('tags/create/', web_views.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', web_views.tag_edit, name='tag_edit'),
    path('tags/<int:pk>/delete/', web_views.tag_delete, name='tag_delete'),
]
