from django.db import models
from django.conf import settings

class Reminder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reminder_and_goals_reminders'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    reminder_time = models.TimeField()
    status = models.BooleanField(default=True)  # Active/Inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for CalDAV integration
    apple_reminder_id = models.CharField(max_length=255, blank=True, null=True)
    apple_calendar_id = models.CharField(max_length=255, blank=True, null=True)
    is_synced_with_apple = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['reminder_time']

class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reminder_and_goals_goals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    target = models.PositiveIntegerField()  # e.g., 5 entries per week
    progress = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def progress_percentage(self):
        if self.target > 0:
            return (self.progress / self.target) * 100
        return 0

    # Add these methods to work with journals
    def get_related_journals(self):
        """Get all journals related to this goal"""
        return self.journals.all()
    
    def get_journal_count(self):
        """Get count of journals related to this goal"""
        return self.journals.count()
    
    def update_progress_from_journals(self):
        """Update progress based on related journal count"""
        journal_count = self.get_journal_count()
        self.progress = min(journal_count, self.target)
        self.save()
        return self.progress

    def is_achieved(self):
        """Check if goal is achieved"""
        return self.progress >= self.target

    def days_remaining(self):
        """Calculate days remaining until end date"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days


class GoalSuggestion(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goal_suggestions'
    )
    journal = models.ForeignKey(
        'journal.Journal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_goal_suggestions'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(default=0.5)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"
    


    