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