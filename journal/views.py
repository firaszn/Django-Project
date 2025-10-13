from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    # Rediriger les admins vers leur dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'journal/home.html')