# journal/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Journal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journals')
    title = models.CharField(max_length=255)
    description = models.TextField()
    entry_date = models.DateField(default=timezone.localdate)
    location = models.CharField(max_length=255, blank=True, null=True)
    hidden = models.BooleanField(default=False)
    category = models.ForeignKey('TagsCat.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='entries')
    tags = models.ManyToManyField('TagsCat.Tag', blank=True, related_name='entries')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_goals = models.ManyToManyField('reminder_and_goals.Goal', blank=True, related_name='journals')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return list(self.tags.values_list('name', flat=True))

    def get_related_goals_count(self):
        return self.related_goals.count()


class JournalImage(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='journal_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.journal.title} ({self.id})"
