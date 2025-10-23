from datetime import datetime, timedelta
from collections import Counter
from django.utils import timezone
from django.db.models import Avg, Count
import json

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
        """Génère des insights hebdomadaires"""
        week_ago = timezone.now() - timedelta(days=7)
        
        try:
            # CORRECTION : Import depuis le bon module
            from journal.models import Journal
            from statistics_and_insights.models import EntryAnalytics  # ← CORRIGÉ
            
            recent_entries = Journal.objects.filter(
                user=user,
                created_at__gte=week_ago
            )
            
            if not recent_entries.exists():
                return None
            
            # Récupérer les analytics associés
            entries_with_analytics = []
            emotions_counter = Counter()
            mood_scores = []
            total_words = 0
            
            for entry in recent_entries:
                try:
                    analytics = EntryAnalytics.objects.get(entry=entry)
                    entries_with_analytics.append((entry, analytics))
                    emotions_counter.update(analytics.emotions)
                    mood_scores.append(analytics.mood_score)
                    total_words += analytics.word_count
                except EntryAnalytics.DoesNotExist:
                    continue
            
            if not entries_with_analytics:
                return None
            
            # Calculer les statistiques
            avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
            avg_word_count = total_words / len(entries_with_analytics)
            
            # Détecter les tendances
            mood_trend = 'stable'
            if len(mood_scores) > 1:
                first_half = mood_scores[:len(mood_scores)//2]
                second_half = mood_scores[len(mood_scores)//2:]
                avg_first = sum(first_half) / len(first_half) if first_half else 0
                avg_second = sum(second_half) / len(second_half) if second_half else 0
                
                if avg_second > avg_first + 0.1:
                    mood_trend = 'amélioration'
                elif avg_second < avg_first - 0.1:
                    mood_trend = 'baisse'
            
            # Générer les recommandations
            recommendations = []
            most_common_emotion = emotions_counter.most_common(1)
            
            if most_common_emotion:
                emotion, count = most_common_emotion[0]
                if emotion == 'anxieux' and count > 2:
                    recommendations.append("💆 Essayez des exercices de respiration pour gérer le stress")
                elif emotion == 'triste' and count > 2:
                    recommendations.append("🌞 Prenez le temps de faire des activités qui vous plaisent")
                elif emotion == 'fatigué' and count > 1:
                    recommendations.append("😴 Pensez à améliorer votre routine de sommeil")
            
            if avg_mood < -0.1:
                recommendations.append("💝 Prenez soin de vous cette semaine !")
            elif avg_mood > 0.2:
                recommendations.append("🎉 Continuez comme ça, vous allez bien !")
            
            if not recommendations:
                recommendations.append("📖 Continuez votre excellent travail de journalisation !")
            
            # Préparer les insights
            insights_data = {
                'total_entries': len(entries_with_analytics),
                'average_mood': round(avg_mood, 2),
                'average_word_count': round(avg_word_count, 0),
                'most_active_day': 'Lundi',
            }
            
            patterns_data = [
                f"Humeur générale: {mood_trend}",
                f"Émotion principale: {most_common_emotion[0][0] if most_common_emotion else 'Non détectée'}",
                f"Productivité d'écriture: {'Élevée' if avg_word_count > 100 else 'Moyenne'}"
            ]
            
            return {
                'insights': insights_data,
                'patterns': patterns_data,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"Erreur génération insights: {e}")
            return None