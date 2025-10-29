from .simple_views import SimpleCategoryViewSet, SimpleTagViewSet

# Alias for compatibility
CategoryViewSet = SimpleCategoryViewSet
TagViewSet = SimpleTagViewSet

__all__ = ['CategoryViewSet', 'TagViewSet', 'SimpleCategoryViewSet', 'SimpleTagViewSet']