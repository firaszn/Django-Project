from django.dispatch import receiver
from allauth.account.signals import email_confirmed

from django.db.models.signals import post_save
from django.conf import settings
from .models import UserProfile

@receiver(email_confirmed)
def email_confirmed_handler(sender, request, email_address, **kwargs):
    """
    Met à jour le champ verified du CustomUser quand l'email est confirmé
    """
    user = email_address.user
    if not user.verified:
        user.verified = True
        user.save(update_fields=['verified'])



@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Automatically save UserProfile when User is saved"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)