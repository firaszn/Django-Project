from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views.category_views import CategoryViewSet
from .views.tag_views import TagViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # Expose the DRF router under the app-level api include. The project-level
    # `config/urls.py` should include this module at path('api/', include(...)).
    path('', include(router.urls)),
]
