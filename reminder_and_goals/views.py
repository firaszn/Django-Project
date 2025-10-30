from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from .models import Reminder, Goal 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import ReminderForm, GoalForm
from .models import GoalSuggestion
from .services.ai_goal_recommender import generate_suggestions_for_journal
from journal.models import Journal
from users.models import UserProfile

@login_required
def connect_apple_account(request):
    if request.method == 'POST':
        apple_username = request.POST.get('apple_username')
        apple_password = request.POST.get('apple_password')
        
        # Validate credentials by testing connection
        from .services.apple_reminders_service import AppleRemindersService
        service = AppleRemindersService(apple_username, apple_password)
        
        if service.connect():
            # Save credentials - make sure this is working
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.apple_username = apple_username
            # Make sure the password is being set
            profile.apple_password = apple_password  # Direct storage for testing
            profile.is_apple_connected = True
            profile.save()
            
            # Verify it was saved
            print(f"Saved - Username: {profile.apple_username}, Password: {profile.apple_password}")
            
            messages.success(request, "Successfully connected to Apple Reminders!")
            return redirect('reminder_list')
        else:
            messages.error(request, "Failed to connect to Apple. Please check your credentials.")
    
    return render(request, 'reminder_and_goals/connect_apple.html')

class ReminderListView(LoginRequiredMixin, ListView):
    model = Reminder
    template_name = 'reminder_and_goals/reminder_list.html'

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

class ReminderCreateView(LoginRequiredMixin, CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'reminder_and_goals/reminder_form.html'
    success_url = reverse_lazy('reminder_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Save the instance first
        response = super().form_valid(form)
        
        # The signal will handle the Apple sync automatically
        # You can check if it worked
        if hasattr(self.object, 'is_synced_with_apple') and self.object.is_synced_with_apple:
            messages.success(self.request, "Reminder created and synced with Apple!")
        else:
            messages.warning(self.request, "Reminder created locally. Connect Apple account to sync with iPhone.")
        
        return response
    

class ReminderUpdateView(LoginRequiredMixin, UpdateView):
    model = Reminder
    fields = ['title', 'description', 'reminder_time', 'status']
    template_name = 'reminder_and_goals/reminder_form.html'
    success_url = reverse_lazy('reminder_list')

class ReminderDeleteView(LoginRequiredMixin, DeleteView):
    model = Reminder
    template_name = 'reminder_and_goals/reminder_confirm_delete.html'
    success_url = reverse_lazy('reminder_list')

class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'reminder_and_goals/goal_list.html'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)


class GoalCreateView(LoginRequiredMixin, CreateView):  # Add LoginRequiredMixin here
    model = Goal
    form_class = GoalForm  # Use form_class instead of fields
    template_name = 'reminder_and_goals/goal_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        journal_id = self.request.GET.get('journal_id')
        if journal_id:
            try:
                journal = Journal.objects.get(id=journal_id, user=self.request.user)
                context['journal_title'] = journal.title
            except Journal.DoesNotExist:
                context['journal_title'] = None
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Link to journal if journal_id is provided
        journal_id = self.request.GET.get('journal_id') or self.request.POST.get('journal_id')
        if journal_id:
            try:
                journal = Journal.objects.get(id=journal_id, user=self.request.user)
                journal.related_goals.add(self.object)
                print(f"Successfully linked goal '{self.object.title}' to journal '{journal.title}'")  # Debug
            except Journal.DoesNotExist:
                print(f"Journal with id {journal_id} not found for user {self.request.user}")  # Debug
                pass
        
        return response

    def get_success_url(self):
        journal_id = self.request.GET.get('journal_id') or self.request.POST.get('journal_id')
        if journal_id:
            return reverse('journal_detail', kwargs={'journal_id': journal_id})
        return reverse('goal_list')

class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    fields = ['title', 'description', 'target', 'progress', 'start_date', 'end_date']
    template_name = 'reminder_and_goals/goal_form.html'
    success_url = reverse_lazy('goal_list')

class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = Goal
    template_name = 'reminder_and_goals/goal_confirm_delete.html'
    success_url = reverse_lazy('goal_list')




class GoalSuggestionListView(LoginRequiredMixin, ListView):
    model = GoalSuggestion
    template_name = 'reminder_and_goals/goal_suggestions.html'

    def get_queryset(self):
        qs = GoalSuggestion.objects.filter(user=self.request.user).order_by('-created_at')
        journal_id = self.request.GET.get('journal_id')
        if journal_id:
            qs = qs.filter(journal_id=journal_id)
        return qs

    def get(self, request, *args, **kwargs):
        journal_id = request.GET.get('journal_id')
        if journal_id:
            try:
                j = Journal.objects.get(id=journal_id, user=request.user)
                # Always refresh suggestions: clear previous pending ones for this journal
                GoalSuggestion.objects.filter(user=request.user, journal=j, status='pending').delete()
                generate_suggestions_for_journal(request.user, j)
            except Journal.DoesNotExist:
                pass
        return super().get(request, *args, **kwargs)


class AcceptGoalSuggestionView(LoginRequiredMixin, View):
    def post(self, request, suggestion_id):
        try:
            suggestion = GoalSuggestion.objects.get(id=suggestion_id, user=request.user)
        except GoalSuggestion.DoesNotExist:
            return HttpResponseForbidden("Not found or not allowed")

        if suggestion.status == 'accepted':
            messages.info(request, "Suggestion already accepted")
            return redirect('goal_suggestions')

        # Create a Goal from the suggestion
        goal = Goal.objects.create(
            user=request.user,
            title=suggestion.title,
            description=suggestion.description or '',
            target=5,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
        )

        # Link to journal if exists
        if suggestion.journal:
            suggestion.journal.related_goals.add(goal)

        # Optionally, auto-create a supporting reminder at 09:00
        try:
            from datetime import time
            Reminder.objects.create(
                user=request.user,
                title=suggestion.title,
                description=suggestion.description or '',
                reminder_time=time(9, 0, 0),
                status=True,
            )
        except Exception:
            pass

        suggestion.status = 'accepted'
        suggestion.save(update_fields=['status'])

        messages.success(request, "Suggestion accepted and goal created.")
        return redirect('goal_list')


def api_list_goal_suggestions(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    rows = GoalSuggestion.objects.filter(user=request.user).order_by('-created_at')
    data = [
        {
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'category': s.category,
            'confidence': s.confidence,
            'status': s.status,
            'journal_id': s.journal_id,
            'created_at': s.created_at.isoformat(),
        }
        for s in rows
    ]
    return JsonResponse({'results': data})


def api_accept_goal_suggestion(request, suggestion_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    view = AcceptGoalSuggestionView.as_view()
    return view(request, suggestion_id=suggestion_id)
