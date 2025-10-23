from rest_framework import serializers
from ..models import Category

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'color',
            'icon',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate category name"""
        value = value.strip().title()
        
        if len(value) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters")
        
        if len(value) > 100:
            raise serializers.ValidationError("Category name cannot exceed 100 characters")
        
        # Check if category already exists for this user
        user = self.context['request'].user
        if self.instance is None:  # Creating new category
            if Category.objects.filter(user=user, name=value).exists():
                raise serializers.ValidationError("You already have a category with this name")
        
        return value
    
    def validate_color(self, value):
        """Validate hex color code"""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #3B82F6)")
        return value


class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing categories"""
    entry_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon', 'entry_count']
    
    def get_entry_count(self, obj):
        """Get number of entries in this category"""
        return obj.get_entry_count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with statistics"""
    entry_count = serializers.SerializerMethodField()
    recent_entries = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'color',
            'icon',
            'description',
            'entry_count',
            'recent_entries',
            'created_at',
            'updated_at'
        ]
    
    def get_entry_count(self, obj):
        """Get number of entries in this category"""
        return obj.get_entry_count()
    
    def get_recent_entries(self, obj):
        """Get IDs of recent entries"""
        return list(obj.get_recent_entries().values_list('id', flat=True))