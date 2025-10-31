from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from django.contrib.auth.hashers import make_password, check_password

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
    # Hashed 4-digit PIN used to unlock hidden journals. Use helper methods to set/check.
    journal_pin = models.CharField(_('journal pin'), max_length=128, null=True, blank=True,
                                   help_text=_('Hashed 4-digit PIN for accessing hidden journals'))
    
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


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # This will point to your CustomUser
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Apple Reminders Integration Fields
    apple_username = models.EmailField(blank=True, null=True, verbose_name=_('Apple ID'))
    encrypted_apple_password = models.BinaryField(blank=True, null=True)
    is_apple_connected = models.BooleanField(default=False, verbose_name=_('Connected to Apple Reminders'))
    
    # Additional profile fields that don't belong in the main User model
    timezone = models.CharField(max_length=50, default='UTC', verbose_name=_('Timezone'))
    language = models.CharField(max_length=10, default='en', verbose_name=_('Language'))
    notification_preferences = models.JSONField(
        default=dict,
        verbose_name=_('Notification Preferences'),
        help_text=_('User preferences for notifications')
    )
    
    # CalDAV specific fields
    apple_calendar_id = models.CharField(max_length=255, blank=True, null=True)
    last_apple_sync = models.DateTimeField(blank=True, null=True)

    # Rappels via Shortcut webhook
    reminders_webhook_url = models.URLField(blank=True, null=True)
    reminders_webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"Profile for {self.user.email}"

    def set_apple_password(self, password):
        """Encrypt and store Apple password"""
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY not set in settings")
        
        fernet = Fernet(settings.ENCRYPTION_KEY)
        self.encrypted_apple_password = fernet.encrypt(password.encode())
        self.is_apple_connected = True

    def get_apple_password(self):
        """Decrypt and return Apple password"""
        if not self.encrypted_apple_password or not settings.ENCRYPTION_KEY:
            return None
        
        fernet = Fernet(settings.ENCRYPTION_KEY)
        try:
            return fernet.decrypt(self.encrypted_apple_password).decode()
        except:
            return None

    def has_apple_credentials(self):
        """Check if user has valid Apple credentials"""
        return bool(self.apple_username and self.encrypted_apple_password and self.is_apple_connected)

    def disconnect_apple(self):
        """Disconnect Apple integration"""
        self.apple_username = None
        self.encrypted_apple_password = None
        self.is_apple_connected = False
        self.apple_calendar_id = None
        self.save()
    def set_journal_pin(self, raw_pin: str):
        """Set a 4-digit numeric PIN for accessing hidden journals. Stores a hashed value."""
        # The actual storage for the hashed PIN lives on the related CustomUser
        # (field `journal_pin`). Update that field instead to avoid DB schema changes.
        if raw_pin is None or raw_pin == '':
            # clear pin
            self.user.journal_pin = None
        else:
            # Expecting exactly 4 digits
            self.user.journal_pin = make_password(raw_pin)
        # Persist the change to the user record
        try:
            self.user.save(update_fields=['journal_pin'])
        except Exception:
            # Fallback to full save if update_fields isn't supported
            self.user.save()

    def check_journal_pin(self, raw_pin: str) -> bool:
        """Return True if raw_pin matches the stored hashed journal PIN."""
        # The hashed PIN is stored on the related user model
        stored = getattr(self.user, 'journal_pin', None)
        if not stored:
            return False
        return check_password(raw_pin, stored)
