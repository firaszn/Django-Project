from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from .models import UserStatistics, MoodTrend, WeeklyInsight, EntryAnalytics
from .analytics_utils import JournalAnalytics

@login_required
def dashboard_view(request):
    """Tableau de bord des statistiques"""
    print(f"🔍 DEBUG: User: {request.user}")
    
    user_stats, created = UserStatistics.objects.get_or_create(user=request.user)
    print(f"🔍 DEBUG: UserStats - total_entries: {user_stats.total_entries}, created: {created}")
    
    # Mettre à jour les statistiques
    update_user_statistics(request.user)
    
    # Recharger les stats après mise à jour
    user_stats.refresh_from_db()
    print(f"🔍 DEBUG: After update - total_entries: {user_stats.total_entries}")
    
    # Générer les insights
    weekly_insight = JournalAnalytics.generate_weekly_insights(request.user)
    print(f"🔍 DEBUG: Weekly insight: {weekly_insight}")
    
    context = {
        'user_stats': user_stats,
        'weekly_insight': weekly_insight,
    }
    
    return render(request, 'statistics_and_insights/dashboard.html', context)

@login_required
def mood_analytics(request):
    """Analyses d'humeur détaillées"""
    # Récupérer les données d'humeur réelles
    mood_trends = MoodTrend.objects.filter(
        user=request.user
    ).order_by('date')[:30]  # 30 derniers jours
    
    # Préparer les données pour le graphique
    dates = [trend.date.strftime('%Y-%m-%d') for trend in mood_trends]
    moods = [float(trend.average_mood) for trend in mood_trends]
    
    context = {
        'mood_trends': mood_trends,
        'chart_data': {
            'dates': dates,
            'moods': moods,
        }
    }

    # Provide zipped pairs for templates (avoid using a non-existent 'zip' filter)
    context['zipped_chart'] = list(zip(dates, moods))

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

# Fonction utilitaire pour mettre à jour les statistiques
def update_user_statistics(user):
    """Met à jour les statistiques de l'utilisateur"""
    try:
        from journal.models import Journal
        
        user_stats, created = UserStatistics.objects.get_or_create(user=user)
        
        # Compter les entrées
        total_entries = Journal.objects.filter(user=user).count()
        print(f"🔍 DEBUG: Total entries found: {total_entries}")
        
        # CORRECTION : Filtrer par user directement, pas par entry__user
        analytics_data = EntryAnalytics.objects.filter(
            user=user  # ← CORRECTION ICI
        ).aggregate(
            avg_mood=Avg('mood_score'),
            avg_word_count=Avg('word_count')
        )
        
        print(f"🔍 DEBUG: Analytics data: {analytics_data}")
        
        # Calculer la série (streak)
        from django.utils import timezone
        today = timezone.now().date()
        streak = 0
        
        # Vérifier les 30 derniers jours pour le streak
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
        
        # Mettre à jour les statistiques
        user_stats.total_entries = total_entries
        user_stats.current_streak = streak
        user_stats.average_mood = analytics_data['avg_mood'] or 0.0
        user_stats.average_word_count = analytics_data['avg_word_count'] or 0.0
        
        if streak > user_stats.longest_streak:
            user_stats.longest_streak = streak
        
        user_stats.save()
        print(f"🔍 DEBUG: Stats saved - entries: {user_stats.total_entries}, streak: {user_stats.current_streak}")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour stats: {e}")
        import traceback
        traceback.print_exc()