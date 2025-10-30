from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from reminder_and_goals.services.ai_goal_recommender import generate_suggestions_for_user


class Command(BaseCommand):
    help = 'Generate AI goal suggestions from recent journals for a user or all users'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--email', type=str, help='User email to generate suggestions for')
        parser.add_argument('--limit', type=int, default=20)
        parser.add_argument('--max', type=int, default=5)

    def handle(self, *args, **options):
        User = get_user_model()
        if options.get('email'):
            users = User.objects.filter(email=options['email'])
        else:
            users = User.objects.all()

        total = 0
        for user in users:
            created = generate_suggestions_for_user(user, limit=options['limit'], max_suggestions=options['max'])
            total += len(created)
            self.stdout.write(self.style.SUCCESS(f"Generated {len(created)} suggestions for {user.email}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Total suggestions created: {total}"))


