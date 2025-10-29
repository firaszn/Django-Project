from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm, LoginForm
from .models import CustomUser

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
    first_name = forms.CharField(max_length=30, label=_('First Name'),
                               widget=forms.TextInput(attrs={'placeholder': _('First Name')}))
    last_name = forms.CharField(max_length=30, label=_('Last Name'),
                              widget=forms.TextInput(attrs={'placeholder': _('Last Name')}))
    phone_number = forms.CharField(max_length=15, label=_('Phone Number'), required=False,
                                 widget=forms.TextInput(attrs={'placeholder': _('Phone Number')}))
    birth_date = forms.DateField(label=_('Date of Birth'), required=True,
                               widget=forms.DateInput(attrs={
                                   'type': 'date',
                                   'placeholder': _('Date of Birth'),
                                   'class': 'form-control'
                               }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.birth_date = self.cleaned_data['birth_date']
        user.save()
        return user

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

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
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
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
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        # Changer le mot de passe si fourni
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        return user


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
        new_pin = cleaned_data.get('new_pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        remove_pin = cleaned_data.get('remove_pin')

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

        # Handle PIN removal or set
        if self.cleaned_data.get('remove_pin'):
            user.set_journal_pin(None)
        else:
            new_pin = self.cleaned_data.get('new_pin')
            if new_pin:
                # Use model helper to set hashed PIN
                user.set_journal_pin(new_pin)

        # Password handling already done by earlier save logic
        if commit:
            user.save()
        return user