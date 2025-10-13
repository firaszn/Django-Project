from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Update usernames to "FirstName LastName" format'

    def handle(self, *args, **options):
        users = CustomUser.objects.all().order_by('id')
        username_counts = {}
        updated_count = 0

        for user in users:
            if user.first_name and user.last_name:
                base_username = f"{user.first_name} {user.last_name}".strip()
                
                # Compter combien de fois ce nom apparaît
                if base_username in username_counts:
                    username_counts[base_username] += 1
                    new_username = f"{base_username}{username_counts[base_username]}"
                else:
                    username_counts[base_username] = 0
                    new_username = base_username
                
                # Mettre à jour le username avec une requête directe pour bypasser le save()
                if user.username != new_username:
                    CustomUser.objects.filter(pk=user.pk).update(username=new_username)
                    self.stdout.write(self.style.SUCCESS(f'✓ Updated: {user.email} -> {new_username}'))
                    updated_count += 1
                else:
                    self.stdout.write(f'  Already correct: {user.email} -> {new_username}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal users updated: {updated_count}/{len(users)}'))

