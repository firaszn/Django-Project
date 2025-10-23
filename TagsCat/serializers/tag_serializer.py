from rest_framework import serializers
from ..models import Tag

class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    
    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'usage_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate tag name"""
        value = value.strip().lower()
        
        if len(value) < 2:
            raise serializers.ValidationError("Tag name must be at least 2 characters")
        
        if len(value) > 50:
            raise serializers.ValidationError("Tag name cannot exceed 50 characters")
        
        # Check if tag already exists for this user
        user = self.context['request'].user
        if self.instance is None:  # Creating new tag
            if Tag.objects.filter(user=user, name=value).exists():
                raise serializers.ValidationError("You already have a tag with this name")
        
        return value


class TagListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing tags"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'usage_count']


class TagDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with entry information"""
    entry_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'usage_count',
            'entry_count',
            'created_at',
            'updated_at'
        ]
    
    def get_entry_count(self, obj):
        """Get number of entries with this tag"""
        return obj.entries.count()