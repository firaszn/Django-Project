from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Tag(models.Model):
  
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tags',
        help_text="Owner of this tag"
    )
    name = models.CharField(
        max_length=50,
        help_text="Tag name (e.g., 'Travel', 'Friends')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this tag has been used"
    )
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-usage_count', 'name']
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        indexes = [
            models.Index(fields=['user', 'name']),
            models.Index(fields=['user', '-usage_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.usage_count} uses)"
    
    def clean(self):
        """Validate tag data"""
        if self.name:
            self.name = self.name.strip().lower()
            if len(self.name) < 2:
                raise ValidationError("Tag name must be at least 2 characters")
            if not self.name.replace('-', '').replace('_', '').isalnum():
                raise ValidationError("Tag name can only contain letters, numbers, hyphens, and underscores")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def decrement_usage(self):
        """Decrement usage count"""
        if self.usage_count > 0:
            self.usage_count -= 1
            self.save(update_fields=['usage_count'])