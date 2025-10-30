"""
AI-powered mood detection using Gemini (no static keyword lists).
"""
import json
import os
import logging
import importlib
import traceback
from django.conf import settings


def parse_mood_json(text):
    """Parse JSON mood response from model output.
    
    Returns tuple (label, confidence) or None if parsing fails.
    """
    if not text:
        return None
    try:
        txt = str(text).strip()
        start = txt.find('{')
        end = txt.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        json_str = txt[start:end+1]
        parsed = json.loads(json_str)
        label = str(parsed.get('label', '')).lower().strip()
        if label not in ('happy', 'sad', 'neutral'):
            return None
        try:
            confidence = float(parsed.get('confidence', 0.0))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5
        return (label, confidence)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def log_mood_detection(content, mood_text, raw_response, final_mood, confidence):
    """Optional logging helper for mood detection debugging."""
    try:
        from django.utils import timezone as dj_tz
        log_path = os.path.join(settings.BASE_DIR, 'journal_mood_debug.log')
        minimal = {
            'timestamp': dj_tz.now().isoformat(),
            'content_snippet': str(content)[:200],
            'final_mood': final_mood,
            'confidence': confidence,
        }
        try:
            with open(log_path, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(minimal) + '\n')
        except Exception:
            pass

        logger = logging.getLogger('journal.mood_detection')
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            sh = logging.StreamHandler()
            sh.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s'))
            logger.addHandler(sh)

        if getattr(settings, 'LOG_MOOD_RAW_RESPONSES', False) or os.environ.get('FORCE_LOG_MOOD', '0') == '1' or getattr(settings, 'DEBUG', False):
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        logger.info(json.dumps(minimal))

        if getattr(settings, 'LOG_MOOD_RAW_RESPONSES', False) or os.environ.get('FORCE_LOG_MOOD', '0') == '1':
            full = {
                'timestamp': dj_tz.now().isoformat(),
                'content_snippet': str(content)[:200],
                'mood_text': str(mood_text)[:200],
                'final_mood': final_mood,
                'confidence': confidence,
                'raw_response': raw_response,
            }
            try:
                with open(log_path, 'a', encoding='utf-8') as fh:
                    fh.write(json.dumps({'detail': full}) + '\n')
            except Exception:
                pass
            logger.debug(json.dumps({'detail': full}))
    except Exception:
        # Never fail the main flow because of logging
        pass


def detect_mood_with_ai(content):
    """Detect mood using Gemini AI exclusively (no static keyword lists).
    
    Returns dict: {'mood': 'happy'|'sad'|'neutral', 'confidence': float}
    """
    if not content or not content.strip():
        return {'mood': 'neutral', 'confidence': 0.0}

    gemini_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
    if not gemini_key:
        return {'mood': 'neutral', 'confidence': 0.0, 'error': 'No API key configured'}

    gemini_model = getattr(settings, 'GEMINI_MOOD_MODEL', os.environ.get('GEMINI_MOOD_MODEL', 'gemini-2.5-flash'))

    enhanced_prompt = f"""You are an expert sentiment analyst. Read the journal entry below and return EXACTLY one valid JSON object (and nothing else).

RESPONSE FORMAT (json only):
{{"label": "happy" OR "sad" OR "neutral", "confidence": <number 0.0-1.0>}}

RULES (must follow):
1) Choose 'happy' for clearly positive emotions (joy, excitement, relief, gratitude, contentment).
2) Choose 'sad' for clearly negative emotions OR when the entry expresses exhaustion, overwhelm, loneliness, despair, persistent stress, hopelessness, crying, or other signs of negative mental state — even if the writer doesn't use the word "sad".
   Examples of indirect sad signals: "tired", "exhausted", "drained", "empty", "couldn't sleep", "couldn't get out of bed", "I cried", "feeling distant", "overwhelmed", "so stressed I can't think".
3) Choose 'neutral' only for purely factual, descriptive, or balanced entries that do not convey a dominant positive or negative emotional tone.
4) If emotions are mixed, pick the dominant overall tone. If truly balanced, pick 'neutral'.
5) Confidence should reflect your certainty. Use high values (>=0.9) for clear cases, 0.5-0.8 for moderate, <0.5 for ambiguous.

FEW-SHOT EXAMPLES (input -> output):
"I had a wonderful day, I felt joyful after meeting friends." -> {{"label": "happy", "confidence": 0.95}}
"I felt lonely and disappointed today, everything went wrong." -> {{"label": "sad", "confidence": 0.92}}
"Today was a long day, I felt tired and exhausted and nothing went as planned." -> {{"label": "sad", "confidence": 0.85}}
"I felt stressed and overwhelmed at work, very hard and frustrating day." -> {{"label": "sad", "confidence": 0.88}}
"I went to the store and did some chores. Nothing notable." -> {{"label": "neutral", "confidence": 0.90}}
"The meeting was okay, some good points and some concerns were raised." -> {{"label": "neutral", "confidence": 0.75}}
"I was anxious but it turned out fine and I felt relieved." -> {{"label": "happy", "confidence": 0.70}}
"Not a bad day, actually felt pretty good about things." -> {{"label": "happy", "confidence": 0.80}}
"I couldn't get out of bed today, I felt empty and cried a few times." -> {{"label": "sad", "confidence": 0.92}}
"I've been so drained and overwhelmed, nothing helps." -> {{"label": "sad", "confidence": 0.90}}

Now analyze this journal entry and return ONLY the JSON (no extra text):

{content[:2000]}

JSON Output:"""

    raw_response = {}
    attempts = []

    try:
        # First attempt: use the official sample usage from Google when possible.
        # This prefers `from google import genai` and the simple Client() surface.
        client = None
        genai = None
        try:
            from google import genai as _genai_official
            genai = _genai_official
            # official sample constructs client with no args
            try:
                client = genai.Client()
            except Exception:
                # If that fails, try passing the api key explicitly
                try:
                    client = genai.Client(api_key=gemini_key)
                except Exception:
                    client = None

            if client is not None:
                # simple _call_model using the documented sample method
                def _call_model(prompt_text):
                    # official sample: client.models.generate_content(model=..., contents=...)
                    return client.models.generate_content(model=gemini_model, contents=prompt_text)
        except Exception:
            # Fallback: try a more resilient import path and construction for other layouts
            try:
                genai = importlib.import_module('google.genai')
            except Exception:
                genai = importlib.import_module('genai')

            client = None
            # Try common construction patterns (keep compatibility)
            if hasattr(genai, 'Client'):
                try:
                    client = genai.Client(api_key=gemini_key)
                except TypeError:
                    try:
                        client = genai.Client()
                    except Exception:
                        client = None
                    if client is None and hasattr(genai, 'configure'):
                        try:
                            genai.configure(api_key=gemini_key)
                            client = genai
                        except Exception:
                            pass

            if client is None and hasattr(genai, 'client') and hasattr(genai.client, 'Client'):
                try:
                    client = genai.client.Client(api_key=gemini_key)
                except TypeError:
                    try:
                        client = genai.client.Client()
                    except Exception:
                        client = None

            if client is None and hasattr(genai, 'configure'):
                try:
                    genai.configure(api_key=gemini_key)
                    client = genai
                except Exception:
                    pass

            if client is None:
                module_attrs = []
                try:
                    module_attrs = sorted([a for a in dir(genai) if not a.startswith('_')])
                except Exception:
                    module_attrs = ['(unable to list attributes)']
                err = {'error': 'Unsupported genai package layout', 'available_attrs': module_attrs[:60]}
                logger = logging.getLogger('journal.mood_detection')
                try:
                    logger.error('Unsupported genai package layout; top-level attributes: %s', module_attrs[:60])
                except Exception:
                    pass
                raw_response['error'] = err
                log_mood_detection(content, '', raw_response, 'neutral', 0.0)
                return {'mood': 'neutral', 'confidence': 0.0, 'error': 'Unsupported genai package layout; see server logs. Install the official google-genai package.'}

        def _call_model(prompt_text):
            # Prefer client.models.generate_content(model=..., contents=...)
            # We attempt calls with temperature when supported; if the signature
            # rejects it (TypeError), retry without the temperature kwarg. This
            # handles variations in google-genai versions where temperature may
            # not be accepted.
            try:
                # client.models.generate_content
                if hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
                    try:
                        return client.models.generate_content(model=gemini_model, contents=prompt_text, temperature=0.0)
                    except TypeError:
                        return client.models.generate_content(model=gemini_model, contents=prompt_text)

                # client.generate
                if hasattr(client, 'generate'):
                    try:
                        return client.generate(model=gemini_model, prompt=prompt_text, temperature=0.0)
                    except TypeError:
                        return client.generate(model=gemini_model, prompt=prompt_text)

                # client.generate_text
                if hasattr(client, 'generate_text'):
                    try:
                        return client.generate_text(model=gemini_model, prompt=prompt_text, temperature=0.0)
                    except TypeError:
                        return client.generate_text(model=gemini_model, prompt=prompt_text)

                # module-level genai.generate
                if hasattr(genai, 'generate'):
                    try:
                        return genai.generate(model=gemini_model, prompt=prompt_text, temperature=0.0)
                    except TypeError:
                        return genai.generate(model=gemini_model, prompt=prompt_text)
            except Exception:
                # Bubble up other exceptions to be handled by outer except
                raise
            raise RuntimeError('No supported generation method found on genai client')

        gen_resp = _call_model(enhanced_prompt)

        mood_text = getattr(gen_resp, 'text', '') or getattr(gen_resp, 'response', '') or ''
        if not mood_text and isinstance(gen_resp, dict):
            mood_text = gen_resp.get('text') or gen_resp.get('candidates', [{}])[0].get('content', '') or ''

        attempts.append({'attempt': 1, 'raw_text': mood_text[:500]})
        raw_response['first_attempt'] = str(gen_resp) if not isinstance(gen_resp, dict) else gen_resp

        parsed_result = parse_mood_json(mood_text)
        if parsed_result:
            label, confidence = parsed_result
            raw_response['parsed_successfully'] = True
            log_mood_detection(content, mood_text, raw_response, label, confidence)
            return {'mood': label, 'confidence': float(confidence)}

        retry_prompt = f"""Return EXACTLY one JSON object and nothing else.

Format: {{"label": "happy"|"sad"|"neutral", "confidence": <0.0-1.0>}}

IMPORTANT: If the text contains negative emotional signals (including exhaustion, overwhelm, loneliness,
crying, inability to function, hopelessness, persistent stress, or similar), prefer 'sad' rather than
defaulting to 'neutral'. Only choose 'neutral' if the entry is purely factual or clearly balanced.

Analyze the emotional tone of the following journal entry and respond ONLY with the JSON:

{content[:2000]}

JSON only:"""

        gen_resp2 = _call_model(retry_prompt)
        mood_text2 = getattr(gen_resp2, 'text', '') or getattr(gen_resp2, 'response', '') or ''
        if not mood_text2 and isinstance(gen_resp2, dict):
            mood_text2 = gen_resp2.get('text') or gen_resp2.get('candidates', [{}])[0].get('content', '') or ''

        attempts.append({'attempt': 2, 'raw_text': mood_text2[:500]})
        raw_response['second_attempt'] = str(gen_resp2) if not isinstance(gen_resp2, dict) else gen_resp2

        parsed_result = parse_mood_json(mood_text2)
        if parsed_result:
            label, confidence = parsed_result
            raw_response['parsed_successfully'] = True
            log_mood_detection(content, mood_text2, raw_response, label, confidence)
            return {'mood': label, 'confidence': float(confidence)}

        raw_response['parsing_failed'] = True
        raw_response['all_attempts'] = attempts
        log_mood_detection(content, mood_text2, raw_response, 'neutral', 0.1)
        return {'mood': 'neutral', 'confidence': 0.1, 'note': 'AI parsing failed, defaulting to neutral'}

    except Exception as e:
        raw_response['error'] = str(e)
        raw_response['traceback'] = traceback.format_exc()
        logger = logging.getLogger('journal.mood_detection')
        try:
            logger.error('Mood detection exception: %s', str(e))
            logger.debug(raw_response.get('traceback', ''))
        except Exception:
            pass
        log_mood_detection(content, '', raw_response, 'neutral', 0.0)
        return {'mood': 'neutral', 'confidence': 0.0, 'error': str(e)}



