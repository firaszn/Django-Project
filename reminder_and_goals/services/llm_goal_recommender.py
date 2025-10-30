import json
import logging
import os
from typing import List, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


GEMINI_MODEL = getattr(settings, 'GOAL_GEMINI_MODEL', 'gemini-latest')
MODEL_FALLBACKS = [
    'gemini-latest',
    'gemini-2.0-flash',
    'gemini-flash-latest',
    'gemini-pro-latest',
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
    'gemini-1.5-flash-8b',
]


def _gemini_prompt(journal_title: str, journal_text: str) -> str:
    return (
        "You are a helpful coaching assistant. Read the journal entry and propose exactly 6 or 7 actionable,"
        " personalized goals derived from the user's own words. Output strict JSON with this schema: {\n"
        "  \"goals\": [\n"
        "    { \"title\": string, \"description\": string, \"category\": string }\n"
        "  ]\n"
        "}.\n"
        "Guidelines: Make them specific, meaningful, and not generic. Reflect the user's themes, pains, and desires."
        f"\nJournal Title: {journal_title}\nJournal Text: {journal_text}"
    )


def generate_with_gemini(journal_title: str, journal_text: str) -> List[Dict[str, str]]:
    api_key = getattr(settings, 'GOAL_GEMINI_API_KEY', None) or os.getenv('GOAL_GEMINI_API_KEY')
    if not api_key:
        logger.info("[LLM] Gemini API key not configured; skipping LLM generation")
        return []

    headers = {"Content-Type": "application/json"}
    prompt = _gemini_prompt(journal_title, journal_text)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "candidateCount": 1,
            "maxOutputTokens": 1024
        }
    }

    def _call_model(model_name: str) -> List[Dict[str, str]]:
        # Accept either 'gemini-xxx' or 'models/gemini-xxx' and normalize
        normalized = model_name.split('/', 1)[1] if model_name.startswith('models/') else model_name
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{normalized}:generateContent?key={api_key}"
        logger.info(f"[LLM] Calling Gemini model='{model_name}' with prompt chars={len(prompt)}")
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        logger.info(f"[LLM] Gemini HTTP status={resp.status_code} for model='{model_name}' (normalized='{normalized}')")
        resp.raise_for_status()
        data = resp.json()
        text = (
            data.get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
        )
        logger.info(f"[LLM] Gemini returned text chars={len(text)}")
        # Attempt to extract JSON block
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            # Try to find a JSON object within markdown/backticks
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None
        goals = []
        if parsed and isinstance(parsed, dict):
            items = parsed.get('goals') or []
            for i, g in enumerate(items):
                title = str(g.get('title', '')).strip()
                if not title:
                    continue
                # Vary confidence: first goal gets highest, then decrease slightly
                base_confidence = 0.85 - (i * 0.05)  # 0.85, 0.80, 0.75, 0.70, 0.65, 0.60
                goals.append({
                    'title': title[:255],
                    'description': str(g.get('description', '')).strip(),
                    'category': str(g.get('category', '')).strip() or None,
                    'confidence': max(0.55, base_confidence),  # floor at 0.55
                })
        # Cap at 5
        logger.info(f"[LLM] Parsed {len(goals)} goals from Gemini response")
        return goals[:6]

    # Try requested model, then fallbacks on 404/Not Found
    tried = []
    for model in [GEMINI_MODEL] + [m for m in MODEL_FALLBACKS if m != GEMINI_MODEL]:
        try:
            tried.append(model)
            return _call_model(model)
        except requests.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 404:
                logger.warning(f"[LLM] Model '{model}' not found (404). Trying next fallback if available...")
                continue
            logger.error(f"[LLM] Gemini call failed for model '{model}': {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"[LLM] Gemini call failed for model '{model}': {e}", exc_info=True)
            return []

    logger.error(f"[LLM] All Gemini model attempts failed. Tried: {tried}")
    return []


