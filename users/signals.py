from django.dispatch import receiver
from allauth.account.signals import email_confirmed

@receiver(email_confirmed)
def email_confirmed_handler(sender, request, email_address, **kwargs):
    """
    Met à jour le champ verified du CustomUser quand l'email est confirmé
    """
    user = email_address.user
    if not user.verified:
        user.verified = True
        user.save(update_fields=['verified'])
