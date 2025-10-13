from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'status', 'is_active')
    list_filter = ('role', 'status', 'is_active', 'verified')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name', 'profilePicture', 'bio', 'birth_date', 'phone_number')}),
        (_('Account info'), {'fields': ('role', 'status', 'verified', 'is_active')}),
        (_('Permissions'), {'fields': ('groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role', 'is_active')}
        ),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')