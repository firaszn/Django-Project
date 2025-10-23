from django.urls import path
from .views import category_management

app_name = 'TagsCat'

urlpatterns = [
    # Category Management
    path('categories/', category_management.category_management, name='category_management'),
    path('categories/create/', category_management.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', category_management.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', category_management.category_delete, name='category_delete'),
    
    # Tag Management
    path('tags/', category_management.tag_management, name='tag_management'),
    path('tags/create/', category_management.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', category_management.tag_edit, name='tag_edit'),
    path('tags/<int:pk>/delete/', category_management.tag_delete, name='tag_delete'),
]
