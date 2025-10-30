from django.db import models
from django.conf import settings
from django.utils import timezone

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


# In reminder_and_goals/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reminder_and_goals_goals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    target = models.PositiveIntegerField(help_text="Target number of journal entries")
    progress = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Completion tracking fields
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target > 0:
            return min(100, (self.progress / self.target) * 100)
        return 0

    def get_related_journals(self):
        """Get all journals related to this goal"""
        return self.journals.all()
    
    def get_journal_count(self):
        """Get count of journals related to this goal"""
        return self.journals.count()
    
    def update_progress_from_journals(self):
        """Update progress based on related journal count"""
        journal_count = self.get_journal_count()
        old_progress = self.progress
        
        # Update progress (can't exceed target)
        self.progress = min(journal_count, self.target)
        
        # Check if goal is newly completed
        was_completed = self.is_completed
        self.is_completed = (self.progress >= self.target)
        
        if self.is_completed and not was_completed:
            self.completed_at = timezone.now()
            print(f"🎯 GOAL COMPLETED: {self.title} - Progress: {self.progress}/{self.target}")
        elif not self.is_completed and was_completed:
            self.completed_at = None
            print(f"🔄 GOAL REOPENED: {self.title} - Progress: {self.progress}/{self.target}")
            
        # Save all changes
        self.save(update_fields=['progress', 'is_completed', 'completed_at', 'updated_at'])
        print(f"✅ Progress updated: {self.title} - {self.progress}/{self.target} - Completed: {self.is_completed}")
        return self.progress

    def is_achieved(self):
        """Check if goal is achieved - use this for template display"""
        return self.is_completed

    def get_progress_status(self):
        """Get progress status text"""
        if self.is_completed:
            return "Completed"
        elif self.progress > 0:
            return "In Progress"
        else:
            return "Not Started"

    def days_remaining(self):
        """Calculate days remaining until end date"""
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days

    def can_add_more_journals(self):
        """Check if more journals can be added to this goal"""
        return not self.is_completed

    def get_missing_count(self):
        """Get how many more journals are needed"""
        return max(0, self.target - self.progress)

    def mark_as_completed(self):
        """Manually mark goal as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
            return True
        return False

    def mark_as_incomplete(self):
        """Manually mark goal as incomplete"""
        if self.is_completed:
            self.is_completed = False
            self.completed_at = None
            self.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
            return True
        return False

    def get_completion_info(self):
        """Get completion information"""
        if self.is_completed and self.completed_at:
            return {
                'is_completed': True,
                'completed_at': self.completed_at,
                'completed_date': self.completed_at.date(),
                'days_to_complete': (self.completed_at.date() - self.start_date).days
            }
        else:
            return {
                'is_completed': False,
                'completed_at': None,
                'days_remaining': self.days_remaining()
            }

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'
        

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
    


    