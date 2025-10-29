from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de test pour Statistics & Insights'

    def handle(self, *args, **options):
        from journal.models import Journal
        from statistics_and_insights.models import EntryAnalytics, UserStatistics, MoodTrend, WeeklyInsight

        # Récupérer un utilisateur
        User = get_user_model()
        try:
            user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            self.stdout.write(self.style.SUCCESS('✅ Utilisateur test créé'))

        # Nettoyer les anciennes données
        Journal.objects.filter(user=user).delete()
        EntryAnalytics.objects.filter(user=user).delete()
        UserStatistics.objects.filter(user=user).delete()
        MoodTrend.objects.filter(user=user).delete()
        WeeklyInsight.objects.filter(user=user).delete()

        # Données de test
        entries_data = [
            {
                'title': 'Belle journée ensoleillée',
                'content': "Aujourd'hui a été une journée incroyable. J'ai terminé mon projet avec succès et j'ai reçu des compliments de mon équipe. Le soleil brillait et je me sens vraiment reconnaissant pour tout ce que j'ai accompli.",
                'mood_score': 0.8,
                'sentiment': 'very_positive',
                'word_count': 85,
                'emotions': {'heureux': 3, 'productif': 2, 'gratitude': 1}
            },
            {
                'title': 'Journée stressante au travail',
                'content': "Beaucoup de pression aujourd'hui avec les deadlines. Les réunions se sont enchaînées et je me sens un peu dépassé. J'espère que demain sera plus calme.",
                'mood_score': -0.4,
                'sentiment': 'negative',
                'word_count': 65,
                'emotions': {'stressé': 2, 'anxieux': 1, 'fatigué': 1}
            },
            {
                'title': 'Moment en famille',
                'content': "Dîner en famille ce soir. C'était agréable de passer du temps avec mes proches. Nous avons rigolé et partagé de bons moments. Ces instants simples sont précieux.",
                'mood_score': 0.6,
                'sentiment': 'positive',
                'word_count': 45,
                'emotions': {'heureux': 2, 'calme': 1, 'amour': 1}
            },
            {
                'title': 'Réflexion du matin',
                'content': "Je me suis levé tôt pour méditer. La tranquillité du matin m'aide à clarifier mes pensées. Je me sens prêt à affronter la journée.",
                'mood_score': 0.3,
                'sentiment': 'positive',
                'word_count': 35,
                'emotions': {'calme': 2, 'productif': 1}
            },
            {
                'title': 'Défi technique',
                'content': "J'ai rencontré un bug difficile à résoudre aujourd'hui. C'était frustrant mais j'ai finalement trouvé la solution. J'ai appris beaucoup dans le processus.",
                'mood_score': -0.1,
                'sentiment': 'neutral',
                'word_count': 40,
                'emotions': {'frustré': 1, 'productif': 1, 'apprentissage': 1}
            }
        ]

        # Créer les entrées et analytics
        for i, data in enumerate(entries_data):
            journal = Journal.objects.create(
                user=user,
                title=data['title'],
                description=data['content'],
                created_at=timezone.now() - timedelta(days=i*2)
            )
            
            EntryAnalytics.objects.create(
                user=user,
                entry=journal,
                mood_score=data['mood_score'],
                sentiment=data['sentiment'],
                word_count=data['word_count'],
                emotions=data['emotions']
            )
            self.stdout.write(f"✅ Entrée créée: {journal.title}")

        # Créer des tendances d'humeur pour les 30 derniers jours
        today = timezone.now().date()
        for i in range(30):
            date = today - timedelta(days=29-i)
            avg_mood = random.uniform(-0.5, 0.8)
            entry_count = random.randint(0, 3)
            
            MoodTrend.objects.create(
                user=user,
                date=date,
                average_mood=round(avg_mood, 2),
                entry_count=entry_count
            )

        # Créer/mettre à jour les statistiques utilisateur
        user_stats, created = UserStatistics.objects.get_or_create(user=user)
        user_stats.total_entries = Journal.objects.filter(user=user).count()
        user_stats.current_streak = 5
        user_stats.longest_streak = 10
        
        analytics_data = EntryAnalytics.objects.filter(user=user).aggregate(
            avg_mood=Avg('mood_score'),
            avg_word_count=Avg('word_count')
        )
        
        user_stats.average_mood = analytics_data['avg_mood'] or 0
        user_stats.average_word_count = analytics_data['avg_word_count'] or 0
        user_stats.save()

        # Créer un insight hebdomadaire
        week_start = today - timedelta(days=7)
        week_end = today
        
        WeeklyInsight.objects.create(
            user=user,
            week_start=week_start,
            week_end=week_end,
            insights={
                'total_entries': 3,
                'average_mood': 0.4,
                'average_word_count': 55,
                'most_active_day': 'Lundi',
                'mood_trend': 'amélioration'
            },
            patterns=[
                "Écriture plus productive les matins",
                "Humeur positive après l'exercice",
                "Plus d'entrées les jours de semaine"
            ],
            recommendations=[
                "💆 Essayez d'écrire le matin pour plus de productivité",
                "🌞 Profitez des jours ensoleillés pour améliorer votre humeur",
                "📖 Continuez votre excellente habitude d'écriture"
            ]
        )

        self.stdout.write(self.style.SUCCESS('\n' + "="*50))
        self.stdout.write(self.style.SUCCESS('✅ DONNÉES DE TEST CRÉÉES AVEC SUCCÈS!'))
        self.stdout.write(self.style.SUCCESS("="*50))
        self.stdout.write(self.style.SUCCESS(f"👤 Utilisateur: {user.username}"))
        self.stdout.write(self.style.SUCCESS(f"📝 Entrées créées: {user_stats.total_entries}"))
        self.stdout.write(self.style.SUCCESS(f"📊 Statistiques mises à jour"))
        self.stdout.write(self.style.SUCCESS(f"📈 Tendances d'humeur: 30 jours"))
        self.stdout.write(self.style.SUCCESS(f"💡 Insights hebdomadaires: 1 créé"))
        self.stdout.write(self.style.SUCCESS("\n🌐 Accédez à: http://127.0.0.1:8000/statistics-and-insights/"))