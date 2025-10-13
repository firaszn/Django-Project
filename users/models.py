from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    # Attributs du diagramme (userid est géré automatiquement par Django)
    username = models.CharField(_('username'), max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    password = models.CharField(_('password'), max_length=128)  # Django gère déjà le hash
    status = models.CharField(_('status'), max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending')
    ])
    # Note: date_joined et last_login sont déjà fournis par AbstractUser
    profilePicture = models.ImageField(_('profile picture'), upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    
    # Champs supplémentaires pour la fonctionnalité
    first_name = models.CharField(_('first name'), max_length=150, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    
    # Additional fields for user preferences
    verified = models.BooleanField(_('verified'), default=False, help_text=_('Indicates if the user has verified their email address'))
    
    # Role field
    role = models.CharField(_('role'), max_length=10, default='user', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ])
    
    # Make email the primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def save(self, *args, **kwargs):
        """
        Synchronise is_staff et is_superuser avec le champ role
        Le champ role est la source de vérité
        Génère automatiquement le username depuis first_name et last_name
        """
        # Synchroniser role avec is_staff et is_superuser
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        
        # Générer username depuis first_name et last_name
        if self.first_name and self.last_name:
            base_username = f"{self.first_name} {self.last_name}".strip()
            
            # Si c'est une nouvelle création ou si le username actuel est vide
            if not self.pk or not self.username or self.username == self.email.split('@')[0]:
                self.username = base_username
                
                # Vérifier l'unicité et ajouter un numéro si nécessaire
                counter = 1
                original_username = self.username
                while CustomUser.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                    self.username = f"{original_username}{counter}"
                    counter += 1
        
        super().save(*args, **kwargs)