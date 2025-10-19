from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Avg, F
from .models import Reminder, Goal

class CustomAdminSite(admin.AdminSite):
    site_header = "Custom Admin Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reminders/', self.admin_view(self.reminder_list_view), name='reminder_list_admin'),
            path('goals/', self.admin_view(self.goal_list_view), name='goal_list_admin'),
        ]
        return custom_urls + urls

    def reminder_list_view(self, request):
        reminders = Reminder.objects.all()
        active_reminders = reminders.filter(status=True).count()
        inactive_reminders = reminders.filter(status=False).count()
        
        context = dict(
            self.each_context(request),
            reminders=reminders,
            reminders_count=reminders.count(),
            active_reminders=active_reminders,
            inactive_reminders=inactive_reminders,
            title="Reminders Overview",
        )
        return TemplateResponse(request, "reminder_and_goals/reminder_list_admin.html", context)

    def goal_list_view(self, request):
        goals = Goal.objects.all()
        completed_goals = goals.filter(progress__gte=F('target')).count()
        in_progress_goals = goals.filter(progress__lt=F('target')).count()
        average_progress = goals.aggregate(Avg('progress'))['progress__avg'] or 0
        
        # Calculate progress percentage for each goal
        for goal in goals:
            goal.progress_percentage = goal.progress_percentage()
            goal.is_achieved = goal.progress >= goal.target
        
        context = dict(
            self.each_context(request),
            goals=goals,
            goals_count=goals.count(),
            completed_goals=completed_goals,
            in_progress_goals=in_progress_goals,
            average_progress=round(average_progress, 1),
            title="Goals Overview",
        )
        return TemplateResponse(request, "reminder_and_goals/goal_list_admin.html", context)

custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(Reminder)
custom_admin_site.register(Goal)