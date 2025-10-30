from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm, LoginForm
from .models import CustomUser
from django.conf import settings
import requests

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name')

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30, 
        label=_('First Name'),
        widget=forms.TextInput(attrs={'placeholder': _('First Name'), 'required': False}),
        help_text=_('Required. Letters only, maximum 30 characters.')
    )
    last_name = forms.CharField(
        max_length=30, 
        label=_('Last Name'),
        widget=forms.TextInput(attrs={'placeholder': _('Last Name'), 'required': False}),
        help_text=_('Required. Letters only, maximum 30 characters.')
    )
    phone_number = forms.CharField(
        max_length=15, 
        label=_('Phone Number'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Phone Number'), 'required': False}),
        help_text=_('Optional. Format: +1234567890 or 0123456789')
    )
    birth_date = forms.DateField(
        label=_('Date of Birth'),
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': _('Date of Birth'),
            'class': 'form-control',
            'required': False
        }),
        help_text=_('You must be at least 13 years old to register.')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # Désactiver la validation HTML5 pour laisser Django gérer la validation
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['required'] = False
        
        # Améliorer les messages d'erreur pour les champs de mot de passe
        if 'password1' in self.fields:
            self.fields['password1'].help_text = _('Your password must contain at least 8 characters.')
        if 'password2' in self.fields:
            self.fields['password2'].help_text = _('Enter the same password as before, for verification.')
        
        # Ajouter des classes CSS pour les erreurs
        for field_name, field in self.fields.items():
            field.error_messages = {
                'required': _('This field is required.'),
                'invalid': _('Enter a valid Email.'),
            }
    
    def clean_first_name(self):
        """Validation du prénom"""
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError(_('First name is required.'))
        
        # Vérifier que ce n'est pas juste des espaces
        if not first_name.strip():
            raise forms.ValidationError(_('First name cannot be only spaces.'))
        
        # Vérifier la longueur minimale
        if len(first_name.strip()) < 2:
            raise forms.ValidationError(_('First name must be at least 2 characters long.'))
        
        # Vérifier que ce sont des lettres (et espaces/apostrophes pour les noms composés)
        if not all(c.isalpha() or c in [" ", "'", "-"] for c in first_name):
            raise forms.ValidationError(_('First name should only contain letters, spaces, hyphens and apostrophes.'))
        
        return first_name.strip().title()
    
    def clean_last_name(self):
        """Validation du nom de famille"""
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError(_('Last name is required.'))
        
        # Vérifier que ce n'est pas juste des espaces
        if not last_name.strip():
            raise forms.ValidationError(_('Last name cannot be only spaces.'))
        
        # Vérifier la longueur minimale
        if len(last_name.strip()) < 2:
            raise forms.ValidationError(_('Last name must be at least 2 characters long.'))
        
        # Vérifier que ce sont des lettres
        if not all(c.isalpha() or c in [" ", "'", "-"] for c in last_name):
            raise forms.ValidationError(_('Last name should only contain letters, spaces, hyphens and apostrophes.'))
        
        return last_name.strip().title()
    
    def clean_phone_number(self):
        """Validation du numéro de téléphone"""
        phone_number = self.cleaned_data.get('phone_number')
        
        # C'est optionnel, donc si vide on retourne
        if not phone_number:
            return phone_number
        
        # Nettoyer le numéro (enlever espaces, tirets, etc.)
        cleaned_phone = ''.join(c for c in phone_number if c.isdigit() or c in ['+', '(', ')', '-'])
        
        # Vérifier la longueur minimale
        if len(cleaned_phone.replace('+', '').replace('(', '').replace(')', '').replace('-', '')) < 8:
            raise forms.ValidationError(_('Phone number must contain at least 8 digits.'))
        
        # Vérifier que ça ne contient que des chiffres et quelques caractères autorisés
        if not all(c.isdigit() or c in ['+', '(', ')', '-', ' '] for c in phone_number):
            raise forms.ValidationError(_('Phone number can only contain digits and these characters: + ( ) -'))
        
        return cleaned_phone
    
    def clean_birth_date(self):
        """Validation de la date de naissance"""
        from datetime import date
        birth_date = self.cleaned_data.get('birth_date')
        
        if not birth_date:
            raise forms.ValidationError(_('Birth date is required.'))
        
        # Vérifier que la personne a au moins 13 ans
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        if age < 13:
            raise forms.ValidationError(_('You must be at least 13 years old to register.'))
        
        # Vérifier que la date n'est pas dans le futur
        if birth_date > today:
            raise forms.ValidationError(_('Birth date cannot be in the future.'))
        
        # Vérifier que la personne n'a pas plus de 150 ans (validation raisonnable)
        if age > 150:
            raise forms.ValidationError(_('Please enter a valid birth date.'))
        
        return birth_date
    
    def clean_email(self):
        """Validation améliorée de l'email"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise forms.ValidationError(_('Email is required.'))
        
        email = email.lower()
        
        # Vérifier le format de base de l'email
        if '@' not in email or '.' not in email.split('@')[1]:
            raise forms.ValidationError(_('Please enter a valid email address.'))
        
        # Vérifier si l'email existe déjà dans la base de données
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Vérifier si l'email existe déjà (pour signup, on ne vérifie pas si c'est l'utilisateur actuel)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email address is already registered. Please use a different email or sign in.'))
        
        # Vérifier les emails temporaires/suspects
        suspicious_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'fakeinbox.com'
        ]
        
        email_domain = email.split('@')[1].lower() if '@' in email else ''
        
        if any(domain in email_domain for domain in suspicious_domains):
            raise forms.ValidationError(_('Please use a valid email address. Temporary email addresses are not allowed.'))
        
        # Vérifier les patterns suspects
        username_part = email.split('@')[0] if '@' in email else ''
        
        if username_part.startswith('test') or username_part.startswith('temp'):
            raise forms.ValidationError(_('Please use a valid email address.'))
        
        return email
    
    def clean_password1(self):
        """Validation améliorée du mot de passe"""
        password1 = self.cleaned_data.get('password1')
        
        if not password1:
            raise forms.ValidationError(_('Password is required.'))
        
        # Vérifier la longueur
        if len(password1) < 8:
            raise forms.ValidationError(_('Password must be at least 8 characters long.'))
        
        # Vérifier la complexité (au moins une lettre et un chiffre)
        has_letter = any(c.isalpha() for c in password1)
        has_digit = any(c.isdigit() for c in password1)
        
        if not (has_letter and has_digit):
            raise forms.ValidationError(_('Password must contain at least one letter and one number.'))
        
        # Vérifier que ce n'est pas un mot de passe trop commun
        common_passwords = ['password', 'password123', '12345678', 'qwerty123', 'admin123']
        if password1.lower() in common_passwords:
            raise forms.ValidationError(_('This password is too common. Please choose a stronger password.'))
        
        return password1
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérifier que first_name et last_name ne sont pas identiques
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        if first_name and last_name and first_name == last_name:
            raise forms.ValidationError(_('First name and last name cannot be identical.'))
        
        return cleaned_data
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.birth_date = self.cleaned_data['birth_date']
        user.save()
        return user

class CustomLoginForm(LoginForm):
    recaptcha_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        """Validate reCAPTCHA token"""
        cleaned_data = super().clean()
        recaptcha_token = cleaned_data.get('recaptcha_token')
        
        # Ne pas valider reCAPTCHA si on est sur Render (les clés locales ne fonctionnent pas)
        import os
        is_on_render = os.environ.get('RENDER_EXTERNAL_HOSTNAME') is not None
        
        # Only validate if RECAPTCHA is configured and not on Render
        if not is_on_render and settings.RECAPTCHA_SECRET_KEY and settings.RECAPTCHA_SITE_KEY:
            if not recaptcha_token:
                raise forms.ValidationError(_('Please complete the reCAPTCHA verification.'))
            
            # Verify the token with Google
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': recaptcha_token
            }
            
            try:
                response = requests.post(verify_url, data=data, timeout=5)
                result = response.json()
                
                if not result.get('success'):
                    raise forms.ValidationError(_('reCAPTCHA verification failed. Please try again.'))
            except requests.exceptions.RequestException:
                # If there's a network error, we'll allow the login to proceed
                # but could also raise an error if you want stricter validation
                pass
        
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    # Champs de mot de passe optionnels
    current_password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if not changing'}),
        required=False,
        help_text=_('Enter your current password to change your password')
    )
    new_password = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if not changing'}),
        required=False,
        help_text=_('Minimum 8 characters')
    )
    confirm_password = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if not changing'}),
        required=False
    )
    
    class Meta:
        model = CustomUser
        fields = ['profilePicture', 'bio', 'birth_date', 'phone_number']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': _('Tell us about yourself...')}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone number')}),
        }
        labels = {
            'profilePicture': _('Profile Picture'),
            'bio': _('Bio'),
            'birth_date': _('Birth Date'),
            'phone_number': _('Phone Number'),
        }
    
    # --- PIN handling for hidden journals ---
    # Add PIN fields dynamically so templates can show them if desired
    new_pin = forms.CharField(
        label=_('Journal PIN (4 digits)'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter 4-digit PIN'}),
        required=False,
        help_text=_('Set a 4-digit numeric PIN to access hidden journals')
    )

    confirm_pin = forms.CharField(
        label=_('Confirm PIN'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm PIN'}),
        required=False
    )

    remove_pin = forms.BooleanField(
        label=_('Remove existing PIN'),
        required=False,
        help_text=_('Check to remove your current journal PIN')
    )

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        new_pin = cleaned_data.get('new_pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        remove_pin = cleaned_data.get('remove_pin')
        
        # Si l'utilisateur veut changer son mot de passe
        if new_password or confirm_password:
            if not current_password:
                raise forms.ValidationError(_('You must enter your current password to change your password.'))
            
            if new_password != confirm_password:
                raise forms.ValidationError(_("The two password fields didn't match."))
            
            if len(new_password) < 8:
                raise forms.ValidationError(_('Password must be at least 8 characters long.'))
            
            # Vérifier le mot de passe actuel
            if not self.instance.check_password(current_password):
                raise forms.ValidationError(_('Your current password is incorrect.'))
        
        # If user asked to remove pin, ignore new_pin/confirm_pin
        if remove_pin:
            return cleaned_data

        if new_pin or confirm_pin:
            if not new_pin or not confirm_pin:
                raise forms.ValidationError(_('Please provide both PIN fields or check Remove PIN.'))
            if new_pin != confirm_pin:
                raise forms.ValidationError(_('The PINs do not match.'))
            if not new_pin.isdigit() or len(new_pin) != 4:
                raise forms.ValidationError(_('PIN must be exactly 4 digits.'))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        # Changer le mot de passe si fourni
        if new_password:
            user.set_password(new_password)

        # Handle PIN removal or set
        if self.cleaned_data.get('remove_pin'):
            user.set_journal_pin(None)
        else:
            new_pin = self.cleaned_data.get('new_pin')
            if new_pin:
                # Use model helper to set hashed PIN
                user.set_journal_pin(new_pin)

        if commit:
            user.save()
        return user