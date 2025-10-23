from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class Category(models.Model):
    """
    Predefined categories for organizing journal entries.
    
    Features:
    - User-specific categories
    - Color coding for UI
    - Icon support
    - Entry counting
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        help_text="Owner of this category"
    )
    name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., 'University', 'Personal Growth')"
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Hex color code (e.g., #3B82F6)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon identifier (e.g., 'university', 'heart')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['user', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name}"
    
    def clean(self):
        """Validate category data"""
        # Validate name
        if self.name:
            self.name = self.name.strip().title()
            if len(self.name) < 2:
                raise ValidationError("Category name must be at least 2 characters")
        
        # Validate color (hex format)
        if self.color:
            if not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
                raise ValidationError("Color must be a valid hex code (e.g., #3B82F6)")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_entry_count(self):
        """Get number of entries in this category"""
        return self.entries.count()
    
    def get_recent_entries(self, limit=5):
        """Get recent entries in this category"""
        return self.entries.order_by('-created_at')[:limit]