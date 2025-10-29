from typing import List
import re
import requests
from django.conf import settings


def get_generation_prompt(tag_count: int) -> str:
    """Génère un prompt adaptatif selon le nombre de tags demandé"""
    count_desc = {
        1: "1 tag SEULEMENT (le plus important et pertinent)",
        2: "2 tags maximum (les plus importants et pertinents)",
        3: "3 tags maximum (les plus importants et pertinents)"
    }
    
    return (
        f"Tu es un assistant expert qui extrait des tags de noms/substantifs pour un agenda personnel. "
        f"Règles ULTRA-STRICTES : "
        f"- Extrais {count_desc[tag_count]} "
        f"- PRIORITÉ ABSOLUE : UNIQUEMENT des noms concrets, objets, concepts, genres, types, catégories "
        f"- Exemples de tags prioritaires : feuilletons, romance, drame, école, travail, famille, santé, sport, voyage, projet "
        f"- INTERDICTION TOTALE : "
        f"  * JAMAIS d'expressions d'opinion (j'aime, j'adore, je préfère, j'aime bien, j'aime les) "
        f"  * JAMAIS de verbes (marcher, manger, faire, aller, regarder, être, avoir) "
        f"  * JAMAIS d'adjectifs (beau, bon, grand, petit, turques, français) "
        f"  * JAMAIS de mots vides (le, la, les, un, une, des, et, ou, mais, avec, dans) "
        f"- Corrige l'orthographe des mots mal écrits (feuilleon → feuilletons) "
        f"- Choisis UNIQUEMENT les mots qui représentent des CONCEPTS ou OBJETS concrets "
        f"- Format : liste JSON en minuscules, sans accents ni dièses "
        f"- Évite les doublons et mots génériques "
        f"Texte: "
    )  


def _dedupe_and_normalize(candidates: List[str]) -> List[str]:
    normalized = []
    seen = set()
    
    # Corrections d'orthographe courantes
    corrections = {
        'feuilleon': 'feuilletons',
        'feuilleons': 'feuilletons',
        'feuileton': 'feuilletons',
        'romance': 'romance',
        'drame': 'drame',
        'ecole': 'école',
        'etude': 'étude',
        'famille': 'famille',
        'travail': 'travail',
        'sante': 'santé',
        'medecin': 'médecin',
        'rendez-vous': 'rendez-vous',
        'projet': 'projet',
        'voyage': 'voyage',
        'sport': 'sport'
    }
    
    for c in candidates:
        tag = re.sub(r"[^\w\s-]", "", c).strip().lower()
        tag = re.sub(r"\s+", " ", tag)
        if not tag:
            continue
            
        # Appliquer les corrections d'orthographe
        tag = corrections.get(tag, tag)
        
        # Ignorer les expressions d'opinion et mots vides
        if tag in ['aime', 'adore', 'prefere', 'j-aime', 'j-adore', 'j-prefere', 'aime-bien', 'j-aime-bien']:
            continue
            
        if tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return normalized[:30]


def suggest_tags_from_text(text: str, tag_count: int = 2) -> List[str]:
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if api_key:
        try:
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-1.5-flash:generateContent?key=" + api_key
            )
            prompt = get_generation_prompt(tag_count)
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"text": f"Texte:\n{text}"},
                        ]
                    }
                ],
            }
            resp = requests.post(endpoint, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # Extract text
            candidates = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            # Try to parse JSON list; if not, split by commas/newlines
            tags: List[str] = []
            try:
                import json

                parsed = json.loads(candidates)
                if isinstance(parsed, list):
                    tags = [str(x) for x in parsed]
            except Exception:
                tags = re.split(r"[,\n]", candidates)
            return _dedupe_and_normalize(tags)[:tag_count]
        except Exception:
            pass

    # Fallback simple heuristic without external API
    # extract frequent words > 3 chars
    words = re.findall(r"[A-Za-zÀ-ÿ0-9-]{4,}", text.lower())
    stop = {
        # Mots vides et articles
        'avec','sans','dans','pour','cette','cela','comme','mais','alors','donc','parce','quand','tous','tout','très','plus','moins',
        'elle','elles','il','ils','nous','vous','que','qui','quoi','quel','dont','sur','sous','entre','vers','chez','une','des','les','aux',
        # Expressions d'opinion - PRIORITÉ ABSOLUE
        'aime','adore','prefere','aime-bien','j-aime','j-adore','j-prefere','j-aime-bien','j-aime-les','aime-les',
        # Verbes communs
        'marcher','manger','faire','aller','regarder','voir','ecouter','parler','dire','etre','avoir',
        # Adjectifs communs
        'beau','bon','grand','petit','nouveau','vieux','jeune','bonne','belle','grande','petite','turques','francais','français',
        # Mots génériques
        'the','and','this','that','from','into','your','avec','chose','truc','machin'
    }
    freq = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return _dedupe_and_normalize([w for w, _ in sorted_words[:tag_count]])


