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
    # API endpoints for categories and tags
    path('api/categories/', include('TagsCat.urls.category_urls')),
    path('api/tags/', include('TagsCat.urls.tag_urls')),
    # Web interfaces for categories and tags
    path('categories/', include('TagsCat.web_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)