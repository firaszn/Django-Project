from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        Redirige les admins vers le dashboard et les utilisateurs vers la home
        """
        user = request.user
        if user.is_authenticated and user.role == 'admin':
            return reverse('admin_dashboard')
        return reverse('journal_home')
    
    def get_email_confirmation_redirect_url(self, request):
        """
        Redirige vers la page de login après confirmation d'email
        """
        return reverse('account_login')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        Redirige les admins vers le dashboard et les utilisateurs vers la home après connexion sociale
        """
        user = request.user
        if user.is_authenticated and user.role == 'admin':
            return reverse('admin_dashboard')
        return reverse('journal_home')
    
    def pre_social_login(self, request, sociallogin):
        """
        Appelé avant la connexion sociale pour personnaliser le processus
        """
        # Si l'utilisateur existe déjà avec cet email, on le connecte
        if sociallogin.user.email:
            try:
                from users.models import CustomUser
                existing_user = CustomUser.objects.get(email=sociallogin.user.email)
                sociallogin.connect(request, existing_user)
            except CustomUser.DoesNotExist:
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Sauvegarde l'utilisateur après connexion sociale
        """
        user = super().save_user(request, sociallogin, form)
        
        # Définir les valeurs par défaut pour les utilisateurs sociaux
        if not user.first_name and sociallogin.account.extra_data.get('given_name'):
            user.first_name = sociallogin.account.extra_data.get('given_name')
        
        if not user.last_name and sociallogin.account.extra_data.get('family_name'):
            user.last_name = sociallogin.account.extra_data.get('family_name')
        
        # Les comptes Google sont automatiquement vérifiés
        user.verified = True
        user.is_active = True
        
        # Définir le rôle par défaut
        if not user.role:
            user.role = 'user'
        
        user.save()
        return user
