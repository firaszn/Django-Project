from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class JournalEntry(models.Model):
    """
    Journal entry model with categories and tags support.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='journal_entries',
        help_text="Owner of this journal entry"
    )
    title = models.CharField(
        max_length=200,
        help_text="Entry title"
    )
    content = models.TextField(
        help_text="Entry content"
    )
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this entry is public"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def get_absolute_url(self):
        return reverse('journal:entry_detail', kwargs={'pk': self.pk})
    
    def get_tags_list(self):
        """Get list of tag names"""
        return list(self.tags.values_list('name', flat=True))
