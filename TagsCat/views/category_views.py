from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from TagsCat.models import Category
from TagsCat.serializers import (
    CategorySerializer,
    CategoryListSerializer,
    CategoryDetailSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    
    Endpoints:
    - GET /api/categories/ - List all user's categories
    - POST /api/categories/ - Create new category
    - GET /api/categories/{id}/ - Get category details
    - PUT /api/categories/{id}/ - Update category
    - DELETE /api/categories/{id}/ - Delete category
    - GET /api/categories/stats/ - Get category statistics
    - GET /api/categories/{id}/entries/ - Get entries in category
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only categories belonging to current user"""
        return Category.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer
    
    def perform_create(self, serializer):
        """Automatically set user when creating category"""
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """
        List all categories for current user.
        Query params:
        - sort: 'name', 'entries', 'recent' (default: name)
        """
        queryset = self.get_queryset()
        
        # Sorting
        sort_by = request.query_params.get('sort', 'name')
        if sort_by == 'entries':
            queryset = queryset.annotate(
                entry_count=Count('entries')
            ).order_by('-entry_count')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        else:  # name (default)
            queryset = queryset.order_by('name')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get category statistics for current user"""
        queryset = self.get_queryset()
        
        total_categories = queryset.count()
        categories_with_entries = queryset.annotate(
            entry_count=Count('entries')
        ).filter(entry_count__gt=0).count()
        
        most_used = queryset.annotate(
            entry_count=Count('entries')
        ).order_by('-entry_count').first()
        
        return Response({
            'total_categories': total_categories,
            'categories_with_entries': categories_with_entries,
            'most_used_category': CategoryListSerializer(most_used).data if most_used else None
        })
    
    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """
        Get all entries in this category.
        Query params:
        - limit: number of entries (default: all)
        """
        category = self.get_object()
        limit = request.query_params.get('limit', None)
        
        entries = category.entries.all()
        if limit:
            entries = entries[:int(limit)]
        
        # Note: You'll need to import your Entry serializer
        # from ..serializers import EntrySerializer
        # serializer = EntrySerializer(entries, many=True)
        
        return Response({
            'category': CategoryListSerializer(category).data,
            'entry_count': category.get_entry_count(),
            'entry_ids': list(entries.values_list('id', flat=True))
            # 'entries': serializer.data  # Uncomment when you have EntrySerializer
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete category and return confirmation"""
        instance = self.get_object()
        category_name = instance.name
        entry_count = instance.get_entry_count()
        
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Category "{category_name}" deleted successfully',
            'affected_entries': entry_count,
            'note': 'Entries are not deleted, only unlinked from this category'
        }, status=status.HTTP_200_OK)
