from datetime import datetime, timedelta
from collections import Counter
from django.utils import timezone
from django.db.models import Avg, Count, Sum
import json
from .ai_service_real import RealAIService

class JournalAnalytics:
    @staticmethod
    def analyze_sentiment(text):
        """Analyse le sentiment du texte"""
        positive_words = {
            'heureux', 'heureuse', 'content', 'contente', 'joyeux', 'joyeuse',
            'bon', 'bonne', 'génial', 'super', 'excellent', 'parfait',
            'réussi', 'fier', 'fière', 'satisfait', 'satisfaite', 'aimer',
            'adorer', 'plaisir', 'succès', 'victoire', 'progrès'
        }
        
        negative_words = {
            'triste', 'malheureux', 'malheureuse', 'déçu', 'déçue',
            'mauvais', 'mauvaise', 'terrible', 'horrible', 'stressé',
            'stressée', 'anxieux', 'anxieuse', 'inquiet', 'inquiète',
            'colère', 'fâché', 'fâchée', 'fatigué', 'fatiguée', 'difficile',
            'problème', 'échec', 'rate', 'échoué'
        }
        
        words = text.lower().split()
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        total_words = len(words)
        
        if total_words == 0:
            return 0, 'neutral'
        
        sentiment_score = (pos_count - neg_count) / total_words
        
        if sentiment_score > 0.1:
            sentiment = 'positive'
        elif sentiment_score > 0.05:
            sentiment = 'positive'
        elif sentiment_score < -0.1:
            sentiment = 'negative'
        elif sentiment_score < -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        return sentiment_score, sentiment

    @staticmethod
    def detect_emotions(text):
        """Détecte les émotions dans le texte"""
        emotion_keywords = {
            'heureux': {'heureux', 'heureuse', 'content', 'contente', 'joyeux', 'joyeuse', 'sourire', 'souriant'},
            'triste': {'triste', 'malheureux', 'malheureuse', 'pleurer', 'déprimé', 'déprimée'},
            'anxieux': {'anxieux', 'anxieuse', 'stressé', 'stressée', 'inquiet', 'inquiète', 'nerveux', 'nerveuse'},
            'en colère': {'colère', 'fâché', 'fâchée', 'énervé', 'énervée', 'frustré', 'frustrée'},
            'calme': {'calme', 'paisible', 'serein', 'sereine', 'tranquille', 'relax', 'détendu', 'détendue'},
            'productif': {'productif', 'productive', 'efficace', 'accompli', 'réussi', 'fier', 'fière', 'succès'},
            'fatigué': {'fatigué', 'fatiguée', 'épuisé', 'épuisée', 'épuisement', 'sommeil', 'dormir'},
        }
        
        words = set(text.lower().split())
        emotions = {}
        
        for emotion, keywords in emotion_keywords.items():
            matches = keywords.intersection(words)
            if matches:
                emotions[emotion] = len(matches)
        
        return emotions

    @staticmethod
    def generate_weekly_insights(user):
        """Génère des insights hebdomadaires - VERSION CORRIGÉE"""
        from datetime import timedelta
        from django.utils import timezone
        from collections import Counter
        from .models import EntryAnalytics
        
        print(f"🔍 GENERATE_WEEKLY_INSIGHTS pour {user.username}")
        
        week_ago = timezone.now() - timedelta(days=7)
        
        try:
            # 1. Récupérer les entrées récentes avec leurs analytics
            from journal.models import Journal
            
            recent_entries = Journal.objects.filter(
                user=user,
                created_at__gte=week_ago
            )
            
            print(f"🔍 Entrées récentes trouvées: {recent_entries.count()}")
            
            # 2. Récupérer les analytics associés
            entries_with_analytics = []
            emotions_counter = Counter()
            mood_scores = []
            total_words = 0
            
            for entry in recent_entries:
                try:
                    analytics = EntryAnalytics.objects.get(entry=entry)
                    entries_with_analytics.append((entry, analytics))
                    emotions_counter.update(analytics.emotions)
                    if analytics.mood_score is not None:
                        mood_scores.append(analytics.mood_score)
                    total_words += analytics.word_count
                    print(f"✅ Analytics utilisés pour: {entry.title}")
                except EntryAnalytics.DoesNotExist:
                    print(f"❌ Analytics manquants pour: {entry.title}")
                    continue
            
            print(f"🔍 Entrées avec analytics valides: {len(entries_with_analytics)}")
            
            # 3. Si pas assez de données, retourner None
            if len(entries_with_analytics) < 1:
                print("❌ Données insuffisantes pour générer des insights")
                return None
            
            # 4. Calculer les statistiques
            avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
            avg_word_count = total_words / len(entries_with_analytics) if entries_with_analytics else 0
            
            print(f"📊 Stats calculées - Humeur: {avg_mood:.2f}, Mots: {avg_word_count:.0f}")
            
            # 5. Générer les recommandations basées sur les données réelles
            recommendations = []
            most_common_emotion = emotions_counter.most_common(1)
            
            if most_common_emotion:
                emotion, count = most_common_emotion[0]
                if emotion == 'anxieux' and count > 1:
                    recommendations.append("💆 Essayez des exercices de respiration pour gérer le stress")
                elif emotion == 'triste' and count > 1:
                    recommendations.append("🌞 Prenez le temps de faire des activités qui vous plaisent")
                elif emotion == 'heureux' and count > 1:
                    recommendations.append("🎉 Excellent ! Continuez à cultiver cette positivité")
            
            # Recommandations basées sur l'humeur moyenne
            if avg_mood < -0.1:
                recommendations.append("💝 Prenez soin de vous cette semaine")
            elif avg_mood > 0.2:
                recommendations.append("🌟 Profitez de cette énergie positive")
            
            # Recommandations basées sur la longueur des entrées
            if avg_word_count < 50:
                recommendations.append("📝 Essayez de développer un peu plus vos pensées")
            elif avg_word_count > 200:
                recommendations.append("✍️ Votre écriture détaillée est excellente pour l'introspection")
            
            if not recommendations:
                recommendations.append("📖 Continuez votre excellent travail de journalisation")
            
            # 6. Préparer les insights
            insights_data = {
                'total_entries': len(entries_with_analytics),
                'average_mood': round(avg_mood, 2),
                'average_word_count': round(avg_word_count, 0),
                'most_active_day': 'Analyse en cours',
            }
            
            # 7. Détecter les patterns basiques
            patterns_data = []
            if len(entries_with_analytics) >= 2:
                patterns_data.append(f"Rythme d'écriture: {len(entries_with_analytics)} entrées cette semaine")
            
            if most_common_emotion:
                patterns_data.append(f"Émotion principale: {most_common_emotion[0][0]}")
            
            if avg_mood > 0.1:
                patterns_data.append("Tendance positive dans vos écrits")
            elif avg_mood < -0.1:
                patterns_data.append("Période de réflexion intense")
            
            print(f"✅ Insights générés avec succès")
            
            return {
                'insights': insights_data,
                'patterns': patterns_data[:3],  # Maximum 3 patterns
                'recommendations': recommendations[:3]  # Maximum 3 recommandations
            }
                
        except Exception as e:
            print(f"❌ Erreur génération insights: {e}")
            import traceback
            traceback.print_exc()
            return None

class EnhancedJournalAnalytics:
    
    @staticmethod
    def analyze_entry(entry):
        """
        Comprehensive entry analysis with AI integration
        """
        from .models import EntryAnalytics
        
        # Basic analysis
        sentiment_score, sentiment = JournalAnalytics.analyze_sentiment(entry.description)
        emotions = JournalAnalytics.detect_emotions(entry.description)
        word_count = len(entry.description.split())
        reading_time = max(1, word_count // 200)
        
        # AI-enhanced analysis
        ai_sentiment = RealAIService.analyze_sentiment_with_huggingface(entry.description)
        keywords = RealAIService.extract_keywords_with_rake(entry.description)
        
        # Combine AI and basic analysis
        final_sentiment = ai_sentiment['sentiment'] if ai_sentiment else sentiment
        final_emotions = emotions
        
        # Create or update analytics
        analytics, created = EntryAnalytics.objects.get_or_create(
            entry=entry,
            defaults={
                'user': entry.user,
                'mood_score': sentiment_score,
                'sentiment': final_sentiment,
                'word_count': word_count,
                'reading_time': reading_time,
                'emotions': final_emotions,
                'keywords': keywords,
                'themes': EnhancedJournalAnalytics.identify_themes(entry.description)
            }
        )
        
        if not created:
            analytics.mood_score = sentiment_score
            analytics.sentiment = final_sentiment
            analytics.word_count = word_count
            analytics.reading_time = reading_time
            analytics.emotions = final_emotions
            analytics.keywords = keywords
            analytics.themes = EnhancedJournalAnalytics.identify_themes(entry.description)
            analytics.save()
        
        return analytics

    @staticmethod
    def identify_themes(text):
        """
        Identify common themes in journal entries
        """
        theme_keywords = {
            'work': {'travail', 'bureau', 'collègue', 'projet', 'réunion', 'deadline'},
            'study': {'étude', 'cours', 'examen', 'devoir', 'professeur', 'université'},
            'family': {'famille', 'parent', 'enfant', 'mère', 'père', 'frère', 'sœur'},
            'friends': {'ami', 'amie', 'copain', 'copine', 'groupe', 'sortie'},
            'health': {'santé', 'médecin', 'malade', 'fatigue', 'sport', 'régime'},
            'hobbies': {'loisir', 'passion', 'musique', 'lecture', 'film', 'série'},
            'travel': {'voyage', 'vacances', 'destination', 'avion', 'hôtel'},
            'reflection': {'pensée', 'réflexion', 'appris', 'compris', 'réalisé'}
        }
        
        words = set(text.lower().split())
        themes = []
        
        for theme, keywords in theme_keywords.items():
            matches = keywords.intersection(words)
            if matches:
                themes.append({
                    'theme': theme,
                    'confidence': len(matches) / len(keywords),
                    'matched_keywords': list(matches)
                })
        
        return sorted(themes, key=lambda x: x['confidence'], reverse=True)[:3]

    @staticmethod
    def prepare_data_for_ai(user, start_date, end_date):
        """
        Prépare les données pour l'analyse IA
        """
        from journal.models import Journal
        from .models import EntryAnalytics
        
        entries = Journal.objects.filter(
            user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        total_entries = entries.count()
        
        # Données de base
        analytics_data = []
        mood_scores = []
        word_counts = []
        all_emotions = Counter()
        all_themes = Counter()
        recent_entries_previews = []
        
        for entry in entries.order_by('-created_at')[:10]:  # 10 entrées récentes
            try:
                analytics = EntryAnalytics.objects.get(entry=entry)
                analytics_data.append({
                    'date': entry.created_at.date(),
                    'mood_score': analytics.mood_score or 0,
                    'sentiment': analytics.sentiment,
                    'word_count': analytics.word_count,
                    'emotions': analytics.emotions,
                    'keywords': analytics.keywords,
                    'themes': analytics.themes
                })
                
                if analytics.mood_score:
                    mood_scores.append(analytics.mood_score)
                word_counts.append(analytics.word_count)
                all_emotions.update(analytics.emotions)
                
                # Compter les thèmes
                for theme_data in analytics.themes:
                    all_themes[theme_data.get('theme', 'unknown')] += 1
                
                # Préparer les previews
                recent_entries_previews.append({
                    'preview': entry.description[:200],
                    'date': entry.created_at.date(),
                    'mood': analytics.mood_score or 0
                })
                
            except EntryAnalytics.DoesNotExist:
                continue
        
        # Calculer les statistiques
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        
        # Top émotions et thèmes
        top_emotions = [emotion for emotion, count in all_emotions.most_common(3)]
        top_themes = [theme for theme, count in all_themes.most_common(3)]
        
        # Calculer la consistance
        period_days = (end_date - start_date).days or 1
        entries_per_week = (total_entries / period_days) * 7
        consistency_score = min(1.0, total_entries / (period_days * 0.3))  # Objectif: 30% des jours avec entrées
        
        return {
            'total_entries': total_entries,
            'period_days': period_days,
            'average_mood': avg_mood,
            'average_word_count': avg_word_count,
            'top_emotions': top_emotions,
            'top_themes': top_themes,
            'entries_per_week': round(entries_per_week, 1),
            'consistency_score': round(consistency_score, 2),
            'recent_entries': recent_entries_previews,
            'start_date': start_date,
            'end_date': end_date
        }

    @staticmethod
    def prepare_data_for_ai_all_time(user):
        """
        Prépare les données avec TOUTES les entrées sans filtre de date
        """
        from journal.models import Journal
        from .models import EntryAnalytics
        
        entries = Journal.objects.filter(user=user)
        total_entries = entries.count()
        
        if total_entries == 0:
            return {'total_entries': 0}
        
        # Calculer les dates min et max
        dates = entries.dates('created_at', 'day')
        if dates:
            start_date = dates.first()
            end_date = dates.last()
            period_days = (end_date - start_date).days or 1
        else:
            start_date = timezone.now().date()
            end_date = timezone.now().date()
            period_days = 1
        
        # Reprendre le code existant de prepare_data_for_ai mais sans filtre de date
        analytics_data = []
        mood_scores = []
        word_counts = []
        all_emotions = Counter()
        all_themes = Counter()
        recent_entries_previews = []
        
        for entry in entries.order_by('-created_at')[:10]:
            try:
                analytics = EntryAnalytics.objects.get(entry=entry)
                analytics_data.append({
                    'date': entry.created_at.date(),
                    'mood_score': analytics.mood_score or 0,
                    'sentiment': analytics.sentiment,
                    'word_count': analytics.word_count,
                    'emotions': analytics.emotions,
                    'keywords': analytics.keywords,
                    'themes': analytics.themes
                })
                
                if analytics.mood_score:
                    mood_scores.append(analytics.mood_score)
                word_counts.append(analytics.word_count)
                all_emotions.update(analytics.emotions)
                
                for theme_data in analytics.themes:
                    all_themes[theme_data.get('theme', 'unknown')] += 1
                
                recent_entries_previews.append({
                    'preview': entry.description[:200],
                    'date': entry.created_at.date(),
                    'mood': analytics.mood_score or 0
                })
                
            except EntryAnalytics.DoesNotExist:
                continue
        
        # Calculs statistiques
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        
        top_emotions = [emotion for emotion, count in all_emotions.most_common(3)]
        top_themes = [theme for theme, count in all_themes.most_common(3)]
        
        entries_per_week = (total_entries / period_days) * 7
        consistency_score = min(1.0, total_entries / (period_days * 0.3))
        
        return {
            'total_entries': total_entries,
            'period_days': period_days,
            'average_mood': avg_mood,
            'average_word_count': avg_word_count,
            'top_emotions': top_emotions,
            'top_themes': top_themes,
            'entries_per_week': round(entries_per_week, 1),
            'consistency_score': round(consistency_score, 2),
            'recent_entries': recent_entries_previews,
            'start_date': start_date,
            'end_date': end_date
        }

    @staticmethod
    def generate_comprehensive_insights(user, days=30):
        """
        Generate comprehensive insights with AI enhancement
        """
        from journal.models import Journal
        from .models import EntryAnalytics
        
        start_date = timezone.now().date() - timedelta(days=days)
        end_date = timezone.now().date()
        
        entries = Journal.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        if not entries.exists():
            return None
        
        # Get analytics data
        analytics_data = []
        for entry in entries:
            try:
                analytics = EntryAnalytics.objects.get(entry=entry)
                analytics_data.append({
                    'date': entry.created_at.date(),
                    'mood_score': analytics.mood_score,
                    'sentiment': analytics.sentiment,
                    'word_count': analytics.word_count,
                    'emotions': analytics.emotions,
                    'keywords': analytics.keywords,
                    'themes': analytics.themes
                })
            except EntryAnalytics.DoesNotExist:
                continue
        
        if not analytics_data:
            return None
        
        # Generate AI insights
        ai_insights = RealAIService.generate_ai_insights_with_huggingface(
            EnhancedJournalAnalytics.prepare_data_for_ai(user, start_date, end_date)
        )
        
        # Comprehensive analysis
        insights = {
            'period_summary': {
                'total_entries': len(analytics_data),
                'days_analyzed': days,
                'start_date': str(start_date),
                'end_date': str(end_date)
            },
            'mood_analysis': EnhancedJournalAnalytics.analyze_mood_patterns(analytics_data),
            'writing_analysis': EnhancedJournalAnalytics.analyze_writing_patterns(analytics_data),
            'theme_analysis': EnhancedJournalAnalytics.analyze_themes(analytics_data),
            'ai_insights': ai_insights,
            'personalized_recommendations': EnhancedJournalAnalytics.generate_recommendations(analytics_data)
        }
        
        return insights

    @staticmethod
    def analyze_mood_patterns(analytics_data):
        """Advanced mood pattern analysis"""
        mood_scores = [entry.get('mood_score', 0) for entry in analytics_data if entry.get('mood_score')]
        
        if not mood_scores:
            return {'message': 'Données d\'humeur insuffisantes'}
        
        analysis = {
            'average_mood': round(sum(mood_scores) / len(mood_scores), 2),
            'mood_range': f"{min(mood_scores):.2f} - {max(mood_scores):.2f}",
            'stability': 'stable' if max(mood_scores) - min(mood_scores) < 0.5 else 'variable',
            'trend': 'positive' if mood_scores[-1] > mood_scores[0] else 'negative' if mood_scores[-1] < mood_scores[0] else 'stable'
        }
        
        return analysis

    @staticmethod
    def analyze_writing_patterns(analytics_data):
        """Advanced writing pattern analysis"""
        word_counts = [entry.get('word_count', 0) for entry in analytics_data]
        
        if not word_counts:
            return {'message': 'Données d\'écriture insuffisantes'}
        
        analysis = {
            'average_length': round(sum(word_counts) / len(word_counts)),
            'total_words': sum(word_counts),
            'consistency': 'constant' if max(word_counts) - min(word_counts) < 100 else 'variable',
            'preferred_time': 'matin'  # This would need timestamp analysis
        }
        
        return analysis

    @staticmethod
    def analyze_themes(analytics_data):
        """Theme evolution analysis"""
        all_themes = []
        for entry in analytics_data:
            all_themes.extend(entry.get('themes', []))
        
        if not all_themes:
            return {'message': 'Aucun thème détecté'}
        
        theme_names = [theme.get('theme', '') for theme in all_themes]
        theme_counter = Counter(theme_names)
        
        return {
            'top_themes': dict(theme_counter.most_common(5)),
            'total_unique_themes': len(set(theme_names))
        }

    @staticmethod
    def generate_recommendations(analytics_data):
        """Personalized recommendations"""
        recommendations = []
        
        # Mood-based recommendations
        mood_scores = [entry.get('mood_score', 0) for entry in analytics_data if entry.get('mood_score')]
        if mood_scores:
            avg_mood = sum(mood_scores) / len(mood_scores)
            if avg_mood < -0.1:
                recommendations.append("💖 Pensez à pratiquer la gratitude quotidiennement")
            elif avg_mood > 0.2:
                recommendations.append("🌟 Partagez votre positivité avec votre entourage")
        
        # Writing habit recommendations
        word_counts = [entry.get('word_count', 0) for entry in analytics_data]
        if word_counts and len(word_counts) > 5:
            if max(word_counts) < 50:
                recommendations.append("📚 Essayez d'écrire des entrées plus détaillées pour mieux explorer vos pensées")
        
        # Theme-based recommendations
        all_themes = []
        for entry in analytics_data:
            all_themes.extend(entry.get('themes', []))
        
        if all_themes:
            theme_names = [theme.get('theme', '') for theme in all_themes]
            theme_counter = Counter(theme_names)
            top_theme = theme_counter.most_common(1)
            
            if top_theme and top_theme[0][0] == 'work':
                recommendations.append("⚖️ Pensez à équilibrer travail et vie personnelle")
            elif top_theme and top_theme[0][0] == 'study':
                recommendations.append("📖 Prenez des pauses régulières pendant vos sessions d'étude")
        
        if not recommendations:
            recommendations.append("📝 Continuez votre excellent travail de journalisation !")
        
        return recommendations[:3]  # Return top 3 recommendations

# Fonctions utilitaires
def debug_weekly_insights(user):
    """Debug détaillé de la génération d'insights"""
    from journal.models import Journal
    from .models import EntryAnalytics
    from datetime import timedelta
    from django.utils import timezone
    
    print(f"\n=== DEBUG WEEKLY INSIGHTS pour {user.username} ===")
    
    # 1. Vérifier les entrées récentes
    week_ago = timezone.now() - timedelta(days=7)
    recent_entries = Journal.objects.filter(
        user=user,
        created_at__gte=week_ago
    )
    print(f"📝 Entrées dernières 7 jours: {recent_entries.count()}")
    
    for entry in recent_entries:
        print(f"   - {entry.title} ({entry.created_at.date()})")
    
    # 2. Vérifier les analytics
    entries_with_analytics = []
    for entry in recent_entries:
        try:
            analytics = EntryAnalytics.objects.get(entry=entry)
            entries_with_analytics.append((entry, analytics))
            print(f"✅ Analytics trouvés pour: {entry.title}")
        except EntryAnalytics.DoesNotExist:
            print(f"❌ PAS d'analytics pour: {entry.title}")
    
    print(f"🔍 Entrées avec analytics: {len(entries_with_analytics)}")
    
    # 3. Vérifier les données des analytics
    for entry, analytics in entries_with_analytics:
        print(f"   {entry.title}: mood={analytics.mood_score}, words={analytics.word_count}")
    
    return len(entries_with_analytics) > 0

# Ajouter la méthode manquante à RealAIService pour éviter les erreurs
def add_missing_methods():
    """Ajoute les méthodes manquantes à RealAIService si nécessaire"""
    if not hasattr(RealAIService, 'extract_keywords_with_rake'):
        @staticmethod
        def extract_keywords_with_rake(text):
            """Extraction basique de mots-clés"""
            words = text.lower().split()
            # Retourner les mots les plus fréquents (simplifié)
            from collections import Counter
            common_words = {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'que', 'dans', 'pour'}
            word_counts = Counter([word for word in words if word not in common_words and len(word) > 3])
            return [word for word, count in word_counts.most_common(5)]
        
        RealAIService.extract_keywords_with_rake = extract_keywords_with_rake

# Appeler cette fonction au chargement du module
add_missing_methods()