from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Reminder, Goal 
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ReminderForm, GoalForm
from django.shortcuts import redirect
from django.urls import reverse
from journal.models import Journal


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
        print("Form is valid. User:", self.request.user)  # Debugging log
        return super().form_valid(form)

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


class GoalCreateView(CreateView):
    model = Goal
    fields = ['title', 'description', 'target', 'start_date', 'end_date']
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
            except Journal.DoesNotExist:
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



