from typing import List
import re
import requests
from django.conf import settings


GENERATION_PROMPT = (
    "Tu es un assistant qui extrait des tags de noms/substantifs pour un agenda personnel. "
    "Règles strictes : "
    "- Extrais SEULEMENT les noms, lieux, objets, concepts (ex: école, étude, amour, travail, santé, famille) "
    "- IGNORE tous les verbes (marcher, manger, faire, aller, etc.) "
    "- Corrige l'orthographe des mots mal écrits "
    "- Propose 3 à 6 tags maximum "
    "- Format : liste JSON en minuscules, sans accents ni dièses "
    "- Évite les doublons et mots vides "
    "Texte: "
)


def _dedupe_and_normalize(candidates: List[str]) -> List[str]:
    normalized = []
    seen = set()
    for c in candidates:
        tag = re.sub(r"[^\w\s-]", "", c).strip().lower()
        tag = re.sub(r"\s+", " ", tag)
        if not tag:
            continue
        if tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return normalized[:30]


def suggest_tags_from_text(text: str) -> List[str]:
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if api_key:
        try:
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-1.5-flash:generateContent?key=" + api_key
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": GENERATION_PROMPT},
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
            return _dedupe_and_normalize(tags)
        except Exception:
            pass

    # Fallback simple heuristic without external API
    # extract frequent words > 3 chars
    words = re.findall(r"[A-Za-zÀ-ÿ0-9-]{4,}", text.lower())
    stop = {
        'avec','sans','dans','pour','avec','cette','cela','comme','mais','alors','donc','parce','quand','tous','tout','très','plus','moins',
        'elle','elles','il','ils','nous','vous','que','qui','quoi','quel','dont','sur','sous','entre','vers','chez','une','des','les','aux','the','and','this','that','from','into','your','avec'
    }
    freq = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return _dedupe_and_normalize([w for w, _ in sorted_words[:10]])


