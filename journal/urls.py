from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='journal_home'),
    path('journals', views.journal_list, name='journal_list'),  # List all journals
    path('journals/new/', views.journal_create, name='journal_create'),
    path('journals/<int:journal_id>/', views.journal_detail, name='journal_detail'),  # Single journal
    path('journals/<int:journal_id>/edit/', views.journal_update, name='journal_update'),
    path('journals/<int:journal_id>/delete/', views.journal_delete, name='journal_delete'),
    path('journals/<int:journal_id>/hide/', views.journal_toggle_hide, name='journal_toggle_hide'),
    path('journals/hidden/', views.journal_hidden, name='journal_hidden'),
    path('journals/places/', views.place_suggest, name='journal_place_suggest'),
    path('journals/content_suggest/', views.content_suggest, name='journal_content_suggest'),

]
