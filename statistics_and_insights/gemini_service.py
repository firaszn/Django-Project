# statistics_and_insights/gemini_service.py
import google.generativeai as genai
from django.conf import settings
import json
import time
import logging

logger = logging.getLogger(__name__)

class GeminiAIService:
    
    @staticmethod
    def get_service():
        """Initialise et retourne le service Gemini"""
        print("🔍 Chargement de Gemini AI...")
        
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            print("❌ GEMINI_API_KEY non configurée")
            raise ValueError("GEMINI_API_KEY non configurée")
        
        if not api_key.startswith('AIza'):
            print(f"❌ Format de clé invalide: {api_key[:20]}...")
            raise ValueError("Format de clé API invalide")
        
        try:
            genai.configure(api_key=api_key)
            print("✅ Gemini AI configuré avec succès")
            return GeminiAIService()
        except Exception as e:
            print(f"❌ Erreur configuration Gemini: {e}")
            raise
    
    def __init__(self):
        # MODÈLES CORRIGÉS - Utiliser les noms actuels
        self.model = None
        self.model_name = "unknown"
        
        # Liste des modèles à essayer (dans l'ordre de préférence)
        model_attempts = [
            'gemini-latest',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash-8b',
        ]
        
        for model_name in model_attempts:
            try:
                print(f"🔍 Essai du modèle: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                # Test rapide pour vérifier que le modèle fonctionne
                test_response = self.model.generate_content("Test")
                self.model_name = model_name
                print(f"✅ Modèle chargé avec succès: {model_name}")
                self.available = True
                break
            except Exception as e:
                print(f"❌ Échec avec {model_name}: {e}")
                continue
        
        if not self.model:
            print("❌ Aucun modèle Gemini disponible")
            self.available = False
            raise Exception("Aucun modèle Gemini disponible")
    
    def analyze_sentiment(self, text):
        """Analyse de sentiment avec Gemini"""
        if not self.available:
            print("❌ Service non disponible, utilisation du fallback")
            return self.fallback_sentiment(text)
            
        try:
            prompt = f"""
            Analyse le sentiment de ce texte de journal personnel. 
            Réponds UNIQUEMENT avec un objet JSON valide.
            
            Texte: "{text[:1000]}"
            
            Format JSON requis:
            {{
              "sentiment": "positive|negative|neutral",
              "confidence": 0.95,
              "explanation": "explication courte en français"
            }}
            """
            
            print(f"🔍 Envoi demande sentiment à Gemini...")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            print(f"🔍 Réponse brute: {result_text}")
            
            cleaned_text = self.clean_json_response(result_text)
            result = json.loads(cleaned_text)
            
            return {
                'sentiment': result.get('sentiment', 'neutral'),
                'confidence': float(result.get('confidence', 0.8)),
                'explanation': result.get('explanation', ''),
                'model_used': self.model_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse sentiment Gemini: {e}")
            return self.fallback_sentiment(text)
    
    def generate_insights(self, entries_data):
        """Génère des insights avec Gemini"""
        if not self.available:
            print("❌ Service non disponible, utilisation du fallback")
            return self.generate_fallback_insights(entries_data)
            
        try:
            context = self.prepare_context(entries_data)
            
            prompt = f"""
            Tu es un expert en psychologie et analyse de journal personnel.
            
            CONTEXTE À ANALYSER:
            {context}
            
            GÉNÈRE UN RAPPORT D'ANALYSE en JSON avec cette structure exacte:
            {{
              "trends": ["tendance 1", "tendance 2", "tendance 3"],
              "patterns": ["pattern 1", "pattern 2", "pattern 3"],
              "recommendations": ["recommandation 1", "recommandation 2", "recommandation 3"],
              "psychological_insights": ["insight 1", "insight 2", "insight 3"],
              "summary": "résumé court en français"
            }}
            
            RÈGLES:
            - Réponds UNIQUEMENT en JSON valide
            - Pas de texte avant ou après
            - Sois bienveillant et constructif
            - Personnalise selon les données
            - Utilise un français clair
            - Sois spécifique et concret
            """
            
            print("🔍 Envoi demande insights à Gemini...")
            start_time = time.time()
            response = self.model.generate_content(prompt)
            processing_time = time.time() - start_time
            
            result_text = response.text.strip()
            print(f"🔍 Réponse brute Gemini: {result_text}")
            
            cleaned_text = self.clean_json_response(result_text)
            print(f"🔍 JSON nettoyé: {cleaned_text}")
            
            insights = json.loads(cleaned_text)
            
            return {
                'trends': insights.get('trends', []),
                'patterns': insights.get('patterns', []),
                'recommendations': insights.get('recommendations', []),
                'psychological_insights': insights.get('psychological_insights', []),
                'summary': insights.get('summary', ''),
                'ai_generated': True,
                'model_used': self.model_name,
                'confidence_score': 0.92,
                'processing_time': processing_time
            }
            
        except Exception as e:
            print(f"❌ Erreur génération insights Gemini: {e}")
            import traceback
            traceback.print_exc()
            return self.generate_fallback_insights(entries_data)
    
    def clean_json_response(self, text):
        """Nettoie la réponse JSON"""
        print(f"🔍 Nettoyage JSON: {text[:100]}...")
        
        # Supprimer les backticks de code
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        # Nettoyer les caractères problématiques
        text = text.strip()
        text = text.replace('\\n', '').replace('\\t', '').replace('\\"', '"')
        
        # S'assurer que c'est du JSON valide
        try:
            # Essayer de parser pour vérifier
            json.loads(text)
            print("✅ JSON valide après nettoyage")
        except json.JSONDecodeError as e:
            print(f"❌ JSON invalide après nettoyage: {e}")
            # Essayer d'extraire le JSON avec une regex
            import re
            json_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
                print(f"🔍 JSON extrait par regex: {text[:100]}...")
        
        return text.strip()
    
    def prepare_context(self, entries_data):
        """Prépare le contexte pour Gemini"""
        avg_mood = entries_data.get('average_mood', 0)
        mood_status = "positive" if avg_mood > 0.1 else "negative" if avg_mood < -0.1 else "neutral"
        
        # Préparer les extraits d'entrées récentes
        recent_previews = ""
        for entry in entries_data.get('recent_entries', [])[:3]:
            recent_previews += f"- {entry.get('preview', '')} (humeur: {entry.get('mood', 0):.2f})\n"
        
        return f"""
        STATISTIQUES DU JOURNAL:
        - Période: {entries_data.get('period_days', 0)} jours
        - Entrées totales: {entries_data.get('total_entries', 0)}
        - Humeur moyenne: {avg_mood:.2f} ({mood_status})
        - Mots par entrée: {entries_data.get('average_word_count', 0):.0f}
        - Consistance d'écriture: {entries_data.get('consistency_score', 0):.0%}
        - Émotions principales: {', '.join(entries_data.get('top_emotions', ['Divers']))}
        - Thèmes récurrents: {', '.join(entries_data.get('top_themes', ['Divers']))}
        - Streak actuel: {entries_data.get('current_streak', 0)} jours
        - Meilleur streak: {entries_data.get('longest_streak', 0)} jours
        
        EXEMPLES D'ENTRÉES RÉCENTES:
        {recent_previews}
        """
    
    def generate_fallback_insights(self, entries_data):
        """Fallback si Gemini échoue"""
        from .ai_service_real import RealAIService
        print("🔍 Utilisation du fallback système expert")
        return RealAIService.generate_enhanced_fallback(entries_data)
    
    def fallback_sentiment(self, text):
        """Fallback pour l'analyse de sentiment"""
        from .ai_service_real import RealAIService
        return RealAIService.fallback_sentiment_analysis(text)
    
    def test_connection(self):
        """Teste la connexion à Gemini"""
        if not self.available:
            return {"status": "error", "error": "Service non disponible"}
            
        try:
            print(f"🔍 Test connexion avec modèle: {self.model_name}")
            response = self.model.generate_content("Réponds uniquement par 'TEST_OK'.")
            return {
                "status": "success", 
                "response": response.text,
                "model": self.model_name
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}