from django.db import models
from django.conf import settings
from django.utils import timezone


class JournalQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class JournalManager(models.Manager):
    def get_queryset(self):
        return JournalQuerySet(self.model, using=self._db).alive()


class JournalAllManager(models.Manager):
    """Manager that returns all journals including trashed ones."""
    def get_queryset(self):
        return JournalQuerySet(self.model, using=self._db)

class Journal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='journals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    # The date this entry should be associated with (can be today or user-chosen)
    entry_date = models.DateField(default=timezone.localdate)

    # Optional location for the entry (free text for now)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Soft-delete / hide flag
    hidden = models.BooleanField(default=False)
    
    # AI-detected mood
    mood = models.CharField(
        max_length=20,
        choices=[
            ('happy', 'Happy'),
            ('sad', 'Sad'),
            ('neutral', 'Neutral'),
        ],
        null=True,
        blank=True,
        help_text="AI-detected mood from entry content"
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

    # Soft-delete timestamp. If set, the entry is considered trashed.
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="When this entry was moved to the trash")

    # Optional AI-generated closing reflection (stored for later viewing)
    closing_reflection = models.TextField(blank=True, null=True, help_text="AI-generated or fallback closing reflection")

    # Managers: default excludes deleted entries
    objects = JournalManager()
    all_objects = JournalAllManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        """Mark the journal as deleted (move to trash)."""
        self.deleted_at = timezone.now()
        # Save only the deleted_at to minimize accidental updates
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """Restore a previously trashed journal."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    def permanently_delete(self):
        """Permanently delete the DB row (and cascade to related objects)."""
        super(Journal, self).delete()

    def get_tags_list(self):
        """Get list of tag names"""
        return list(self.tags.values_list('name', flat=True))

    def get_related_goals_count(self):
        return self.related_goals.count()


class JournalImage(models.Model):
    """Simple model to store images attached to a Journal entry."""
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='journal_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.journal.title} ({self.id})"


class AIPromptUsage(models.Model):
    """Track which AI-generated prompts a user has chosen, so we don't repeat them.

    We store the prompt text and timestamp. Prompts used within a cooldown
    window (e.g., 100 days) will be excluded from future suggestions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_prompts')
    prompt_text = models.TextField()
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']

    def __str__(self):
        return f"AI prompt for {self.user} @ {self.used_at:%Y-%m-%d}: {self.prompt_text[:50]}"
