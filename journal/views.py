from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Journal
from reminder_and_goals.models import Goal

@login_required
def home(request):
    # Rediriger les admins vers leur dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'journal/home.html')

@login_required
def journal_list(request):
    """Display list of all journals for the current user"""
    journals = Journal.objects.filter(user=request.user).prefetch_related('related_goals')
    
    context = {
        'journals': journals,
    }
    return render(request, 'journal/journal_list.html', context)

@login_required
def journal_detail(request, journal_id):
    """Display details of a specific journal"""
    journal = Journal.objects.filter(user=request.user, id=journal_id).first()
    
    if not journal:
        return render(request, 'journal/404.html')
    
    context = {
        'journal': journal,
    }
    return render(request, 'journal/journal_detail.html', context)


    