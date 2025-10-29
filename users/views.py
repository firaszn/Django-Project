from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView, DetailView
from django.db.models import Q, Count
from django.core.paginator import Paginator
<<<<<<< HEAD
from .forms import UserProfileForm
from .models import CustomUser
=======
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import UserProfileForm
from .models import CustomUser
from .ai_services import BioGeneratorService, FraudDetectionService
>>>>>>> ecdb9b019095c41a274895a0b0c6bd4521bd1f2e

class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/profile.html'
    context_object_name = 'user'
    
    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Your profile has been updated successfully!'))
        return super().form_valid(form)

@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your settings have been updated successfully!'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/profile_settings.html', {
        'form': form,
        'active_tab': 'settings'
    })

# Vérifier si l'utilisateur est admin
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard personnalisé pour les administrateurs"""
    
    # Statistiques générales
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    admin_users = CustomUser.objects.filter(role='admin').count()
    verified_users = CustomUser.objects.filter(verified=True).count()
    
    # Utilisateurs récents
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    # Statistiques par statut
    status_stats = CustomUser.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'verified_users': verified_users,
        'recent_users': recent_users,
        'status_stats': status_stats,
    }
    
    return render(request, 'users/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users_list(request):
    """Liste des utilisateurs avec recherche et filtres"""
    
    # Récupérer les paramètres de recherche et filtres
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    role_filter = request.GET.get('role', '')
    
    # Requête de base - Exclure l'utilisateur connecté (admin)
    users = CustomUser.objects.exclude(id=request.user.id).order_by('-date_joined')
    
    # Appliquer la recherche
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Appliquer les filtres
    if status_filter:
        users = users.filter(status=status_filter)
    
    if role_filter:
        users = users.filter(role=role_filter)
    
<<<<<<< HEAD
    # Pagination
    paginator = Paginator(users, 10)  # 10 utilisateurs par page
=======
    # Calculer les scores de confiance pour chaque utilisateur
    users_with_confidence = []
    for user in users:
        fraud_data = FraudDetectionService.analyze_user(user)
        users_with_confidence.append({
            'user': user,
            'confidence_score': fraud_data['confidence_score'],
            'risk_level': fraud_data['risk_level']
        })
    
    # Pagination
    paginator = Paginator(users_with_confidence, 10)  # 10 utilisateurs par page
>>>>>>> ecdb9b019095c41a274895a0b0c6bd4521bd1f2e
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    # Statistiques pour la sidebar
    total_users = CustomUser.objects.exclude(id=request.user.id).count()
    active_users = CustomUser.objects.exclude(id=request.user.id).filter(is_active=True).count()
    admin_users = CustomUser.objects.exclude(id=request.user.id).filter(role='admin').count()
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
    }
    
    return render(request, 'users/admin_users_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """Détails d'un utilisateur"""
    user = CustomUser.objects.get(id=user_id)
    
<<<<<<< HEAD
=======
    # Analyse de fraude/confiance
    fraud_data = FraudDetectionService.analyze_user(user)
    
>>>>>>> ecdb9b019095c41a274895a0b0c6bd4521bd1f2e
    # Statistiques pour la sidebar
    total_users = CustomUser.objects.exclude(id=request.user.id).count()
    active_users = CustomUser.objects.exclude(id=request.user.id).filter(is_active=True).count()
    admin_users = CustomUser.objects.exclude(id=request.user.id).filter(role='admin').count()
    
    context = {
        'viewed_user': user,
<<<<<<< HEAD
=======
        'fraud_data': fraud_data,
>>>>>>> ecdb9b019095c41a274895a0b0c6bd4521bd1f2e
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
    }
    
    return render(request, 'users/admin_user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_toggle_status(request, user_id):
    """Activer/Désactiver un utilisateur"""
    user = CustomUser.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    status = _('activated') if user.is_active else _('deactivated')
    messages.success(request, _(f'User {user.email} has been {status}'))
    
<<<<<<< HEAD
    return redirect('admin_users_list')
=======
    return redirect('admin_users_list')

# Nouvelle vue pour générer une bio avec IA
@login_required
@require_http_methods(["POST"])
def generate_bio_ai(request):
    """Génère une bio avec l'IA pour l'utilisateur connecté"""
    try:
        keywords = request.POST.get('keywords', '').split(',')
        keywords = [k.strip() for k in keywords if k.strip()]
        
        bio = BioGeneratorService.generate_bio(request.user, keywords)
        
        return JsonResponse({
            'success': True,
            'bio': bio
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
>>>>>>> ecdb9b019095c41a274895a0b0c6bd4521bd1f2e
