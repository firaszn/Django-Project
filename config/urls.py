from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import CustomLoginView

urlpatterns = [
    # Admin Django temporairement activé pour configurer Google OAuth
    path('admin/', admin.site.urls),
    path('', include('journal.urls')),
    path('users/', include('users.urls')),
    # Override allauth login view with custom one that includes reCAPTCHA
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/', include('allauth.urls')),
    path('reminder-and-goals/', include('reminder_and_goals.urls')),
    path('manage/', include('TagsCat.urls')),
    path('statistics-and-insights/', include('statistics_and_insights.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)