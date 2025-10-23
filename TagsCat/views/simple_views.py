from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from TagsCat.models import Category, Tag
from TagsCat.serializers import CategorySerializer, TagSerializer

class SimpleCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

class SimpleTagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)
