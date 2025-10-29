"""
Services IA pour la gestion des utilisateurs
Utilise des APIs gratuites : HuggingFace Inference API, Groq API
"""
import requests
import os
import json
import re
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

# Configuration des APIs IA
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models"
HUGGINGFACE_API_KEY = getattr(settings, 'HUGGINGFACE_API_KEY', None)

# Groq API (Gratuit et rapide - https://console.groq.com/)
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', None)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class AIServiceError(Exception):
    """Exception personnalisée pour les erreurs de service IA"""
    pass


class BioGeneratorService:
    """
    Service pour générer une bio automatiquement en utilisant l'IA
    Utilise HuggingFace GPT-2 ou GPT-Neo (gratuit)
    """
    
    @staticmethod
    def generate_bio(user, keywords=None):
        """
        Génère une bio professionnelle pour un utilisateur
        
        Args:
            user: Instance CustomUser
            keywords: Liste de mots-clés optionnels (ex: ['passionné', 'développeur'])
        
        Returns:
            str: Bio générée
        """
        try:
            # Préparer le prompt
            full_name = user.get_full_name()
            role = user.role
            
            # Construire le prompt pour l'IA
            keywords_str = f" et {' '.join(keywords)}" if keywords else ""
            
            prompt = f"Write a professional and engaging biography in French for {full_name}, who is a {role}{keywords_str}. " \
                    f"Keep it short (maximum 150 words), friendly, and professional. " \
                    f"Do not include email or phone number."
            
            # Essayer différentes APIs dans l'ordre
            bio = None
            
            # Option 1: Groq (gratuit, rapide, excellent pour français)
            if GROQ_API_KEY:
                bio = BioGeneratorService._generate_with_groq(full_name, role, keywords)
            
            # Option 2: HuggingFace (si Groq n'est pas disponible)
            if not bio:
                bio = BioGeneratorService._generate_with_huggingface(prompt)
            
            # Limiter à 500 caractères (limite du modèle CustomUser.bio)
            if bio and len(bio) > 500:
                # Couper à la dernière phrase complète avant 500 caractères
                truncated = bio[:497]
                last_period = truncated.rfind('.')
                last_exclamation = truncated.rfind('!')
                last_question = truncated.rfind('?')
                
                # Trouver la dernière ponctuation
                last_punctuation = max(last_period, last_exclamation, last_question)
                
                if last_punctuation > 400:  # Si on a une phrase complète pas trop tôt
                    bio = truncated[:last_punctuation + 1]
                else:
                    bio = truncated + "..."
            
            # Option 3: Templates variés si les APIs échouent
            return bio if bio else BioGeneratorService._generate_fallback_bio(user, keywords)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de bio: {str(e)}")
            return BioGeneratorService._generate_fallback_bio(user, keywords)
    
    @staticmethod
    def _generate_with_groq(full_name, role, keywords=None):
        """
        Génère une bio en utilisant Groq API (gratuit, rapide, excellent pour français)
        Nécessite une clé API gratuite depuis https://console.groq.com/
        """
        if not GROQ_API_KEY:
            return None
            
        try:
            # Construire le message en français
            keywords_text = f" avec les centres d'intérêt suivants : {', '.join(keywords)}" if keywords else ""
            
            messages = [
                {
                    "role": "system",
                    "content": "Tu es un assistant qui crée des biographies professionnelles. Réponds UNIQUEMENT avec la biographie, sans préfixe, sans guillemets, sans explication. Juste la bio directement."
                },
                {
                    "role": "user",
                    "content": f"Écris une biographie courte et complète (exactement 80-100 mots, finis la dernière phrase) pour {full_name}, un {role}{keywords_text}. Écris UNIQUEMENT la bio complète et finie, commence directement sans préface. Assure-toi de finir la dernière phrase."
                }
            ]
            
            payload = {
                "model": "llama-3.1-8b-instant",  # Modèle gratuit et rapide
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 350,  # Augmenté pour générer des bios complètes
            }
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    bio = result['choices'][0]['message']['content'].strip()
                    
                    # Nettoyer la bio : enlever les préfixes communs
                    prefixes_to_remove = [
                        f"Voici une biographie professionnelle courte et engageante pour {full_name}",
                        f"Voici une biographie professionnelle pour {full_name}",
                        f"Biographie professionnelle pour {full_name}",
                        f"Biographie de {full_name}",
                        "Voici une biographie professionnelle",
                        "Voici une biographie",
                        "Biographie professionnelle:",
                        "Biographie:",
                    ]
                    
                    for prefix in prefixes_to_remove:
                        if bio.startswith(prefix):
                            bio = bio[len(prefix):].strip()
                            # Enlever les deux-points, guillemets, tirets qui suivent
                            bio = bio.lstrip(':"-').strip()
                    
                    # Enlever les guillemets et astérisques
                    bio = bio.strip('"').strip("'").strip('*').strip()
                    
                    # Enlever les lignes "Bonjour ! Je suis..." si présentes
                    if bio.startswith("Bonjour"):
                        # Trouver la première phrase complète après "Bonjour"
                        sentences = bio.split('.')
                        if len(sentences) > 1:
                            bio = '.'.join(sentences[1:]).strip().lstrip()
                    
                    # Enlever les préfixes avec le nom
                    if bio.startswith(f"Je suis {full_name}"):
                        bio = bio[len(f"Je suis {full_name}"):].strip().lstrip(',.-')
                    elif bio.startswith(f"{full_name} est"):
                        # Garder cette structure car c'est naturel
                        pass
                    
                    # Nettoyer les espaces multiples
                    bio = ' '.join(bio.split())
                    
                    # Détecter et corriger les phrases incomplètes
                    if bio and len(bio) > 20:
                        # Détecter si la bio est coupée (se termine par des mots indicatifs d'incomplétude)
                        incomplete_indicators = ['traduisent', 'explore', 'développe', 'continue', 'réfléchit', 'cherche']
                        last_words = ' '.join(bio.split()[-5:]).lower()
                        
                        # Si la bio se termine par "..." ou une phrase incomplète
                        is_incomplete = bio.endswith("...") or any(indicator in last_words for indicator in incomplete_indicators)
                        
                        if is_incomplete:
                            # Trouver la dernière phrase complète
                            sentences = bio.rstrip('...').split('.')
                            complete_sentences = []
                            
                            for sentence in sentences:
                                sentence = sentence.strip()
                                if sentence and not any(word in sentence.lower().split()[-3:] for word in incomplete_indicators):
                                    complete_sentences.append(sentence)
                            
                            if complete_sentences:
                                bio = '. '.join(complete_sentences) + '.'
                            else:
                                # Si aucune phrase complète, prendre tout jusqu'à l'avant-dernière phrase
                                if len(sentences) > 1:
                                    bio = '. '.join(sentences[:-1]).strip() + '.'
                        
                        # S'assurer que la bio se termine par une ponctuation appropriée
                        if bio and not bio.endswith('.') and not bio.endswith('!') and not bio.endswith('?'):
                            # Vérifier que ce n'est pas une phrase incomplète
                            if not any(word in bio.lower().split()[-3:] for word in incomplete_indicators):
                                bio = bio.rstrip('.') + '.'
                        
                        return bio
            else:
                logger.warning(f"Erreur Groq API: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion Groq: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue Groq: {str(e)}")
        
        return None
    
    @staticmethod
    def _generate_with_huggingface(prompt):
        """
        Génère une bio en utilisant HuggingFace Inference API
        Utilise un modèle français ou un modèle de texte-to-text en français
        """
        try:
            # Modèles français disponibles sur HuggingFace (gratuits)
            # Essayons d'abord un modèle de génération français
            models_to_try = [
                "dbmdz/gpt2-french-small",  # GPT-2 français
                "microsoft/DialoGPT-medium",  # Alternative
            ]
            
            for model_name in models_to_try:
                try:
                    url = f"{HUGGINGFACE_API_URL}/{model_name}"
                    
                    headers = {}
                    if HUGGINGFACE_API_KEY:
                        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_KEY}"
                    
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 150,
                            "temperature": 0.8,
                            "do_sample": True,
                            "top_p": 0.95,
                            "repetition_penalty": 1.2,
                        }
                    }
                    
                    response = requests.post(url, headers=headers, json=payload, timeout=15)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and len(result) > 0:
                            generated_text = result[0].get('generated_text', '')
                            # Extraire la bio (enlever le prompt initial)
                            if prompt in generated_text:
                                bio = generated_text.replace(prompt, '').strip()
                            else:
                                bio = generated_text.strip()
                            
                            # Vérifier que la bio a du sens et n'est pas juste une répétition
                            if bio and len(bio) > 20 and len(bio.split()) > 3:
                                return bio
                    elif response.status_code == 503:
                        # Modèle en chargement, passer au suivant
                        continue
                except:
                    # Erreur avec ce modèle, essayer le suivant
                    continue
            
            # Si aucun modèle ne fonctionne, retourner None pour utiliser le générateur intelligent
            return None
                
        except Exception as e:
            logger.error(f"Erreur HuggingFace: {str(e)}")
            return None
    
    @staticmethod
    def _generate_fallback_bio(user, keywords):
        """
        Génère une bio variée et intelligente si l'API échoue
        Utilise des templates variés pour éviter la répétition
        """
        import random
        
        full_name = user.get_full_name()
        role = user.role
        
        # Templates variés pour générer des bios différentes (neutre/genre)
        templates = [
            f"{full_name} est un {role} passionné qui aime partager ses expériences et apprendre de nouvelles choses.",
            f"{full_name} est un {role} dynamique et créatif, toujours prêt à explorer de nouveaux horizons.",
            f"{full_name} est un {role} enthousiaste qui cherche constamment à s'améliorer et à contribuer positivement.",
            f"{full_name} est un {role} curieux et ouvert d'esprit, passionné par la découverte et l'échange.",
            f"{full_name} est un {role} engagé qui croit en la collaboration et au partage de connaissances.",
            f"{full_name} est un {role} qui valorise l'apprentissage continu et les échanges constructifs.",
            f"Passionné par l'innovation, {full_name} est un {role} toujours à la recherche de nouvelles opportunités.",
        ]
        
        # Si des mots-clés sont fournis, personnaliser la bio
        if keywords:
            keywords_str = ", ".join(keywords)
            customized_templates = [
                f"{full_name} est un {role} passionné par {keywords_str} et toujours prêt à partager ses connaissances.",
                f"{full_name} est un {role} spécialisé dans {keywords_str}, cherchant à créer et partager de la valeur.",
                f"Passionné par {keywords_str}, {full_name} est un {role} qui aime explorer de nouvelles perspectives et apprendre continuellement.",
                f"{full_name} combine ses intérêts pour {keywords_str} avec sa passion pour l'innovation et le partage.",
                f"{full_name} est un {role} expert en {keywords_str} qui aime transmettre son savoir et découvrir de nouvelles choses.",
            ]
            templates.extend(customized_templates)
        
        # Choisir un template aléatoirement pour varier
        return random.choice(templates)


class FraudDetectionService:
    """
    Service pour détecter les comptes suspects et frauduleux
    Utilise Groq AI pour une analyse intelligente
    """
    
    @staticmethod
    def analyze_user(user):
        """
        Analyse un utilisateur pour détecter les signaux de fraude/suspicion
        Combine analyse locale et IA pour un score de confiance
        
        Args:
            user: Instance CustomUser
            
        Returns:
            dict: {
                'confidence_score': int (0-100),  # 100 = très fiable, 0 = très suspect
                'risk_level': str ('trusted', 'normal', 'suspicious', 'high_risk'),
                'factors': list,
                'ai_analysis': str,  # Analyse IA détaillée
                'recommendations': list
            }
        """
        from django.utils import timezone
        from datetime import timedelta
        
        factors = []
        risk_points = 0
        max_risk = 100
        
        # ========== ANALYSE LOCALE (Signaux rapides) ==========
        
        # 1. Analyse de l'email
        email_risk = FraudDetectionService._analyze_email(user.email)
        if email_risk['risk']:
            risk_points += email_risk['points']
            factors.append(email_risk['reason'])
        
        # 2. Analyse du username
        username_risk = FraudDetectionService._analyze_username(user.username)
        if username_risk['risk']:
            risk_points += username_risk['points']
            factors.append(username_risk['reason'])
        
        # 3. Ancienneté du compte
        days_old = (timezone.now() - user.date_joined).days
        if days_old < 1:
            risk_points += 15
            factors.append(_("Compte créé il y a moins de 24h"))
        elif days_old < 7:
            risk_points += 5
            factors.append(_("Compte très récent (< 7 jours)"))
        else:
            # Points de confiance pour les comptes anciens
            risk_points = max(0, risk_points - 10)
        
        # 4. Vérification email
        if not user.verified:
            risk_points += 10
            factors.append(_("Email non vérifié"))
        else:
            risk_points = max(0, risk_points - 5)  # Bonus confiance
        
        # 5. Activité
        if not user.last_login:
            risk_points += 15
            factors.append(_("Jamais connecté après inscription"))
        elif user.last_login:
            days_since_login = (timezone.now() - user.last_login).days
            if days_since_login > 180:
                risk_points += 10
                factors.append(_("Aucune activité depuis 6 mois"))
        
        # 6. Complétude du profil
        if not user.bio and not user.profilePicture:
            risk_points += 5
            factors.append(_("Profil incomplet (pas de bio ni photo)"))
        
        # 7. Analyse de la bio (si présente)
        if user.bio:
            bio_risk = FraudDetectionService._analyze_bio(user.bio)
            if bio_risk['risk']:
                risk_points += bio_risk['points']
                factors.append(bio_risk['reason'])
        
        # Limiter les points de risque
        risk_points = min(risk_points, max_risk)
        
        # Calculer le score de confiance (inverse du risque)
        confidence_score = max(0, 100 - risk_points)
        
        # Déterminer le niveau
        if confidence_score >= 80:
            risk_level = 'trusted'
        elif confidence_score >= 60:
            risk_level = 'normal'
        elif confidence_score >= 40:
            risk_level = 'suspicious'
        else:
            risk_level = 'high_risk'
        
        # ========== ANALYSE IA (Groq) - Pour TOUS les comptes ==========
        ai_analysis = None
        ai_recommendations = []
        ai_confidence_override = None  # Score IA peut overrider le score local
        
        if GROQ_API_KEY:
            # Utiliser l'IA pour TOUS les comptes pour une vraie analyse intelligente
            ai_result = FraudDetectionService._analyze_with_ai(user, factors, risk_points, confidence_score)
            if ai_result:
                ai_analysis = ai_result.get('analysis', '')
                ai_recommendations = ai_result.get('recommendations', [])
                # Si l'IA fournit un score, l'utiliser (plus intelligent)
                if ai_result.get('confidence_score') is not None:
                    ai_confidence_override = ai_result['confidence_score']
                    confidence_score = ai_confidence_override
                    # Recalculer le niveau avec le score IA
                    if confidence_score >= 80:
                        risk_level = 'trusted'
                    elif confidence_score >= 60:
                        risk_level = 'normal'
                    elif confidence_score >= 40:
                        risk_level = 'suspicious'
                    else:
                        risk_level = 'high_risk'
        
        # Recommandations automatiques basées sur le niveau (fallback si pas d'IA)
        recommendations = ai_recommendations if ai_recommendations else []
        if not recommendations:
            if risk_level == 'high_risk':
                recommendations.append(_("Compte à haut risque - Suspension recommandée"))
                recommendations.append(_("Vérification manuelle obligatoire"))
                recommendations.append(_("Contacter l'utilisateur pour vérification"))
            elif risk_level == 'suspicious':
                recommendations.append(_("Surveiller l'activité de près"))
                recommendations.append(_("Vérifier l'authenticité des informations"))
            
            if not user.verified:
                recommendations.append(_("Demander la vérification d'email"))
        
        return {
            'confidence_score': confidence_score,
            'risk_level': risk_level,
            'factors': factors,
            'ai_analysis': ai_analysis,
            'recommendations': recommendations[:5]  # Limiter à 5
        }
    
    @staticmethod
    def _analyze_email(email):
        """Analyse l'email pour détecter des patterns suspects"""
        email_lower = email.lower()
        
        # Patterns suspects
        suspicious_patterns = [
            email_lower.startswith('test'),
            email_lower.startswith('temp'),
            email_lower.startswith('fake'),
            'spam' in email_lower,
            'temp' in email_lower.split('@')[0],
            email.count('+') > 2,
            email.count('.') > 4,
            len(email.split('@')[0]) > 30,
            email.split('@')[1] in ['tempmail.com', '10minutemail.com', 'guerrillamail.com'],
        ]
        
        if any(suspicious_patterns):
            return {
                'risk': True,
                'points': 20,
                'reason': _("Email avec pattern suspect détecté")
            }
        
        # Emails avec chiffres séquentiels
        username_part = email.split('@')[0]
        if len(username_part) > 3 and username_part[-3:].isdigit():
            return {
                'risk': True,
                'points': 10,
                'reason': _("Email avec pattern généré automatiquement")
            }
        
        return {'risk': False, 'points': 0, 'reason': ''}
    
    @staticmethod
    def _analyze_username(username):
        """Analyse le username pour détecter des patterns suspects"""
        username_lower = username.lower()
        
        # Patterns suspects
        suspicious_patterns = [
            username_lower.startswith('user_'),
            username_lower.startswith('test'),
            username_lower.startswith('temp'),
            len(username) > 20,
            username.count('_') > 3,
            username.count('.') > 2,
        ]
        
        if any(suspicious_patterns):
            return {
                'risk': True,
                'points': 10,
                'reason': _("Username avec pattern suspect")
            }
        
        # Nombres séquentiels à la fin
        if len(username) > 3 and username[-4:].isdigit():
            return {
                'risk': True,
                'points': 15,
                'reason': _("Username généré automatiquement détecté")
            }
        
        return {'risk': False, 'points': 0, 'reason': ''}
    
    @staticmethod
    def _analyze_bio(bio):
        """Analyse la bio pour détecter du spam ou contenu suspect"""
        bio_lower = bio.lower()
        
        # Mots-clés spam/fraude
        spam_keywords = [
            'bitcoin', 'crypto', 'free money', 'click here', 'winner',
            'congratulations', 'urgent', 'act now', 'limited time',
            'investment opportunity', 'get rich', 'work from home', 'make money'
        ]
        
        spam_found = [keyword for keyword in spam_keywords if keyword in bio_lower]
        if spam_found:
            return {
                'risk': True,
                'points': 25,
                'reason': _(f"Bio contient des mots-clés suspects: {', '.join(spam_found[:2])}")
            }
        
        # Liens suspects
        if 'http://' in bio or 'https://' in bio:
            return {
                'risk': True,
                'points': 15,
                'reason': _("Bio contient des liens - vérification recommandée")
            }
        
        return {'risk': False, 'points': 0, 'reason': ''}
    
    @staticmethod
    def _analyze_with_ai(user, factors, risk_points, current_confidence):
        """
        Utilise Groq AI pour analyser le compte de manière intelligente
        L'IA calcule son propre score de confiance basé sur une analyse contextuelle
        """
        if not GROQ_API_KEY:
            return None
        
        try:
            from django.utils import timezone
            
            # Préparer les données pour l'IA
            days_old = (timezone.now() - user.date_joined).days
            last_login_info = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Jamais connecté"
            days_since_login = (timezone.now() - user.last_login).days if user.last_login else None
            
            prompt = f"""
Tu es un expert en détection de fraude pour plateformes web. Analyse ce compte utilisateur et détermine un score de confiance (0-100).

Informations complètes du compte:
- Email: {user.email}
- Username: {user.username}
- Nom complet: {user.get_full_name()}
- Compte créé: il y a {days_old} jours ({user.date_joined.strftime("%Y-%m-%d")})
- Dernière connexion: {last_login_info} {'(il y a ' + str(days_since_login) + ' jours)' if days_since_login else ''}
- Email vérifié: {'Oui' if user.verified else 'Non'}
- Compte actif: {'Oui' if user.is_active else 'Non'}
- Bio: {user.bio[:150] if user.bio else 'Aucune bio'}
- Photo de profil: {'Oui' if user.profilePicture else 'Non'}
- Statut: {user.status}

Signaux détectés automatiquement: {', '.join(factors[:7]) if factors else 'Aucun signal détecté'}
Score de base calculé: {current_confidence}/100

Instructions:
1. Analyse le compte de manière holistique et contextuelle
2. Considère les patterns suspects (emails temporaires, usernames générés, etc.)
3. Considère les signaux positifs (compte ancien, activité régulière, profil complet)
4. Calcule un score de confiance IA (0-100) où:
   - 80-100 = Trusted (compte très fiable)
   - 60-79 = Normal (compte normal, quelques points à vérifier)
   - 40-59 = Suspicious (plusieurs signaux suspects)
   - 0-39 = High Risk (compte très suspect, probablement frauduleux)

5. Fournis une analyse détaillée (2-4 phrases) expliquant ton évaluation
6. Donne 2-3 recommandations d'action concrètes

Réponds UNIQUEMENT en JSON valide:
{{
    "confidence_score": 85,
    "analysis": "analyse détaillée ici expliquant pourquoi ce score",
    "recommendations": ["reco1", "reco2", "reco3"]
}}
"""
            
            messages = [
                {
                    "role": "system",
                    "content": "Tu es un expert en détection de fraude pour plateformes web. Tu analyses les comptes utilisateurs de manière intelligente et contextuelle. Tu fournis toujours un score de confiance (0-100), une analyse détaillée et des recommandations en JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "temperature": 0.4,  # Équilibre entre créativité et précision
                "max_tokens": 400,
            }
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_text = result['choices'][0]['message']['content'].strip()
                    
                    # Essayer d'extraire du JSON de la réponse
                    json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group())
                            # Extraire le score de confiance IA
                            ai_confidence = parsed.get('confidence_score')
                            if ai_confidence is not None:
                                # S'assurer que c'est un entier entre 0-100
                                ai_confidence = max(0, min(100, int(ai_confidence)))
                            
                            return {
                                'confidence_score': ai_confidence,
                                'analysis': parsed.get('analysis', ai_text),
                                'recommendations': parsed.get('recommendations', [])
                            }
                        except json.JSONDecodeError as e:
                            logger.warning(f"Erreur parsing JSON IA: {str(e)}")
                        except Exception as e:
                            logger.warning(f"Erreur extraction score IA: {str(e)}")
                    
                    # Si pas de JSON valide, retourner l'analyse texte quand même
                    return {
                        'confidence_score': None,
                        'analysis': ai_text,
                        'recommendations': []
                    }
        except Exception as e:
            logger.error(f"Erreur analyse IA fraude: {str(e)}")
        
        return None
