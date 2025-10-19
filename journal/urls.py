from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='journal_home'),
    path('journals', views.journal_list, name='journal_list'),  # List all journals
    path('journals/<int:journal_id>/', views.journal_detail, name='journal_detail'),  # Single journal

]
