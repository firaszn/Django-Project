from django.db import models
from django.conf import settings

class Journal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='journals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    category = models.ForeignKey(
        'TagsCat.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entries',
        help_text="Entry category"
    )
    tags = models.ManyToManyField(
        'TagsCat.Tag',
        blank=True,
        related_name='entries',
        help_text="Entry tags"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this entry is public"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationship with Goals - One Journal can link to multiple Goals
    related_goals = models.ManyToManyField(
        'reminder_and_goals.Goal',  # Reference the Goal model from reminder_and_goals app
        related_name='journals',    # This creates the reverse relation: goal.journals.all()
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        """Get list of tag names"""
        return list(self.tags.values_list('name', flat=True))

    def get_related_goals_count(self):
        return self.related_goals.count()
