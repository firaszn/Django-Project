from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from TagsCat.models import Tag
from TagsCat.serializers import (
    TagSerializer,
    TagListSerializer,
    TagDetailSerializer
)

class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tags.
    
    Endpoints:
    - GET /api/tags/ - List all user's tags
    - POST /api/tags/ - Create new tag
    - GET /api/tags/{id}/ - Get tag details
    - PUT /api/tags/{id}/ - Update tag
    - DELETE /api/tags/{id}/ - Delete tag
    - GET /api/tags/popular/ - Get most popular tags
    - GET /api/tags/search/?q=query - Search tags
    - GET /api/tags/stats/ - Get tag statistics
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only tags belonging to current user"""
        return Tag.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TagListSerializer
        elif self.action == 'retrieve':
            return TagDetailSerializer
        return TagSerializer
    
    def perform_create(self, serializer):
        """Automatically set user when creating tag"""
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """
        List all tags for current user.
        Query params:
        - sort: 'popular', 'name', 'recent' (default: popular)
        """
        queryset = self.get_queryset()
        
        # Sorting
        sort_by = request.query_params.get('sort', 'popular')
        if sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        else:  # popular (default)
            queryset = queryset.order_by('-usage_count', 'name')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get most popular tags.
        Query params:
        - limit: number of tags to return (default: 10)
        """
        limit = int(request.query_params.get('limit', 10))
        tags = self.get_queryset().order_by('-usage_count')[:limit]
        serializer = TagListSerializer(tags, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search tags by name (autocomplete).
        Query params:
        - q: search query (required)
        - limit: number of results (default: 5)
        """
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.query_params.get('limit', 5))
        tags = self.get_queryset().filter(
            name__icontains=query
        )[:limit]
        
        serializer = TagListSerializer(tags, many=True)
        return Response({
            'query': query,
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get tag statistics for current user"""
        queryset = self.get_queryset()
        
        total_tags = queryset.count()
        total_usage = sum(tag.usage_count for tag in queryset)
        most_used = queryset.order_by('-usage_count').first()
        
        return Response({
            'total_tags': total_tags,
            'total_usage': total_usage,
            'most_used_tag': TagListSerializer(most_used).data if most_used else None,
            'average_usage': round(total_usage / total_tags, 2) if total_tags > 0 else 0
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete tag and return confirmation"""
        instance = self.get_object()
        tag_name = instance.name
        entry_count = instance.entries.count()
        
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Tag "{tag_name}" deleted successfully',
            'affected_entries': entry_count
        }, status=status.HTTP_200_OK)
