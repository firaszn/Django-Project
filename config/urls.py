from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Django temporairement activé pour configurer Google OAuth
    path('admin/', admin.site.urls),
    path('', include('journal.urls')),
    path('users/', include('users.urls')),
    path('accounts/', include('allauth.urls')),
    path('reminder-and-goals/', include('reminder_and_goals.urls')),
    # API endpoints for categories and tags (removed - using unified URLs)
    # Category and Tag Management
    path('manage/', include('TagsCat.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)