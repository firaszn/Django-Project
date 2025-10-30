# statistics_and_insights/ai_service_real.py
import json
from django.conf import settings
from datetime import datetime, timedelta
import time
import re
from collections import Counter

try:
    from .gemini_service import GeminiAIService
except ImportError:
    pass

class RealAIService:
    
    @staticmethod
    def analyze_sentiment_with_gemini(text):
        """Analyse de sentiment avec Gemini"""
        try:
            gemini = GeminiAIService.get_service()
            return gemini.analyze_sentiment(text)
        except Exception as e:
            print(f"❌ Gemini non disponible: {e}")
            return RealAIService.fallback_sentiment_analysis(text)
    
    @staticmethod
    def generate_ai_insights_with_gemini(entries_data):
        """Génération d'insights avec Gemini"""
        try:
            gemini = GeminiAIService.get_service()
            return gemini.generate_insights(entries_data)
        except Exception as e:
            print(f"❌ Gemini non disponible: {e}")
            return RealAIService.generate_enhanced_fallback(entries_data)
    
    @staticmethod
    def generate_ai_insights_with_huggingface(entries_data):
        """Ancienne méthode - maintenant utilise Gemini"""
        print("🔍 Utilisation de Gemini au lieu de Hugging Face...")
        return RealAIService.generate_ai_insights_with_gemini(entries_data)
    
    @staticmethod
    def analyze_sentiment_with_huggingface(text):
        """Ancienne méthode - maintenant utilise Gemini"""
        print("🔍 Utilisation de Gemini au lieu de Hugging Face...")
        return RealAIService.analyze_sentiment_with_gemini(text)

    # =========================================================================
    # MÉTHODES EXISTANTES (SYSTÈME EXPERT) - GARDER TOUTES CES MÉTHODES
    # =========================================================================
    
    @staticmethod
    def parse_sentiment_response(result):
        """Parse la réponse de l'API de sentiment"""
        try:
            if isinstance(result, list) and len(result) > 0:
                sentiment_data = result[0]
                
                if isinstance(sentiment_data, list) and len(sentiment_data) > 0:
                    for item in sentiment_data:
                        if isinstance(item, dict) and 'label' in item:
                            label = item['label'].lower()
                            score = item['score']
                            
                            if 'positive' in label or 'pos' in label:
                                return {'sentiment': 'positive', 'confidence': score}
                            elif 'negative' in label or 'neg' in label:
                                return {'sentiment': 'negative', 'confidence': score}
                            elif 'neutral' in label or 'neu' in label:
                                return {'sentiment': 'neutral', 'confidence': score}
                
                elif isinstance(sentiment_data, dict) and 'label' in sentiment_data:
                    label = sentiment_data['label'].lower()
                    score = sentiment_data['score']
                    
                    if '1 star' in label or '2 stars' in label:
                        return {'sentiment': 'negative', 'confidence': score}
                    elif '4 stars' in label or '5 stars' in label:
                        return {'sentiment': 'positive', 'confidence': score}
                    else:
                        return {'sentiment': 'neutral', 'confidence': score}
            
            print(f"❌ Format de réponse non reconnu: {result}")
            return RealAIService.fallback_sentiment_analysis("")
            
        except Exception as e:
            print(f"❌ Erreur parsing réponse: {e}")
            return RealAIService.fallback_sentiment_analysis("")
    
    @staticmethod
    def parse_ai_response_optimized(ai_response, entries_data):
        """Parsing OPTIMISÉ de la réponse IA"""
        try:
            print(f"🔍 Raw AI response type: {type(ai_response)}")
            
            generated_text = ""
            if isinstance(ai_response, list) and ai_response:
                if isinstance(ai_response[0], dict):
                    generated_text = ai_response[0].get('generated_text', '')
            elif isinstance(ai_response, dict):
                generated_text = ai_response.get('generated_text', '')
            
            print(f"🔍 Generated text: {generated_text}")
            
            if not generated_text:
                print("❌ Aucun texte généré trouvé")
                return RealAIService.generate_enhanced_fallback(entries_data)
            
            cleaned_text = generated_text.strip()
            
            json_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group()
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
                    json_str = json_str.replace('\\n', '').replace('\\t', '').replace('\\"', '"')
                    
                    parsed_data = json.loads(json_str)
                    print(f"✅ JSON parsé avec succès: {parsed_data}")
                    
                    trends = parsed_data.get('trends', [])
                    patterns = parsed_data.get('patterns', [])
                    recommendations = parsed_data.get('recommendations', [])
                    insights = parsed_data.get('psychological_insights', [])
                    
                    if any([trends, patterns, recommendations, insights]):
                        return {
                            'trends': trends[:3] or ["Tendance d'écriture régulière"],
                            'patterns': patterns[:3] or ["Pattern de réflexion constante"],
                            'recommendations': recommendations[:3] or ["Continuez votre excellent travail"],
                            'psychological_insights': insights[:3] or ["Votre pratique montre une grande conscience de soi"],
                            'ai_generated': True,
                            'model_used': 'huggingface',
                            'confidence_score': 0.85
                        }
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur JSON: {e}")
                    print(f"🔍 JSON string problématique: {json_str}")
            
            print("🔍 Tentative d'extraction de listes depuis le texte...")
            extracted_data = RealAIService.extract_lists_from_text(cleaned_text)
            
            if any(extracted_data.values()):
                print(f"✅ Données extraites du texte: {extracted_data}")
                return {
                    'trends': extracted_data['trends'][:3],
                    'patterns': extracted_data['patterns'][:3],
                    'recommendations': extracted_data['recommendations'][:3],
                    'psychological_insights': extracted_data['insights'][:3],
                    'ai_generated': True,
                    'model_used': 'text_analysis',
                    'confidence_score': 0.75
                }
            
            print("❌ Impossible d'extraire des données structurées")
            return RealAIService.generate_enhanced_fallback(entries_data)
                
        except Exception as e:
            print(f"❌ Erreur parsing réponse IA: {e}")
            import traceback
            traceback.print_exc()
            return RealAIService.generate_enhanced_fallback(entries_data)
    
    @staticmethod
    def extract_lists_from_text(text):
        """Extrait des listes depuis le texte généré"""
        trends = []
        patterns = []
        recommendations = []
        insights = []
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in ['tendance', 'trend', 'évolution']):
                current_section = 'trends'
                continue
            elif any(keyword in lower_line for keyword in ['pattern', 'comportement', 'habitude']):
                current_section = 'patterns'
                continue
            elif any(keyword in lower_line for keyword in ['recommandation', 'suggestion', 'conseil']):
                current_section = 'recommendations'
                continue
            elif any(keyword in lower_line for keyword in ['insight', 'psycholog', 'analyse']):
                current_section = 'insights'
                continue
            
            if (line.startswith('-') or line.startswith('•') or 
                line.startswith('*') or (line[0].isdigit() and '.' in line[:3]) or
                line.startswith('"') or (len(line) > 10 and not line.startswith('{'))):
                
                item = re.sub(r'^[-•*\d."\']+\s*', '', line).strip()
                
                if len(item) > 15:
                    if current_section == 'trends' and len(trends) < 5:
                        trends.append(item)
                    elif current_section == 'patterns' and len(patterns) < 5:
                        patterns.append(item)
                    elif current_section == 'recommendations' and len(recommendations) < 5:
                        recommendations.append(item)
                    elif current_section == 'insights' and len(insights) < 5:
                        insights.append(item)
        
        return {
            'trends': trends or ["Croissance dans la pratique d'écriture"],
            'patterns': patterns or ["Régularité dans l'expression personnelle"],
            'recommendations': recommendations or ["Continuez à documenter vos réflexions"],
            'insights': insights or ["Votre journal renforce la conscience de soi"]
        }

    @staticmethod
    def prepare_context_for_ai(entries_data):
        """Contexte pour l'analyse"""
        avg_mood = entries_data.get('average_mood', 0)
        mood_status = "positive" if avg_mood > 0.1 else "negative" if avg_mood < -0.1 else "neutral"
        
        return f"""
        Statistiques du journal:
        - Période: {entries_data.get('period_days', 0)} jours
        - Nombre d'entrées: {entries_data.get('total_entries', 0)}
        - Humeur moyenne: {avg_mood:.2f} ({mood_status})
        - Mots par entrée: {entries_data.get('average_word_count', 0):.0f}
        - Émotions principales: {', '.join(entries_data.get('top_emotions', ['Divers']))}
        - Thèmes récurrents: {', '.join(entries_data.get('top_themes', ['Divers']))}
        - Consistance: {entries_data.get('consistency_score', 0):.0%}
        """

    @staticmethod
    def generate_enhanced_fallback(entries_data):
        """Système expert d'analyse de journal - Insights contextuels avancés"""
        trends = []
        patterns = []
        recommendations = []
        insights = []
        
        avg_mood = entries_data.get('average_mood', 0)
        total_entries = entries_data.get('total_entries', 0)
        consistency = entries_data.get('consistency_score', 0)
        avg_words = entries_data.get('average_word_count', 0)
        top_emotions = entries_data.get('top_emotions', [])
        top_themes = entries_data.get('top_themes', [])
        period_days = entries_data.get('period_days', 7)
        
        print(f"🔍 Analyse expert - Humeur: {avg_mood:.2f}, Entrées: {total_entries}, Consistance: {consistency:.2f}")
        
        if avg_mood > 0.3:
            trends.extend([
                "Tendance émotionnelle très positive dans vos écrits récents",
                "Énergie et optimisme en progression constante",
                "Équilibre général dans votre perspective quotidienne"
            ])
        elif avg_mood > 0.1:
            trends.extend([
                "Humeur globalement positive avec des moments de réflexion",
                "Stabilité émotionnelle bien établie",
                "Approche constructive des situations rencontrées"
            ])
        elif avg_mood < -0.3:
            trends.extend([
                "Période d'introspection profonde et d'expression authentique",
                "Recherche de sens dans les défis actuels",
                "Expression émotionnelle intense et réfléchie"
            ])
        elif avg_mood < -0.1:
            trends.extend([
                "Moments de réflexion sur les difficultés rencontrées",
                "Expression honnête des émotions complexes",
                "Recherche d'équilibre émotionnel"
            ])
        else:
            trends.extend([
                "Stabilité émotionnelle remarquable",
                "Équilibre entre réflexion et action",
                "Consistance dans l'expression de vos pensées"
            ])
        
        if consistency > 0.8:
            patterns.extend([
                "Excellente discipline d'écriture quotidienne",
                "Routine bien ancrée et productive",
                "Engagement remarquable dans votre pratique"
            ])
        elif consistency > 0.6:
            patterns.extend([
                "Régularité soutenue dans votre journalisation",
                "Rythme d'écriture adapté à votre style de vie",
                "Consistance bénéfique pour la réflexion"
            ])
        elif consistency > 0.4:
            patterns.extend([
                "Équilibre entre écriture régulière et spontanée",
                "Adaptation flexible de votre routine",
                "Approche organique de la journalisation"
            ])
        else:
            patterns.extend([
                "Écriture guidée par l'inspiration du moment",
                "Opportunité de développer une routine plus stable",
                "Flexibilité dans votre expression personnelle"
            ])
        
        theme_patterns = []
        themes_str = str(top_themes).lower()
        if any(theme in themes_str for theme in ['work', 'travail', 'profession']):
            theme_patterns.append("Focus marqué sur les aspects professionnels")
        if any(theme in themes_str for theme in ['family', 'famille', 'parent']):
            theme_patterns.append("Attention particulière aux relations familiales")
        if any(theme in themes_str for theme in ['friend', 'ami', 'social']):
            theme_patterns.append("Importance des relations sociales")
        if any(theme in themes_str for theme in ['health', 'santé', 'sport']):
            theme_patterns.append("Préoccupation pour le bien-être physique")
        if any(theme in themes_str for theme in ['study', 'étude', 'apprentissage']):
            theme_patterns.append("Engagement dans le développement des connaissances")
        
        patterns.extend(theme_patterns[:2])
        
        if total_entries < 5:
            recommendations.extend([
                "🎯 Fixez-vous un objectif de 2-3 entrées par semaine pour établir une routine",
                "📝 Explorez différents formats : listes, lettres à vous-même, ou dialogues",
                "⏰ Essayez d'écrire à différents moments de la journée pour découvrir vos préférences"
            ])
        elif total_entries < 15:
            recommendations.extend([
                "🌟 Capitalisez sur votre engagement en variant les thèmes d'écriture",
                "🔍 Relisez occasionnellement vos anciennes entrées pour mesurer votre progression",
                "💭 Expérimentez avec l'écriture libre pour explorer de nouvelles perspectives"
            ])
        else:
            recommendations.extend([
                "📚 Approfondissez vos thèmes récurrents pour des insights plus riches",
                "🔄 Créez des rituels d'écriture autour de vos moments clés de la journée",
                "🎨 Envisagez d'intégrer des éléments créatifs comme des dessins ou citations"
            ])
        
        if avg_mood < -0.2:
            recommendations.extend([
                "💝 Pratiquez l'auto-compassion lors des périodes difficiles",
                "🌱 Identifiez les petites victoires quotidiennes dans vos écrits",
                "🤝 Partagez vos réflexions avec une personne de confiance"
            ])
        elif avg_mood > 0.2:
            recommendations.extend([
                "🚀 Utilisez votre énergie positive pour initier de nouveaux projets",
                "🌈 Documentez ce qui contribue à votre bien-être pour le reproduire",
                "🎉 Célébrez vos progrès et moments de bonheur dans votre journal"
            ])
        
        if avg_words < 50:
            recommendations.append("✍️ Essayez de développer davantage vos pensées pour des insights plus profonds")
        elif avg_words > 300:
            recommendations.append("🎯 Concentrez-vous sur l'essentiel pour identifier vos priorités claires")
        
        insights.extend([
            "Votre pratique de journalisation renforce votre intelligence émotionnelle et votre conscience de soi",
            "Chaque entrée contribue à construire une compréhension plus profonde de vos patterns mentaux",
            "L'écriture régulière développe votre capacité à naviguer dans les complexités émotionnelles"
        ])
        
        if total_entries > 20:
            insights.append("Votre persévérance démontre un engagement profond envers votre développement personnel")
        if consistency > 0.7:
            insights.append("Votre régularité crée une base solide pour la croissance et l'auto-réflexion")
        
        if -0.1 <= avg_mood <= 0.1:
            insights.append("Votre stabilité émotionnelle témoigne d'une bonne régulation interne")
        
        trends = trends[:3]
        patterns = patterns[:3]
        recommendations = recommendations[:3]
        insights = insights[:3]
        
        return {
            'trends': trends,
            'patterns': patterns,
            'recommendations': recommendations,
            'psychological_insights': insights,
            'ai_generated': False,
            'enhanced_fallback': True,
            'analysis_type': 'système_expert_avancé',
            'confidence_score': 0.85
        }

    @staticmethod
    def fallback_sentiment_analysis(text):
        """Analyse de sentiment de fallback"""
        positive_words = {'heureux', 'content', 'joyeux', 'bon', 'super', 'excellent', 'génial', 'formidable', 'fier', 'satisfait', 'réussi', 'positif', 'optimiste', 'chanceux', 'chanceuse', 'enthousiaste', 'motivé', 'motivée'}
        negative_words = {'triste', 'malheureux', 'déçu', 'mauvais', 'terrible', 'horrible', 'stressé', 'fatigué', 'anxieux', 'inquiet', 'négatif', 'pessimiste', 'découragé', 'découragée', 'frustré', 'frustrée'}
        
        words = set(text.lower().split())
        pos_count = len(positive_words.intersection(words))
        neg_count = len(negative_words.intersection(words))
        total_relevant = pos_count + neg_count
        
        if total_relevant == 0:
            return {'sentiment': 'neutral', 'confidence': 0.5}
        
        sentiment_score = (pos_count - neg_count) / total_relevant
        
        if sentiment_score > 0.3:
            return {'sentiment': 'positive', 'confidence': min(0.9, 0.6 + sentiment_score)}
        elif sentiment_score < -0.3:
            return {'sentiment': 'negative', 'confidence': min(0.9, 0.6 - sentiment_score)}
        else:
            return {'sentiment': 'neutral', 'confidence': 0.7}

    @staticmethod
    def generate_fallback_insights(entries_data):
        """Insights de fallback"""
        avg_mood = entries_data.get('average_mood', 0)
        total_entries = entries_data.get('total_entries', 0)
        
        if total_entries == 0:
            return {
                'trends': ["Début de votre parcours de journalisation"],
                'patterns': ["Aucun pattern détecté pour le moment"],
                'recommendations': [
                    "Commencez par écrire une première entrée pour démarrer l'analyse",
                    "Fixez-vous un objectif simple: une entrée cette semaine",
                    "Explorez différents sujets qui vous tiennent à cœur"
                ],
                'psychological_insights': [
                    "La journalisation est un outil puissant pour la conscience de soi",
                    "Chaque parcours commence par un premier pas",
                    "L'écriture régulière améliore la clarté mentale et la résilience"
                ],
                'ai_generated': False
            }
        
        if avg_mood > 0.3:
            mood_insights = [
                "Humeur globalement positive et optimiste",
                "Bonne énergie et motivation perceptibles",
                "Équilibre émotionnel favorable"
            ]
            recommendations = [
                "Capitalisez sur cette énergie positive pour explorer de nouveaux projets",
                "Partagez votre positivité avec votre entourage",
                "Documentez ce qui contribue à votre bien-être pour le reproduire"
            ]
        elif avg_mood < -0.3:
            mood_insights = [
                "Période de défis émotionnels",
                "Besoin d'attention particulière au bien-être",
                "Opportunité de croissance personnelle"
            ]
            recommendations = [
                "Pratiquez l'auto-compassion et la bienveillance envers vous-même",
                "Identifiez les sources de soutien dans votre entourage",
                "Consacrez du temps à des activités qui vous ressourcent"
            ]
        else:
            mood_insights = [
                "Stabilité émotionnelle remarquable",
                "Équilibre entre les différentes sphères de vie",
                "Approche mesurée et réfléchie"
            ]
            recommendations = [
                "Maintenez cette belle régularité dans votre pratique",
                "Explorez de nouvelles perspectives dans vos écrits",
                "Célébrez la consistance de votre engagement"
            ]
        
        return {
            'trends': mood_insights,
            'patterns': [
                f"Rythme d'écriture: {total_entries} entrées sur la période",
                "Engagement constant dans la pratique réflexive",
                "Développement progressif de la conscience de soi"
            ],
            'recommendations': recommendations,
            'psychological_insights': [
                "Votre pratique de journalisation renforce la résilience émotionnelle",
                "L'écriture régulière améliore la capacité d'introspection",
                "Chaque entrée contribue à construire une narrative personnelle cohérente"
            ],
            'ai_generated': False
        }

    @staticmethod
    def test_available_models():
        """Teste quels modèles sont disponibles"""
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return {"error": "API key non configurée"}
        
        try:
            gemini = GeminiAIService.get_service()
            test_result = gemini.test_connection()
            return {
                "gemini": {
                    "status": "success" if test_result["status"] == "success" else "error",
                    "available": test_result["status"] == "success",
                    "model": test_result.get("model", "unknown"),
                    "response": test_result.get("response", "")
                }
            }
        except Exception as e:
            return {
                "gemini": {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }
            }