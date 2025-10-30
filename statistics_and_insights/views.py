# statistics_and_insights/views.py
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from datetime import timedelta
import json
import time
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings

from .models import UserStatistics, MoodTrend, WeeklyInsight, EntryAnalytics, CustomReport, AIGeneratedReport, AIReportLog
from .analytics_utils import JournalAnalytics, EnhancedJournalAnalytics
from .forms import CustomReportForm
from .ai_service_real import RealAIService
from .gemini_service import GeminiAIService 

@login_required
def dashboard_view(request):
    """Tableau de bord des statistiques"""
    print(f"🔍 DEBUG: User: {request.user}")
    
    create_missing_analytics(request.user)
    update_user_statistics(request.user)
    
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    if user_stats.total_entries == 0:
        update_user_statistics(request.user)
        user_stats.refresh_from_db()
    
    print(f"🔍 DEBUG: UserStats - total_entries: {user_stats.total_entries}")
    
    weekly_insight = None
    try:
        weekly_insight_data = JournalAnalytics.generate_weekly_insights(request.user)
        
        if weekly_insight_data:
            week_start = timezone.now().date() - timedelta(days=7)
            weekly_insight, created = WeeklyInsight.objects.get_or_create(
                user=request.user,
                week_start=week_start,
                defaults={
                    'week_end': timezone.now().date(),
                    'insights': weekly_insight_data.get('insights', {}),
                    'patterns': weekly_insight_data.get('patterns', []),
                    'recommendations': weekly_insight_data.get('recommendations', [])
                }
            )
            print(f"🔍 DEBUG: Weekly insight créé: {weekly_insight}")
        else:
            print("🔍 DEBUG: Aucun insight hebdomadaire généré")
            
    except Exception as e:
        print(f"❌ Erreur génération insights: {e}")
        import traceback
        traceback.print_exc()
        weekly_insight = None
    
    recent_reports = CustomReport.objects.filter(user=request.user)[:2]
    recent_ai_reports = AIGeneratedReport.objects.filter(user=request.user)[:2]
    
    context = {
        'user_stats': user_stats,
        'weekly_insight': weekly_insight,
        'recent_reports': recent_reports,
        'recent_ai_reports': recent_ai_reports,
    }
    
    return render(request, 'statistics_and_insights/dashboard.html', context)

@login_required
def mood_analytics(request):
    """Analyses d'humeur détaillées"""
    mood_trends = MoodTrend.objects.filter(
        user=request.user
    ).order_by('date')[:30]
    
    dates = [trend.date.strftime('%Y-%m-%d') for trend in mood_trends]
    moods = [float(trend.average_mood) for trend in mood_trends]
    
    context = {
        'mood_trends': mood_trends,
        'chart_data': {
            'dates': dates,
            'moods': moods,
        },
        'zipped_chart': list(zip(dates, moods))
    }

    return render(request, 'statistics_and_insights/mood_analytics.html', context)

@login_required
def statistics_api(request):
    """API pour les données statistiques"""
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    data = {
        'total_entries': user_stats.total_entries,
        'current_streak': user_stats.current_streak,
        'longest_streak': user_stats.longest_streak,
        'average_mood': user_stats.average_mood,
        'average_word_count': user_stats.average_word_count,
    }
    
    return JsonResponse(data)

@login_required
def advanced_statistics_api(request):
    """Advanced statistics API with AI insights"""
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    ai_insights = EnhancedJournalAnalytics.generate_comprehensive_insights(request.user, days=30)
    
    data = {
        'basic_stats': {
            'total_entries': user_stats.total_entries,
            'current_streak': user_stats.current_streak,
            'longest_streak': user_stats.longest_streak,
            'average_mood': user_stats.average_mood,
            'average_word_count': user_stats.average_word_count,
            'total_words_written': user_stats.total_words_written,
        },
        'ai_insights': ai_insights,
        'writing_consistency': user_stats.writing_consistency,
        'favorite_topics': user_stats.favorite_topics[:5]
    }
    
    return JsonResponse(data)

@login_required
def real_time_analysis_api(request):
    """Real-time analysis of recent entries"""
    if request.method == 'POST':
        text = request.POST.get('text', '')
        
        ai_sentiment = RealAIService.analyze_sentiment_with_gemini(text)
        
        response_data = {
            'sentiment': {
                'label': ai_sentiment.get('sentiment', 'neutral'),
                'confidence': ai_sentiment.get('confidence', 0.8),
                'explanation': ai_sentiment.get('explanation', ''),
                'model': ai_sentiment.get('model_used', 'gemini')
            },
            'word_count': len(text.split()),
            'reading_time': max(1, len(text.split()) // 200)
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'POST method required'})

# CRUD Operations for Custom Reports
@login_required
def custom_report_list(request):
    """Liste des rapports de l'utilisateur"""
    reports = CustomReport.objects.filter(user=request.user)
    return render(request, 'statistics_and_insights/report_list.html', {
        'reports': reports
    })

@login_required
def custom_report_create(request):
    """Create a new custom report"""
    if request.method == 'POST':
        form = CustomReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            
            try:
                from datetime import date
                days = (report.date_range_end - report.date_range_start).days
                
                report_data = EnhancedJournalAnalytics.generate_comprehensive_insights(
                    request.user,
                    days=min(days, 365)
                )
                
                if report_data:
                    report.data = report_data
                    print("✅ Données IA générées pour le rapport")
                else:
                    report.data = {
                        'period_summary': {
                            'total_entries': 0,
                            'days_analyzed': days,
                            'start_date': str(report.date_range_start),
                            'end_date': str(report.date_range_end)
                        },
                        'error': 'Aucune donnée disponible pour cette période'
                    }
                    print("⚠️ Aucune donnée disponible")
                    
            except Exception as e:
                print(f"❌ Erreur génération rapport: {e}")
                report.data = {'error': f'Erreur de génération: {str(e)}'}
            
            report.save()
            return redirect('statistics_and_insights:report_detail', pk=report.pk)
    else:
        form = CustomReportForm()
    
    return render(request, 'statistics_and_insights/report_form.html', {
        'form': form,
        'title': 'Créer un Rapport Personnalisé'
    })

@login_required
def custom_report_detail(request, pk):
    """View a custom report"""
    report = get_object_or_404(CustomReport, pk=pk, user=request.user)
    return render(request, 'statistics_and_insights/report_detail.html', {
        'report': report
    })

@login_required
def custom_report_update(request, pk):
    """Update a custom report"""
    report = get_object_or_404(CustomReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CustomReportForm(request.POST, instance=report)
        if form.is_valid():
            updated_report = form.save(commit=False)
            if (report.date_range_start != updated_report.date_range_start or 
                report.date_range_end != updated_report.date_range_end):
                days = (updated_report.date_range_end - updated_report.date_range_start).days
                report_data = EnhancedJournalAnalytics.generate_comprehensive_insights(
                    request.user,
                    days=min(days, 365)
                )
                updated_report.data = report_data or {}
            
            updated_report.save()
            return redirect('statistics_and_insights:report_detail', pk=report.pk)
    else:
        form = CustomReportForm(instance=report)
    
    return render(request, 'statistics_and_insights/report_form.html', {
        'form': form,
        'title': 'Modifier le Rapport',
        'report': report
    })

@login_required
def custom_report_delete(request, pk):
    """Suppression définitive d'un rapport"""
    report = get_object_or_404(CustomReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            report_title = report.title
            report.delete()
            
            messages.success(request, f"Le rapport '{report_title}' a été supprimé définitivement.")
            return redirect('statistics_and_insights:report_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('statistics_and_insights:report_detail', pk=report.pk)
    
    return render(request, 'statistics_and_insights/report_confirm_delete.html', {
        'report': report
    })

@login_required
def custom_report_share(request, pk):
    """Share a report (generate shareable link)"""
    report = get_object_or_404(CustomReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        report.is_shared = True
        if not report.share_token:
            report.generate_share_token()
        report.save()
    
    return redirect('statistics_and_insights:report_detail', pk=report.pk)

@login_required
def shared_report_view(request, share_token):
    """View a shared report (no login required)"""
    report = get_object_or_404(CustomReport, share_token=share_token, is_shared=True)
    return render(request, 'statistics_and_insights/shared_report.html', {
        'report': report
    })

# RAPPORTS IA
@login_required
def generate_ai_report(request):
    """Génère un rapport IA automatiquement"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'weekly_auto')
        
        print(f"🔍 Début génération rapport - Type: {report_type}")
        print(f"🔍 User: {request.user}")
        start_time = time.time()
        
        try:
            end_date = timezone.now().date()
            if report_type == 'weekly_auto':
                start_date = end_date - timedelta(days=7)
                title = f"Rapport Hebdomadaire Gemini AI - {end_date}"
                period_name = "hebdomadaire"
            elif report_type == 'monthly_auto':
                start_date = end_date - timedelta(days=30)
                title = f"Rapport Mensuel Gemini AI - {end_date.strftime('%B %Y')}"
                period_name = "mensuel"
            else:
                start_date = end_date - timedelta(days=30)
                title = f"Rapport {report_type.replace('_', ' ').title()} - {end_date}"
                period_name = "personnalisé"
            
            print(f"🔍 Période analysée: {start_date} à {end_date}")
            
            entries_data = EnhancedJournalAnalytics.prepare_data_for_ai(
                request.user, 
                start_date, 
                end_date
            )
            
            print(f"🔍 Données préparées pour analyse:")
            print(f"   - Entrées totales: {entries_data.get('total_entries', 0)}")
            print(f"   - Humeur moyenne: {entries_data.get('average_mood', 0)}")
            
            if entries_data['total_entries'] == 0:
                print("❌ Aucune donnée disponible pour la période")
                
                error_report = AIGeneratedReport.objects.create(
                    user=request.user,
                    title=f"Rapport {period_name} - Données insuffisantes",
                    report_type=report_type,
                    period_start=start_date,
                    period_end=end_date,
                    ai_insights={'error': 'Aucune donnée disponible'},
                    trends_analysis=["Données insuffisantes pour l'analyse"],
                    recommendations=[
                        "Commencez par écrire quelques entrées de journal",
                        "La régularité d'écriture permet de meilleures analyses",
                        "Revenez après avoir écrit quelques entrées"
                    ],
                    psychological_insights=[
                        "Le journal personnel est un outil puissant pour la croissance personnelle",
                        "Chaque entrée construit une meilleure compréhension de soi",
                        "La constance dans l'écriture renforce les bénéfices"
                    ],
                    confidence_score=0.1,
                    ai_model_used='system_expert'
                )
                
                AIReportLog.objects.create(
                    user=request.user,
                    report_type=report_type,
                    status='error',
                    ai_model='no_data',
                    processing_time=time.time() - start_time
                )
                
                return JsonResponse({
                    'success': False,
                    'error': f'Aucune donnée disponible pour la période {period_name}. Écrivez quelques entrées et réessayez.',
                    'report_id': error_report.id
                })
            
            print("🔍 Appel de Gemini AI pour l'analyse...")
            ai_insights = RealAIService.generate_ai_insights_with_gemini(entries_data)
            
            print(f"🔍 Résultats Gemini AI reçus:")
            print(f"   - AI Généré: {ai_insights.get('ai_generated', False)}")
            print(f"   - Score de confiance: {ai_insights.get('confidence_score', 0)}")
            
            is_ai_generated = ai_insights.get('ai_generated', False)
            confidence_score = ai_insights.get('confidence_score', 0.9)
            
            if not is_ai_generated:
                title = title.replace('Gemini AI', 'Système Expert')
            
            report = AIGeneratedReport.objects.create(
                user=request.user,
                title=title,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                ai_insights=ai_insights,
                trends_analysis=ai_insights.get('trends', []),
                recommendations=ai_insights.get('recommendations', []),
                psychological_insights=ai_insights.get('psychological_insights', []),
                confidence_score=confidence_score,
                ai_model_used='gemini' if is_ai_generated else 'system_expert'
            )
            
            processing_time = time.time() - start_time
            AIReportLog.objects.create(
                user=request.user,
                report_type=report_type,
                status='success',
                ai_model='gemini' if is_ai_generated else 'system_expert',
                processing_time=processing_time
            )
            
            if is_ai_generated:
                message = f'Rapport {period_name} généré avec succès par Gemini AI !'
                analysis_type = "Gemini AI"
            else:
                message = f'Analyse {period_name} générée avec succès par notre système expert !'
                analysis_type = "Système Expert d'Analyse"
            
            response_data = {
                'success': True,
                'report_id': report.id,
                'message': message,
                'analysis_type': analysis_type,
                'confidence': f"{int(confidence_score * 100)}%",
                'processing_time': f"{processing_time:.1f}s",
                'entries_analyzed': entries_data['total_entries'],
                'period': f"{start_date} à {end_date}",
                'is_ai_generated': is_ai_generated
            }
            
            print(f"✅ Rapport créé avec ID: {report.id}")
            print(f"⏱️ Temps de traitement: {processing_time:.2f}s")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Erreur lors de la génération du rapport: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            AIReportLog.objects.create(
                user=request.user,
                report_type=report_type,
                status='error',
                ai_model='gemini',
                processing_time=processing_time
            )
            
            try:
                error_report = AIGeneratedReport.objects.create(
                    user=request.user,
                    title=f"Rapport en erreur - {timezone.now().strftime('%Y-%m-%d')}",
                    report_type=report_type,
                    period_start=timezone.now().date() - timedelta(days=7),
                    period_end=timezone.now().date(),
                    ai_insights={'error': error_msg},
                    trends_analysis=["Erreur lors de l'analyse"],
                    recommendations=[
                        "Réessayez plus tard",
                        "Vérifiez votre connexion internet",
                        "Contactez le support si le problème persiste"
                    ],
                    psychological_insights=[
                        "Les analyses peuvent parfois rencontrer des difficultés techniques",
                        "Votre pratique de journalisation reste précieuse",
                        "Revenez pour générer un nouveau rapport ultérieurement"
                    ],
                    confidence_score=0.0,
                    ai_model_used='error'
                )
                
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'report_id': error_report.id,
                    'fallback_created': True
                })
                
            except Exception as create_error:
                print(f"❌ Erreur création rapport de secours: {create_error}")
                return JsonResponse({
                    'success': False,
                    'error': f"{error_msg} (et impossible de créer un rapport de secours)"
                })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée. Utilisez POST.'
    })

@login_required
def ai_reports_list(request):
    """Liste des rapports générés par l'IA"""
    reports = AIGeneratedReport.objects.filter(user=request.user).order_by('-created_at')
    
    stats = {
        'total_reports': reports.count(),
        'ai_generated': reports.filter(confidence_score__gt=0.7).count(),
        'this_week': reports.filter(created_at__gte=timezone.now()-timedelta(days=7)).count()
    }
    
    return render(request, 'statistics_and_insights/ai_reports_list.html', {
        'reports': reports,
        'stats': stats
    })

@login_required 
def ai_report_detail(request, pk):
    """Détail d'un rapport IA"""
    report = get_object_or_404(AIGeneratedReport, pk=pk, user=request.user)
    
    context = {
        'report': report,
        'is_ai_generated': report.confidence_score > 0.7,
        'confidence_percentage': int(report.confidence_score * 100)
    }
    
    return render(request, 'statistics_and_insights/ai_report_detail.html', context)

# BACKOFFICE
@login_required
def backoffice_dashboard(request):
    """Tableau de bord backoffice"""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('statistics_and_insights:dashboard')
    
    print("=== BACKOFFICE DASHBOARD EXECUTED ===")
    
    try:
        from journal.models import Journal
        from users.models import CustomUser
        
        total_users = CustomUser.objects.count()
        
        try:
            total_entries = Journal.objects.count()
        except:
            total_entries = 0
            print("⚠️ Journal model not available")
        
        total_ai_reports = AIGeneratedReport.objects.count()
        
        recent_ai_reports_query = AIGeneratedReport.objects.select_related('user').order_by('-created_at')[:5]
        recent_ai_reports = list(recent_ai_reports_query)
        
        print(f"🔍 Total AI Reports: {total_ai_reports}")
        print(f"🔍 Recent AI Reports: {len(recent_ai_reports)}")
        
        total_logs = AIReportLog.objects.count()
        success_logs = AIReportLog.objects.filter(status='success').count()
        ai_success_rate = (success_logs / total_logs * 100) if total_logs > 0 else 0
        
        ai_generated_count = AIGeneratedReport.objects.filter(confidence_score__gt=0.7).count()
        auto_generated_count = AIGeneratedReport.objects.filter(confidence_score__lte=0.7).count()
        
        recent_logs = list(AIReportLog.objects.select_related('user').order_by('-created_at')[:10])
        
        context = {
            'total_users': total_users,
            'total_entries': total_entries,
            'total_ai_reports': total_ai_reports,
            'ai_success_rate': ai_success_rate,
            'recent_ai_reports': recent_ai_reports,
            'recent_logs': recent_logs,
            'ai_generated_count': ai_generated_count,
            'auto_generated_count': auto_generated_count,
        }
        
        print(f"🔍 Context prepared - recent_ai_reports: {len(context['recent_ai_reports'])}")
        
        return render(request, 'statistics_and_insights/backoffice_dashboard.html', context)
        
    except Exception as e:
        print(f"❌ ERROR in backoffice_dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        return render(request, 'statistics_and_insights/backoffice_dashboard.html', {
            'total_users': 0,
            'total_entries': 0,
            'total_ai_reports': 0,
            'ai_success_rate': 0,
            'recent_ai_reports': [],
            'recent_logs': [],
            'ai_generated_count': 0,
            'auto_generated_count': 0,
        })

@login_required
def backoffice_ai_reports(request):
    """Tous les rapports IA (backoffice)"""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('statistics_and_insights:dashboard')
    
    reports = AIGeneratedReport.objects.select_related('user').order_by('-created_at')
    
    report_type = request.GET.get('type', '')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    ai_generated = request.GET.get('ai_generated', '')
    if ai_generated == 'true':
        reports = reports.filter(confidence_score__gt=0.7)
    elif ai_generated == 'false':
        reports = reports.filter(confidence_score__lte=0.7)
    
    ai_generated_count = AIGeneratedReport.objects.filter(confidence_score__gt=0.7).count()
    auto_generated_count = AIGeneratedReport.objects.filter(confidence_score__lte=0.7).count()
    
    from django.db.models import Avg
    average_confidence = reports.aggregate(avg_confidence=Avg('confidence_score'))['avg_confidence'] or 0
    
    return render(request, 'statistics_and_insights/backoffice_ai_reports.html', {
        'reports': reports,
        'filters': {
            'report_type': report_type,
            'ai_generated': ai_generated
        },
        'ai_generated_count': ai_generated_count,
        'auto_generated_count': auto_generated_count,
        'average_confidence': average_confidence,
    })

@login_required
def backoffice_ai_report_detail(request, pk):
    """Détail d'un rapport IA en backoffice"""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('statistics_and_insights:dashboard')
    
    report = get_object_or_404(AIGeneratedReport, pk=pk)
    
    return render(request, 'statistics_and_insights/backoffice_ai_report_detail.html', {
        'report': report
    })

# FONCTIONS UTILITAIRES
def update_user_statistics(user):
    """Met à jour les statistiques de l'utilisateur"""
    try:
        from journal.models import Journal
        
        user_stats, created = UserStatistics.objects.get_or_create(user=user)
        
        total_entries = Journal.objects.filter(user=user).count()
        print(f"🔍 DEBUG: Total entries found: {total_entries}")
        
        analytics_data = EntryAnalytics.objects.filter(
            user=user
        ).aggregate(
            avg_mood=Avg('mood_score'),
            avg_word_count=Avg('word_count'),
            total_words=Sum('word_count')
        )
        
        print(f"🔍 DEBUG: Analytics data: {analytics_data}")
        
        from django.utils import timezone
        today = timezone.now().date()
        streak = 0
        
        for i in range(30):
            check_date = today - timedelta(days=i)
            has_entry = Journal.objects.filter(
                user=user,
                created_at__date=check_date
            ).exists()
            
            if has_entry:
                streak += 1
            else:
                break
        
        user_stats.total_entries = total_entries
        user_stats.current_streak = streak
        user_stats.average_mood = analytics_data['avg_mood'] or 0.0
        user_stats.average_word_count = analytics_data['avg_word_count'] or 0.0
        user_stats.total_words_written = analytics_data['total_words'] or 0
        user_stats.writing_consistency = user_stats.calculate_consistency()
        
        if streak > user_stats.longest_streak:
            user_stats.longest_streak = streak
        
        user_stats.save()
        print(f"🔍 DEBUG: Stats saved - entries: {user_stats.total_entries}, streak: {user_stats.current_streak}")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour stats: {e}")
        import traceback
        traceback.print_exc()

@login_required
def ai_report_update(request, pk):
    """Modifier un rapport IA dans le backoffice"""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('statistics_and_insights:dashboard')
    
    report = get_object_or_404(AIGeneratedReport, pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        report_type = request.POST.get('report_type')
        confidence_score = request.POST.get('confidence_score')
        
        if title:
            report.title = title
        if report_type:
            report.report_type = report_type
        if confidence_score:
            report.confidence_score = float(confidence_score)
        
        report.save()
        
        messages.success(request, f"Le rapport '{report.title}' a été mis à jour avec succès.")
        return redirect('statistics_and_insights:ai_report_detail', pk=report.pk)
    
    return render(request, 'statistics_and_insights/ai_report_update.html', {
        'report': report
    })

@login_required
def ai_report_delete(request, pk):
    """Supprimer un rapport IA dans le backoffice"""
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('statistics_and_insights:dashboard')
    
    report = get_object_or_404(AIGeneratedReport, pk=pk)
    
    if request.method == 'POST':
        try:
            report_title = report.title
            report.delete()
            
            messages.success(request, f"Le rapport '{report_title}' a été supprimé avec succès.")
            return redirect('statistics_and_insights:ai_reports_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
            return redirect('statistics_and_insights:ai_report_detail', pk=report.pk)
    
    return render(request, 'statistics_and_insights/ai_report_delete.html', {
        'report': report
    })

def create_missing_analytics(user):
    """Create missing analytics for journal entries"""
    from journal.models import Journal
    from .models import EntryAnalytics
    from .analytics_utils import EnhancedJournalAnalytics
    
    try:
        entries_without_analytics = Journal.objects.filter(
            user=user
        ).exclude(
            id__in=EntryAnalytics.objects.values('entry_id')
        )
        
        print(f"🔍 DEBUG: Found {entries_without_analytics.count()} entries without analytics")
        
        for entry in entries_without_analytics:
            print(f"🔍 DEBUG: Creating analytics for entry {entry.id}")
            EnhancedJournalAnalytics.analyze_entry(entry)
            
    except Exception as e:
        print(f"❌ Error creating missing analytics: {e}")

@login_required
def test_gemini(request):
    """Test de connexion à Gemini"""
    try:
        from .gemini_service import GeminiAIService
        gemini = GeminiAIService.get_service()
        result = gemini.test_connection()
        
        return JsonResponse({
            'gemini_test': result,
            'api_configured': bool(getattr(settings, 'GEMINI_API_KEY', None))
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'api_configured': bool(getattr(settings, 'GEMINI_API_KEY', None))
        })

# statistics_and_insights/views.py - Modifier cette fonction

@login_required 
def generate_gemini_report(request):
    """Génère un rapport avec Gemini - Version avec redirection directe"""
    if request.method == 'POST':
        try:
            print("🔍 Début génération rapport Gemini...")
            
            # Préparer les données
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=7)
            
            entries_data = EnhancedJournalAnalytics.prepare_data_for_ai(
                request.user, start_date, end_date
            )
            
            print(f"🔍 Données préparées: {entries_data.get('total_entries', 0)} entrées")
            
            # Vérifier s'il y a des données
            if entries_data.get('total_entries', 0) == 0:
                messages.error(request, 'Aucune donnée disponible pour générer un rapport.')
                return redirect('statistics_and_insights:ai_reports_list')
            
            # Appeler Gemini directement
            print("🔍 Appel de Gemini AI...")
            gemini_service = GeminiAIService.get_service()
            insights = gemini_service.generate_insights(entries_data)
            
            print(f"🔍 Réponse Gemini: {insights.get('ai_generated', False)}")
            
            # Créer le rapport
            report = AIGeneratedReport.objects.create(
                user=request.user,
                title=f"Rapport Gemini - {end_date}",
                report_type='weekly_auto',
                period_start=start_date,
                period_end=end_date,
                ai_insights=insights,
                trends_analysis=insights.get('trends', []),
                recommendations=insights.get('recommendations', []),
                psychological_insights=insights.get('psychological_insights', []),
                confidence_score=insights.get('confidence_score', 0.9),
                ai_model_used=insights.get('model_used', 'gemini')
            )
            
            messages.success(request, 'Rapport Gemini généré avec succès !')
            return redirect('statistics_and_insights:ai_report_detail', pk=report.id)
            
        except Exception as e:
            print(f"❌ Erreur génération rapport Gemini: {e}")
            import traceback
            traceback.print_exc()
            
            messages.error(request, f'Erreur lors de la génération: {str(e)}')
            return redirect('statistics_and_insights:ai_reports_list')
    
    messages.error(request, 'Méthode non autorisée')
    return redirect('statistics_and_insights:ai_reports_list')


@login_required 
def generate_gemini_report_debug(request):
    """Version debug qui accepte GET et POST"""
    if request.method in ['GET', 'POST']:
        try:
            from .gemini_service import GeminiAIService
            from .analytics_utils import EnhancedJournalAnalytics
            
            # Paramètres par défaut ou depuis la requête
            days = int(request.GET.get('days', 7))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            entries_data = EnhancedJournalAnalytics.prepare_data_for_ai(
                request.user, start_date, end_date
            )
            
            if entries_data.get('total_entries', 0) == 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucune donnée disponible',
                    'period': f'{start_date} à {end_date}'
                })
            
            gemini = GeminiAIService.get_service()
            insights = gemini.generate_insights(entries_data)
            
            report = AIGeneratedReport.objects.create(
                user=request.user,
                title=f"Rapport Gemini Debug - {end_date}",
                report_type='weekly_auto',
                period_start=start_date,
                period_end=end_date,
                ai_insights=insights,
                trends_analysis=insights.get('trends', []),
                recommendations=insights.get('recommendations', []),
                psychological_insights=insights.get('psychological_insights', []),
                confidence_score=insights.get('confidence_score', 0.9),
                ai_model_used='gemini-pro'
            )
            
            return JsonResponse({
                'success': True,
                'report_id': report.id,
                'ai_generated': insights.get('ai_generated', False),
                'period': f'{start_date} à {end_date}',
                'entries_analyzed': entries_data.get('total_entries', 0),
                'report_url': f'/statistics/ai-reports/{report.id}/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Méthode non supportée'})

@login_required
def test_gemini_detailed(request):
    """Test détaillé de Gemini"""
    try:
        from .gemini_service import GeminiAIService
        
        # Test de connexion
        gemini = GeminiAIService.get_service()
        test_result = gemini.test_connection()
        
        # Test avec des données réelles
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        entries_data = EnhancedJournalAnalytics.prepare_data_for_ai(
            request.user, start_date, end_date
        )
        
        print(f"🔍 Données pour test: {entries_data}")
        
        if entries_data.get('total_entries', 0) > 0:
            insights = gemini.generate_insights(entries_data)
            return JsonResponse({
                'connection_test': test_result,
                'insights_test': insights,
                'entries_data': entries_data,
                'status': 'success'
            })
        else:
            return JsonResponse({
                'connection_test': test_result,
                'entries_data': entries_data,
                'status': 'no_data'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        })
    