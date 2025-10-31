from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Memory(models.Model):
    """A special moment saved by the user. Can have multiple photos and tags."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='memories'
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('TagsCat.Tag', blank=True, related_name='memories')
    # Optionally related to a journal entry if such model exists
    # Link to the journal entry (the project defines `Journal` model, not `JournalEntry`)
    related_entry = models.ForeignKey(
        'journal.Journal', null=True, blank=True, on_delete=models.SET_NULL, related_name='memories'
    )

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return self.title or f"Memory {self.pk}"


class MemoryPhoto(models.Model):
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='memory_photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.memory} ({self.pk})"
