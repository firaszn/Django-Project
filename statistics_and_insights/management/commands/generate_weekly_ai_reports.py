from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from statistics_and_insights.ai_service_real import RealAIService
from statistics_and_insights.models import AIGeneratedReport, AIReportLog
from statistics_and_insights.analytics_utils import EnhancedJournalAnalytics

class Command(BaseCommand):
    help = 'Génère automatiquement les rapports IA hebdomadaires pour tous les utilisateurs actifs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=str,
            help='Liste d\'emails d\'utilisateurs spécifiques (séparés par des virgules)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule la génération sans créer de rapports'
        )
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        # Déterminer quels utilisateurs traiter
        if options['users']:
            user_emails = [email.strip() for email in options['users'].split(',')]
            users = User.objects.filter(email__in=user_emails, is_active=True)
        else:
            # Tous les utilisateurs actifs avec des entrées récentes
            from journal.models import Journal
            recent_date = timezone.now() - timedelta(days=8)
            users_with_entries = Journal.objects.filter(
                created_at__gte=recent_date
            ).values_list('user', flat=True).distinct()
            users = User.objects.filter(id__in=users_with_entries, is_active=True)
        
        self.stdout.write(f"📊 Génération de rapports IA pour {users.count()} utilisateur(s)")
        
        for user in users:
            try:
                self.stdout.write(f"\n👤 Traitement de {user.username}...")
                
                if options['dry_run']:
                    self.stdout.write(self.style.WARNING("   DRY RUN - Aucun rapport créé"))
                    continue
                
                # Préparer les données
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=7)
                
                entries_data = EnhancedJournalAnalytics.prepare_data_for_ai(user, start_date, end_date)
                
                if entries_data['total_entries'] == 0:
                    self.stdout.write(self.style.WARNING("   ❌ Aucune donnée récente"))
                    continue
                
                # Générer le rapport IA
                ai_insights = RealAIService.generate_ai_insights_with_huggingface(entries_data)
                
                # Créer le rapport
                report = AIGeneratedReport.objects.create(
                    user=user,
                    title=f"Rapport Hebdomadaire IA - {end_date}",
                    report_type='weekly_auto',
                    period_start=start_date,
                    period_end=end_date,
                    ai_insights=ai_insights,
                    trends_analysis=ai_insights.get('trends', []),
                    recommendations=ai_insights.get('recommendations', []),
                    psychological_insights=ai_insights.get('psychological_insights', []),
                    confidence_score=0.8 if ai_insights.get('ai_generated') else 0.6
                )
                
                # Logger
                AIReportLog.objects.create(
                    user=user,
                    report_type='weekly_auto',
                    status='success',
                    ai_model='huggingface',
                    processing_time=0  # Simplifié pour la commande
                )
                
                self.stdout.write(self.style.SUCCESS(f"   ✅ Rapport créé: #{report.id}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erreur: {str(e)}"))
                AIReportLog.objects.create(
                    user=user,
                    report_type='weekly_auto',
                    status='error',
                    ai_model='huggingface',
                    processing_time=0
                )
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Génération terminée !"))