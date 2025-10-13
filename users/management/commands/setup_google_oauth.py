from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Configure Google OAuth application'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=str, help='Google OAuth Client ID')
        parser.add_argument('--client-secret', type=str, help='Google OAuth Client Secret')

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    'Veuillez fournir --client-id et --client-secret\n'
                    'Exemple: python manage.py setup_google_oauth --client-id="your-client-id" --client-secret="your-secret"'
                )
            )
            return

        # Créer ou mettre à jour le site
        site, created = Site.objects.get_or_create(
            domain='127.0.0.1:8000',
            defaults={'name': 'AI Personal Journal Local'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Site créé: {site.domain}')
            )

        # Créer ou mettre à jour l'application Google OAuth
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            # Mettre à jour si elle existe déjà
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            self.stdout.write(
                self.style.SUCCESS('Application Google OAuth mise à jour')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Application Google OAuth créée')
            )

        # Associer l'application au site
        google_app.sites.add(site)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Configuration terminée!\n'
                f'Site: {site.domain}\n'
                f'Application: {google_app.name}\n'
                f'Client ID: {client_id[:20]}...\n'
                f'Vous pouvez maintenant tester l\'authentification Google sur /accounts/login/'
            )
        )
