from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Journal, JournalImage
from reminder_and_goals.models import Goal
from .forms import JournalForm
from django.utils import timezone
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.db.models import Count
from django import forms
from django.conf import settings
import importlib
import requests
from .mood_detection import detect_mood_with_ai
from .models import AIPromptUsage
from django.utils import dateparse
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
from django.utils.html import strip_tags
import bleach
from django.views.decorators.csrf import csrf_exempt


class JournalPinForm(forms.Form):
    pin = forms.CharField(
        label='PIN',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4-digit PIN'}),
        max_length=4,
        min_length=4,
        required=True
    )

@login_required
def home(request):
    # Rediriger les admins vers leur dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'journal/home.html')

@login_required
def journal_list(request):
    """Display list of all journals for the current user"""
    # Exclude hidden entries from the general list
    qs = Journal.objects.filter(user=request.user, hidden=False).prefetch_related('related_goals', 'images')

    # Search support (GET param 'q')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    context = {
        'journals': qs,
        'search_query': q,
    }
    return render(request, 'journal/journal_list.html', context)
@login_required
def journal_detail(request, journal_id):
    """Display details of a specific journal"""
    journal = get_object_or_404(Journal, user=request.user, id=journal_id)
    
    context = {
        'journal': journal,
    }
    return render(request, 'journal/journal_detail.html', context)


@csrf_exempt  # TEMP: exempt from CSRF during debugging to unblock you — remove in production
@login_required
def journal_create(request):
    """Create a new journal entry."""
    if request.method == 'POST':
        # Debug: log incoming POST keys and description preview to help diagnose missing content
        try:
            logger.debug('journal_create POST keys=%s', list(request.POST.keys()))
            logger.debug('journal_create description preview=%s', (request.POST.get('description') or '')[:200])
        except Exception:
            pass
        form = JournalForm(request.POST, request.FILES)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            # If no entry_date provided, use today
            if not form.cleaned_data.get('entry_date'):
                journal.entry_date = timezone.localdate()
            else:
                journal.entry_date = form.cleaned_data.get('entry_date')
            
            # Sanitize HTML description (we allow a small set of formatting tags)
            if journal.description:
                ALLOWED_TAGS = [
                    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li',
                    'a', 'h1', 'h2', 'h3', 'blockquote', 'code', 'pre'
                ]
                ALLOWED_ATTRS = {
                    'a': ['href', 'title', 'rel', 'target'],
                }
                try:
                    journal.description = bleach.clean(journal.description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
                except Exception:
                    # If bleach isn't available for some reason, fall back to stripping tags
                    journal.description = strip_tags(journal.description)

                # Detect mood from plain text (strip tags for more reliable classification)
                plain = strip_tags(journal.description)
                if plain:
                    mood_result = _detect_mood_internal(plain)
                    journal.mood = mood_result.get('mood', 'neutral')
            
            journal.save()

            # Debug: log saved description length so we can confirm persistence
            try:
                logger.debug('journal saved id=%s description_len=%d', getattr(journal, 'id', None), len((journal.description or '').strip()))
            except Exception:
                logger.exception('Failed to log saved journal description length')

            # Handle multiple images
            images = request.FILES.getlist('images')
            for img in images:
                JournalImage.objects.create(journal=journal, image=img)

            # Generate a short, empathetic closing reflection via AI (best-effort)
            try:
                plain_for_ai = strip_tags(journal.description or '')[:1200]
                # Stronger instruction: produce a concise personalized analysis followed by a concrete suggestion.
                # IMPORTANT: do NOT end with a question — produce an analysis sentence and then a clear actionable advice sentence.
                instr = (
                    "You are a thoughtful writing coach. Read the user's journal entry below and produce a short, personalized closing reflection with two parts:\n"
                    "(A) a one-sentence observational analysis that references the content (do not simply repeat the user's exact words), and\n"
                    "(B) a one-sentence, concrete piece of advice or a next step the user could try (imperative or descriptive), without phrasing it as a question.\n"
                    "Keep the tone warm, specific to the entry, and concise (about 2 short sentences total).\n\nEntry:\n" + plain_for_ai
                )

                # call AI and log raw output for debugging
                closing = _call_ai_text(instr, max_output_tokens=160, temperature=0.7)
                try:
                    dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_closing_debug.log')
                    # attempt to annotate likely provider for easier triage
                    provider = 'none'
                    if getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY')):
                        provider = 'gemini'
                    elif getattr(settings, 'OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY')):
                        provider = 'openai'
                    elif getattr(settings, 'AI_COMPLETION_API_URL', os.environ.get('AI_COMPLETION_API_URL')):
                        provider = 'generic'
                    with open(dbg_path, 'a', encoding='utf-8') as f:
                        f.write(f"{timezone.now().isoformat()} | user={getattr(request.user,'id',None)} | provider={provider} | plain_len={len(plain_for_ai)} | raw={repr(closing)[:1000]}\n")
                except Exception:
                    logger.exception('Failed to write closing debug file')

                # If AI returned something, persist it to the journal. Otherwise, use a deterministic local fallback
                closing_text = (closing or '').strip()
                if closing_text:
                    # Save the generated closing reflection into the model so it is persisted
                    try:
                        journal.closing_reflection = closing_text
                        journal.save(update_fields=['closing_reflection'])
                    except Exception:
                        # if update_fields is not supported or fails, attempt full save
                        try:
                            journal.save()
                        except Exception:
                            logger.exception('Failed to save journal closing_reflection')
                    messages.info(request, closing_text)
                else:
                    try:
                        fallback = _generate_local_closing(plain_for_ai)
                        messages.info(request, fallback)
                        # log fallback used
                        try:
                            dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_closing_debug.log')
                            with open(dbg_path, 'a', encoding='utf-8') as f:
                                f.write(f"{timezone.now().isoformat()} | user={getattr(request.user,'id',None)} | provider={provider} | fallback_used=1 | fallback={fallback[:500]}\n")
                        except Exception:
                            logger.exception('Failed to write closing fallback debug file')
                        # persist fallback as well so user sees it later
                        try:
                            journal.closing_reflection = fallback
                            journal.save(update_fields=['closing_reflection'])
                        except Exception:
                            try:
                                journal.save()
                            except Exception:
                                logger.exception('Failed to save journal fallback closing_reflection')
                    except Exception:
                        logger.exception('Local closing fallback failed')
            except Exception:
                pass

            messages.success(request, 'Journal entry created.')
            return redirect('journal_detail', journal_id=journal.id)
        else:
            # Log form errors to help debug why entries are not saved
            try:
                logger.warning('journal_create form invalid errors=%s POST_keys=%s user=%s', form.errors.as_json(), list(request.POST.keys()), getattr(request.user, 'id', None))
            except Exception:
                logger.exception('Failed to log form errors in journal_create')
            # Surface a helpful message to the user (show first field error)
            try:
                # form.errors is an ErrorDict; get first message
                first_field = next(iter(form.errors))
                first_msg = form.errors[first_field][0]
                messages.error(request, f"Form error: {first_field} - {first_msg}")
            except Exception:
                messages.error(request, 'There was a problem with your submission. Please check the form and try again.')
    else:
        # Pre-fill entry_date when provided via querystring (e.g. from calendar day click)
        initial = {}
        entry_date = request.GET.get('entry_date')
        prompt = request.GET.get('prompt')
        ai_invitation = None
        if entry_date:
            # Leave as string YYYY-MM-DD; Django DateField widget will render it correctly
            initial['entry_date'] = entry_date

        # If a prompt was chosen from home, prefill the title and prepare a personalized invitation
        if prompt:
            # record prompt usage (enforce 100-day cooldown)
            cooldown_days = getattr(settings, 'AI_PROMPT_COOLDOWN_DAYS', 100)
            cutoff = timezone.now() - timedelta(days=int(cooldown_days))
            # create usage entry if not already used recently
            already = AIPromptUsage.objects.filter(user=request.user, prompt_text=prompt, used_at__gte=cutoff).exists()
            if not already:
                try:
                    AIPromptUsage.objects.create(user=request.user, prompt_text=prompt)
                except Exception:
                    # non-fatal if DB write fails
                    pass

            initial['title'] = prompt
            # transform prompt into a gentle invitation (try AI, fallback to simple copy)
            try:
                ai_invitation = _ai_transform_prompt(prompt, request.user)
            except Exception:
                ai_invitation = None

        form = JournalForm(initial=initial)

    return render(request, 'journal/journal_form.html', {'form': form, 'create': True, 'ai_prompt': prompt if prompt else None, 'ai_invitation': ai_invitation})


@csrf_exempt  # TEMP: exempt from CSRF during debugging; remove after diagnosing CSRF config
@login_required
def journal_update(request, journal_id):
    journal = get_object_or_404(Journal, user=request.user, id=journal_id)

    if request.method == 'POST':
        form = JournalForm(request.POST, request.FILES, instance=journal, user=request.user)
        if form.is_valid():
            journal = form.save(commit=False)
            # If no entry_date provided, keep existing or use today
            if not form.cleaned_data.get('entry_date'):
                if not journal.entry_date:
                    journal.entry_date = timezone.localdate()
            else:
                journal.entry_date = form.cleaned_data.get('entry_date')
            
            # Sanitize and re-detect mood if content changed
            if journal.description:
                ALLOWED_TAGS = [
                    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li',
                    'a', 'h1', 'h2', 'h3', 'blockquote', 'code', 'pre'
                ]
                ALLOWED_ATTRS = {
                    'a': ['href', 'title', 'rel', 'target'],
                }
                try:
                    journal.description = bleach.clean(journal.description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
                except Exception:
                    journal.description = strip_tags(journal.description)

                plain = strip_tags(journal.description)
                if plain:
                    mood_result = _detect_mood_internal(plain)
                    journal.mood = mood_result.get('mood', 'neutral')
            
            journal.save()

            images = request.FILES.getlist('images')
            for img in images:
                JournalImage.objects.create(journal=journal, image=img)

            messages.success(request, 'Journal entry updated.')
            return redirect('journal_detail', journal_id=journal.id)
    else:
        form = JournalForm(instance=journal, user=request.user)

    return render(request, 'journal/journal_form.html', {'form': form, 'create': False, 'journal': journal})


@login_required
def journal_delete(request, journal_id):
    journal = get_object_or_404(Journal, user=request.user, id=journal_id)
    if request.method == 'POST':
        # Soft-delete: move to trash
        journal.soft_delete()
        messages.success(request, 'Journal entry moved to Deleted (trash).')
        return redirect('journal_list')

    return render(request, 'journal/journal_confirm_delete.html', {'journal': journal})


@login_required
def journal_deleted_list(request):
    """Show recently deleted (trashed) journals for the current user."""
    # Use all_objects to include deleted entries
    journals = Journal.all_objects.filter(user=request.user, deleted_at__isnull=False).order_by('-deleted_at').prefetch_related('images', 'related_goals')
    return render(request, 'journal/deleted_list.html', {'journals': journals})


@login_required
def journal_restore(request, journal_id):
    """Restore a trashed journal back to active state."""
    journal = get_object_or_404(Journal.all_objects, id=journal_id)
    # Ensure only owner or staff can restore
    if journal.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('journal_deleted_list')

    if request.method == 'POST':
        journal.restore()
        messages.success(request, 'Journal entry restored.')
        return redirect('journal_detail', journal_id=journal.id)

    return render(request, 'journal/journal_confirm_restore.html', {'journal': journal})


@login_required
def journal_permanent_delete(request, journal_id):
    """Permanently delete a trashed journal. This removes the DB record."""
    journal = get_object_or_404(Journal.all_objects, id=journal_id)
    if journal.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('journal_deleted_list')

    if request.method == 'POST':
        journal.permanently_delete()
        messages.success(request, 'Journal entry permanently deleted.')
        return redirect('journal_deleted_list')

    return render(request, 'journal/journal_confirm_permanent_delete.html', {'journal': journal})


@login_required
@require_POST
def journal_toggle_hide(request, journal_id):
    journal = get_object_or_404(Journal, user=request.user, id=journal_id)
    journal.hidden = not journal.hidden
    journal.save()
    state = 'hidden' if journal.hidden else 'visible'
    messages.success(request, f'Journal entry is now {state}.')
    return redirect('journal_list')


@login_required
def journal_hidden(request):
    """Prompt user for PIN; on correct PIN show hidden journals for the user."""
    if request.method == 'POST':
        form = JournalPinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            user = request.user
            # Check pin using model helper
            if user.check_journal_pin(pin):
                journals = Journal.objects.filter(user=user, hidden=True).prefetch_related('images', 'related_goals')
                return render(request, 'journal/hidden_journals_list.html', {'journals': journals})
            else:
                messages.error(request, 'Invalid PIN.')
    else:
        form = JournalPinForm()

    return render(request, 'journal/hidden_journals_prompt.html', {'form': form})


@login_required
def place_suggest(request):
    """Proxy/search endpoint for place suggestions using OpenStreetMap Nominatim.

    Query param: q
    Returns JSON list of {display_name, lat, lon}
    """
    q = request.GET.get('q')
    if not q:
        return JsonResponse([], safe=False)

    params = {
        'q': q,
        'format': 'jsonv2',
        'addressdetails': 0,
        'limit': 6,
    }
    url = 'https://nominatim.openstreetmap.org/search?' + urlencode(params)
    try:
        req = Request(url, headers={'User-Agent': 'AI-Journal-App/1.0 (+http://example.com)'} )
        with urlopen(req, timeout=5) as resp:
            data = json.load(resp)
    except Exception as e:
        return JsonResponse([], safe=False)

    results = []
    for item in data:
        results.append({
            'display_name': item.get('display_name'),
            'lat': item.get('lat'),
            'lon': item.get('lon'),
        })

    return JsonResponse(results, safe=False)


@login_required
def content_suggest(request):
    """Return autocomplete suggestions for journal content based on user's past entries.

    Query param: q
    Returns JSON list of suggestion strings (short snippets or titles).
    """
    q = request.GET.get('q')
    if not q:
        return JsonResponse([], safe=False)

    # If an AI completion provider is configured, use it to generate suggestions.
    # Support Gemini (Google Generative Language API) via GEMINI_API_KEY and GEMINI_MODEL,
    gemini_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
    gemini_model = getattr(settings, 'GEMINI_MODEL', os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash'))
    openai_key = getattr(settings, 'OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY'))
    ai_api_url = getattr(settings, 'AI_COMPLETION_API_URL', os.environ.get('AI_COMPLETION_API_URL'))

    # Collect recent entries to give context
    recent = Journal.objects.filter(user=request.user).order_by('-created_at')[:30]
    recent_texts = []
    for r in recent:
        if r.title:
            recent_texts.append(f"Title: {r.title}")
        if r.description:
            recent_texts.append(f"Desc: {r.description[:300]}")

    if openai_key or ai_api_url:
        try:
            prompt = (
                f"You are a helpful assistant that suggests short journal content completions or titles. "
                f"User typed: \"{q}\". Based on these examples of the user's previous entries:\n\n"
                + "\n".join(recent_texts[:10])
                + "\n\nProvide up to 8 short suggestions (one per line). Keep each suggestion concise (under 120 chars)."
            )

            suggestions = []

            # Try Gemini first if configured
            if gemini_key:
                try:
                    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta2/models/{gemini_model}:generateText?key={gemini_key}"
                    payload = {
                        "prompt": {"text": prompt},
                        "temperature": 0.8,
                        "maxOutputTokens": 256,
                        "candidateCount": 5
                    }
                    resp = requests.post(gemini_endpoint, json=payload, timeout=8)
                    resp.raise_for_status()
                    data = resp.json()
                    for cand in data.get('candidates', []):
                        content = cand.get('content') or cand.get('output') or ''
                        for line in str(content).splitlines():
                            s = line.strip('-• \t')
                            if s:
                                suggestions.append(s)
                except Exception:
                    # on failure, continue to other providers
                    pass

            if not suggestions and openai_key:
                model = getattr(settings, 'OPENAI_MODEL', os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'))
                headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}
                payload = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': 'You are a helpful assistant that suggests short journal content completions.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    'max_tokens': 200,
                    'temperature': 0.8,
                }
                resp = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=8)
                resp.raise_for_status()
                data = resp.json()
                text = ''
                try:
                    text = data['choices'][0]['message']['content']
                except Exception:
                    text = data.get('choices', [{}])[0].get('text', '')

                for line in text.splitlines():
                    s = line.strip('-• 	')
                    if s:
                        suggestions.append(s)
            else:
                headers = {'Content-Type': 'application/json'}
                payload = {'prompt': prompt, 'max_tokens': 200}
                resp = requests.post(ai_api_url, json=payload, headers=headers, timeout=8)
                resp.raise_for_status()
                data = resp.json()
                text = data.get('text') or data.get('completion') or data.get('result') or ''
                for line in text.splitlines():
                    s = line.strip('-• 	')
                    if s:
                        suggestions.append(s)

            # Clean and return
            out = []
            seen = set()
            for s in suggestions:
                s2 = s.strip()
                if s2 and s2 not in seen:
                    seen.add(s2)
                    out.append(s2)
                if len(out) >= 8:
                    break
            if out:
                return JsonResponse(out, safe=False)
        except Exception:
            # fallback to local method
            pass

    # Local fallback
    matches = Journal.objects.filter(user=request.user).filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    ).order_by('-created_at')[:20]

    suggestions = []
    seen = set()
    for j in matches:
        if q.lower() in (j.title or '').lower():
            s = j.title.strip()
            if s and s not in seen:
                suggestions.append(s)
                seen.add(s)
        if j.description and q.lower() in j.description.lower():
            idx = j.description.lower().find(q.lower())
            start = max(0, idx - 30)
            end = min(len(j.description), idx + 80)
            snippet = j.description[start:end].strip()
            snippet = ('...' if start>0 else '') + snippet + ('...' if end < len(j.description) else '')
            if snippet not in seen:
                suggestions.append(snippet)
                seen.add(snippet)
        if len(suggestions) >= 8:
            break

    return JsonResponse(suggestions, safe=False)


# Mood parsing and logging moved to `journal.mood_detection` to avoid
# duplicated logic and keep a single source of truth. Views call
# `detect_mood_with_ai()` (imported from `journal.mood_detection`) which
# handles parsing, retries and logging.


def _detect_mood_internal(content):
    """Wrapper for mood detection using AI exclusively (no static keywords).
    
    Returns dict: {'mood': 'happy'|'sad'|'neutral', 'confidence': float}
    """
    return detect_mood_with_ai(content)



@login_required
def detect_mood(request):
    """Detect mood from journal content using Gemini API.
    
    POST param: content
    Returns JSON: {'mood': 'happy'|'sad'|'neutral', 'confidence': float}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
    except Exception:
        content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'mood': 'neutral', 'confidence': 0.0})
    
    result = _detect_mood_internal(content)
    # Ensure confidence key exists
    result['confidence'] = float(result.get('confidence', 0.0))

    return JsonResponse(result)


@login_required
def journal_calendar_data(request):
    """Return JSON data for a monthly calendar for the logged-in user.

    Query params: year (int), month (int)
    Response: { year, month, days_in_month, days: [{day: int, count: int}, ...], message }
    """
    # Defaults to current month
    try:
        year = int(request.GET.get('year', 0))
        month = int(request.GET.get('month', 0))
    except Exception:
        year = 0
        month = 0

    today = timezone.localdate()
    if not year or not month:
        year = today.year
        month = today.month

    # Aggregate mood counts grouped by entry_date for the user (exclude trashed entries)
    from django.db.models import IntegerField, Case, When, Sum

    qs = Journal.all_objects.filter(user=request.user, deleted_at__isnull=True, entry_date__year=year, entry_date__month=month)

    grouped = qs.values('entry_date').annotate(
        happy=Sum(Case(When(mood='happy', then=1), default=0, output_field=IntegerField())),
        sad=Sum(Case(When(mood='sad', then=1), default=0, output_field=IntegerField())),
        neutral=Sum(Case(When(mood='neutral', then=1), default=0, output_field=IntegerField())),
    )

    days = []
    happy_days = 0
    sad_days = 0
    neutral_days = 0
    for item in grouped:
        d = item['entry_date']
        if d:
            h = int(item.get('happy') or 0)
            s = int(item.get('sad') or 0)
            n = int(item.get('neutral') or 0)
            days.append({'day': d.day, 'happy': h, 'sad': s, 'neutral': n})
            # count day as mood-day if any entries present; tally which mood is dominant on that day
            if h >= s and h >= n and (h or s or n):
                happy_days += 1
            elif s > h and s >= n and (h or s or n):
                sad_days += 1
            elif n > h and n > s and (h or s or n):
                neutral_days += 1

    days_written = happy_days + sad_days + neutral_days

    # Days in month
    import calendar as _calendar
    days_in_month = _calendar.monthrange(year, month)[1]

    # Encouragement message based on moods
    if happy_days >= max(20, int(days_in_month * 0.6)):
        message = "Amazing streak — you're writing happily and consistently!"
    elif happy_days >= 10:
        message = "Great — many happy entries this month. Keep it up!"
    elif sad_days > happy_days and sad_days >= 3:
        message = "You've had several sad entries recently — consider checking in with a friend or taking a short break."
    elif days_written >= 3:
        message = "Nice progress — keep writing, small steps count."
    elif days_written >= 1:
        message = "Good start — try to keep a small streak going." 
    else:
        message = "No entries this month yet. Try writing one today!"

    return JsonResponse({
        'year': year,
        'month': month,
        'days_in_month': days_in_month,
        'days': days,
        'days_written': days_written,
        'happy_days': happy_days,
        'sad_days': sad_days,
        'neutral_days': neutral_days,
        'message': message,
    })


# --- AI helper endpoints --------------------------------------------------
def _call_ai_text(prompt_text, max_output_tokens=256, temperature=0.7):
    """Call the configured AI provider (Gemini preferred, OpenAI fallback).

    This implementation mirrors the robust approach used in
    `journal/mood_detection.py`: prefer the python `google.genai`/`genai`
    client when available (tries multiple client surfaces for
    compatibility), and fall back to the REST endpoint only when the
    client path isn't available. If Gemini isn't configured or fails,
    OpenAI or a generic AI API URL will be used as a fallback.
    """
    gemini_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
    gemini_model = getattr(settings, 'GEMINI_MODEL', os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash'))
    openai_key = getattr(settings, 'OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY'))
    ai_api_url = getattr(settings, 'AI_COMPLETION_API_URL', os.environ.get('AI_COMPLETION_API_URL'))

    # Try Gemini via python client first (preferred)
    if gemini_key:
        try:
            genai = None
            client = None
            try:
                from google import genai as _genai_official
                genai = _genai_official
                try:
                    client = genai.Client()
                except Exception:
                    try:
                        client = genai.Client(api_key=gemini_key)
                    except Exception:
                        client = None
            except Exception:
                # try alternate import paths
                try:
                    genai = importlib.import_module('google.genai')
                except Exception:
                    try:
                        genai = importlib.import_module('genai')
                    except Exception:
                        genai = None

            # If the client is available, try a few generation call patterns
            if genai:
                # Attempt to use client surfaces if present
                if not client and hasattr(genai, 'Client'):
                    try:
                        client = genai.Client(api_key=gemini_key)
                    except Exception:
                        try:
                            client = genai.Client()
                        except Exception:
                            client = None

                if not client and hasattr(genai, 'configure'):
                    try:
                        genai.configure(api_key=gemini_key)
                        client = genai
                    except Exception:
                        client = None

                if client:
                    # Try known generation methods with/without temperature
                    methods = [
                        (getattr(client, 'models', None) and getattr(client.models, 'generate_content', None)),
                        getattr(client, 'generate', None),
                        getattr(client, 'generate_text', None),
                        getattr(genai, 'generate', None),
                    ]
                    for method in methods:
                        if not method:
                            continue
                        try:
                            try:
                                resp = method(model=gemini_model, contents=prompt_text, temperature=float(temperature))
                            except TypeError:
                                # some client signatures use different arg names
                                try:
                                    resp = method(model=gemini_model, prompt=prompt_text, temperature=float(temperature))
                                except TypeError:
                                    resp = method(model=gemini_model, prompt=prompt_text)
                        except Exception:
                            # try next method
                            continue

                        # Extract text from response
                        text = getattr(resp, 'text', None) or getattr(resp, 'response', None) or ''
                        if not text and isinstance(resp, dict):
                            text = resp.get('text') or resp.get('candidates', [{}])[0].get('content', '') or ''
                        if text:
                            return text

        except Exception:
            logger.exception('Gemini python client attempts failed; will try other providers')

    # OpenAI fallback
    if openai_key:
        try:
            model = getattr(settings, 'OPENAI_MODEL', os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'))
            headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You are a thoughtful, gentle writing assistant.'},
                    {'role': 'user', 'content': prompt_text},
                ],
                'max_tokens': int(max_output_tokens),
                'temperature': float(temperature),
            }
            resp = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            try:
                return data['choices'][0]['message']['content']
            except Exception:
                return data.get('choices', [{}])[0].get('text', '')
        except Exception:
            logger.exception('OpenAI call failed')

    # Generic ai_api_url fallback
    if ai_api_url:
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {'prompt': prompt_text, 'max_tokens': int(max_output_tokens)}
            resp = requests.post(ai_api_url, json=payload, headers=headers, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            return data.get('text') or data.get('result') or ''
        except Exception:
            logger.exception('Generic AI API call failed')

    return ''


def _ai_transform_prompt(prompt_text, user):
    """Transform a short prompt into a calm, personal invitation with a brief call-to-action.

    Note: we intentionally avoid adding a repeated generic follow-up question. Instead include a short, specific call-to-action
    (for example: "Try naming one small step you might take") or a gentle prompt that does not repeat the same sentence each time.
    """
    instr = (
        "Rewrite the following journal prompt as a calm, personal invitation (2-3 short sentences). "
        "Use empathetic language, make it specific to the prompt, and include a brief, concrete call-to-action rather than a generic follow-up question.\n\nPrompt:\n" + prompt_text
    )
    out = _call_ai_text(instr, max_output_tokens=200, temperature=0.7)
    return out.strip() if out else None


def _generate_local_nudge(text):
    """Content-aware local nudge generator.

    Returns a short, statement-style nudge tailored to keywords in `text`. This avoids returning the same
    generic sentence for many different entries while keeping the output deterministic and privacy-preserving.
    """
    if not text:
        return 'Notice what felt meaningful and choose one small, concrete next step to try.'

    s = text.lower()
    # pick a short snippet of the first line to personalize (cleaned)
    first_line = (text.splitlines() or [''])[0].strip()
    snippet = re.sub(r'[^0-9a-zA-Z\s]', '', first_line)
    snippet = re.sub(r'\s+', ' ', snippet).strip()
    sn = snippet if len(snippet) <= 40 else (snippet[:40].rsplit(' ', 1)[0] + '...')

    # content-driven templates (statements, not questions)
    def _pick_variant(txt, templates):
        if not templates:
            return ''
        # simple deterministic hash: sum of codepoints mod len
        try:
            total = sum(ord(c) for c in txt)
        except Exception:
            total = len(txt)
        return templates[total % len(templates)]

    if any(k in s for k in ['create', 'creative', 'creativity', 'ideas', 'idea', 'invent']):
        creativity_templates = [
            'You are exploring creativity — try listing three quick ideas in 10 minutes to build momentum.',
            'Creative energy is present — sketch or jot down one concept to expand over the week.',
            'Capture a single, tiny creative experiment to try today and note what you learn.'
        ]
        return _pick_variant(text, creativity_templates)
    if any(k in s for k in ['learn', 'reading', 'read', 'study']):
        learning_templates = [
            'You mentioned learning — schedule a 20-minute reading block this week to get started.',
            'To support learning, commit to a short, focused study window and note one takeaway.',
        ]
        return _pick_variant(text, learning_templates)
    if any(k in s for k in ['health', 'eat', 'exercise', 'diet', 'sleep', 'fitness']):
        health_templates = [
            'This is about health — pick one small habit (for example, a 10-minute walk) to try this week.',
            'Focus on one tiny, doable habit (like an extra glass of water) and track it for a few days.'
        ]
        return _pick_variant(text, health_templates)
    if any(k in s for k in ['friend', 'friends', 'family', 'relationship', 'partner']):
        relation_templates = [
            'Relationships matter — consider sending a short message to the person who came to mind.',
            'If someone came to mind, think of one small way to connect with them this week.'
        ]
        return _pick_variant(text, relation_templates)
    if any(k in s for k in ['work', 'job', 'career', 'deadline']):
        work_templates = [
            'At work — break one task into a 10-minute chunk and try that as a small next step.',
            'Identify one tiny action that moves a project forward and do it for 10 minutes.'
        ]
        return _pick_variant(text, work_templates)
    if any(k in s for k in ['happy', 'joy', 'smile', 'grateful']):
        positive_templates = [
            'You noted something positive — write down one detail to return to when you need a boost.',
            'Hold onto this uplifting moment — note one small thing you can repeat to feel this again.'
        ]
        return _pick_variant(text, positive_templates)
    if any(k in s for k in ['anxious', 'anxiety', 'nervous', 'worried', 'stress']):
        anxiety_templates = [
            'There is some worry here — try a short grounding exercise (three deep breaths) to center yourself.',
            'Notice one small step you can take to reduce immediate stress and try it now.'
        ]
        return _pick_variant(text, anxiety_templates)

    # fallback: personalized short-statement using snippet so repeated entries vary
    if sn:
        return f'About "{sn}": notice what mattered and pick one small action to try next.'

    return 'Notice what felt meaningful and choose one small, concrete next step to try.'


def _generate_local_closing(text):
    """Produce a short (2-3 sentence) local closing that includes:
    - one observational sentence about tone/behavior
    - one concise, practical suggestion
    - one gentle reflective question

    This is a deterministic fallback used when AI providers are unavailable.
    """
    t = (text or '').strip()
    if not t:
        return "Thanks for writing — what's one small thing you noticed about how you're feeling right now?"

    s = t.lower()
    # simple tone inference
    tone = 'neutral'
    if any(k in s for k in ['sad', 'upset', 'depressed', 'tear', 'cry']):
        tone = 'sad'
    elif any(k in s for k in ['anxious', 'anxiety', 'nervous', 'worried', 'stress']):
        tone = 'anxious'
    elif any(k in s for k in ['happy', 'joy', 'glad', 'excited', 'delighted', 'smile']):
        tone = 'happy'
    elif any(k in s for k in ['angry', 'frustrat', 'annoyed']):
        tone = 'frustrated'

    # observation
    if tone == 'sad':
        obs = 'You seem to be carrying some heaviness in this entry.'
    elif tone == 'anxious':
        obs = 'There is a thread of worry running through what you wrote.'
    elif tone == 'happy':
        obs = 'This writing has a bright, uplifting tone.'
    elif tone == 'frustrated':
        obs = 'I notice some frustration in your words.'
    else:
        obs = 'You described your experience clearly and thoughtfully.'

    # suggestion based on keywords
    if any(k in s for k in ['work', 'working', 'job', 'deadline']):
        sug = 'Consider one tiny, concrete step you could take next to ease the pressure (even 5 minutes helps).'
    elif any(k in s for k in ['friend', 'family', 'partner', 'relationship']):
        sug = 'Maybe try reaching out to one person you trust to share the part that mattered to you.'
    elif any(k in s for k in ['sleep', 'tired', 'exhaust']):
        sug = 'A brief rest or grounding exercise might help — try a 3-minute pause to notice your breath.'
    else:
        sug = 'Name one small action you could try in the next day that would support you.'

    # combine into two short sentences: observation + concrete suggestion (no trailing question)
    out = f"{obs} {sug}"
    return out


@login_required
def ai_prompts(request):
    """Return 3 AI-generated prompts for the home screen, excluding those used within cooldown period."""
    cooldown_days = int(getattr(settings, 'AI_PROMPT_COOLDOWN_DAYS', 100))
    cutoff = timezone.now() - timedelta(days=cooldown_days)
    used = set(AIPromptUsage.objects.filter(user=request.user, used_at__gte=cutoff).values_list('prompt_text', flat=True))

    # Ask the AI to produce 6 candidate prompts, we'll filter locally
    instruction = (
        "Generate six gentle, open-ended journal prompts for personal reflection. "
        "Each prompt should be one short sentence, empathetic and inviting. Return each prompt on its own line."
    )
    raw = _call_ai_text(instruction, max_output_tokens=300, temperature=0.8)
    prompts = []
    if raw:
        for line in str(raw).splitlines():
            s = line.strip('-• \t ')
            if s:
                prompts.append(s)

    # Fallback defaults
    if not prompts:
        prompts = [
            "Describe something that made you smile this week.",
            "Write about a small goal you want to try this month.",
            "What's been on your mind lately?",
            "Recall a kindness you witnessed recently.",
            "What are you grateful for today?",
            "Write about a moment you felt proud of yourself."
        ]

    # Normalize and filter prompts to avoid repeating identical or near-identical question templates
    import string
    def _normalize_prompt(text):
        t = text.lower()
        # remove punctuation
        t = re.sub(r'[^a-z0-9\s]', '', t)
        # collapse whitespace
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    # blacklist fragments that commonly repeat (question templates we want to avoid)
    blacklist = [
        'what about this experience',
        'what felt most',
        'what are you grateful',
        'what are you grateful for',
        'what do you notice',
    ]

    filtered = []
    seen_norm = set()
    for p in prompts:
        n = _normalize_prompt(p)
        if not n:
            continue
        skip = False
        for b in blacklist:
            if b in n:
                skip = True
                break
        if skip:
            continue
        if n in seen_norm:
            continue
        seen_norm.add(n)
        if p not in used:
            filtered.append(p)
    # Ensure at least 3 by falling back to any unique items from prompts
    if len(filtered) < 3:
        for p in prompts:
            n = _normalize_prompt(p)
            if not n or n in seen_norm:
                continue
            seen_norm.add(n)
            filtered.append(p)
            if len(filtered) >= 3:
                break

    return JsonResponse(filtered[:3], safe=False)


@csrf_exempt
@login_required
def ai_nudge(request):
    """Given a short paragraph, return a single-sentence reflective nudge.

    POST JSON: { text: '...' }
    Response: { nudge: '...' }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        text = data.get('text', '').strip()
    except Exception:
        text = request.POST.get('text', '').strip()

    if not text:
        logger.debug('ai_nudge called with empty text by user=%s', request.user)
        return JsonResponse({'nudge': ''})

    # Log incoming nudge request (truncate for privacy)
    try:
        logger.info('ai_nudge request user=%s id=%s text_len=%d text_preview=%s', request.user, getattr(request.user, 'id', None), len(text), (text[:200].replace('\n',' ')))
    except Exception:
        logger.exception('Failed to log ai_nudge request')

    # Also append to a local debug file to ensure visibility regardless of logging config
    try:
        dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_nudge_debug.log')
        preview = (text or '')[:300].replace('\n', ' ')
        with open(dbg_path, 'a', encoding='utf-8') as f:
            f.write(f"{timezone.now().isoformat()} | user={getattr(request.user, 'id', None)} | pre={preview}\n")
    except Exception:
        logger.exception('Failed to write ai_nudge debug file')

    instr = (
        "You are a gentle reflective coach. Given the user's short paragraph below, produce one concise, empathetic, reflective sentence that nudges them deeper. "
        "Keep it under 20 words and phrased as a question when appropriate.\n\nParagraph:\n" + text
    )

    try:
        out = _call_ai_text(instr, max_output_tokens=80, temperature=0.7)
        nudge = (out or '').strip().splitlines()[0] if out else ''
        logger.info('ai_nudge response user=%s nudge_len=%d preview=%s', request.user, len(nudge), (nudge[:200] if nudge else ''))
        # write raw AI output for debugging (may differ from final nudge extraction)
        try:
            dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_nudge_debug.log')
            with open(dbg_path, 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now().isoformat()} | user={getattr(request.user, 'id', None)} | raw_out_len={len(out or '')} | raw_out={repr(out)[:1000]}\n")
        except Exception:
            logger.exception('Failed to append raw ai output to debug file')
        try:
            dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_nudge_debug.log')
            nudge_preview = (nudge or '')[:400].replace('\n', ' ')
            with open(dbg_path, 'a', encoding='utf-8') as f:
                f.write(f"{timezone.now().isoformat()} | user={getattr(request.user, 'id', None)} | nudge={nudge_preview}\n")
        except Exception:
            logger.exception('Failed to append ai_nudge response to debug file')
    except Exception as e:
        logger.exception('ai_nudge processing failed: %s', e)
        nudge = ''

    # If the AI returned nothing, provide a lightweight local fallback so the feature remains useful
    if not nudge:
        try:
            fallback = _generate_local_nudge(text)
            if fallback:
                nudge = fallback
                logger.info('ai_nudge using local fallback for user=%s preview=%s', request.user, nudge[:200])
                try:
                    dbg_path = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'journal_nudge_debug.log')
                    fallback_preview = (nudge or '')[:300].replace('\n', ' ')
                    with open(dbg_path, 'a', encoding='utf-8') as f:
                        f.write(f"{timezone.now().isoformat()} | user={getattr(request.user, 'id', None)} | fallback_used=1 | fallback={fallback_preview}\n")
                except Exception:
                    logger.exception('Failed to append fallback debug info')
        except Exception:
            # keep nudge empty if fallback fails
            logger.exception('Local fallback nudge generation failed')

    return JsonResponse({'nudge': nudge})


@login_required
def journal_garden(request):
    """Render the garden visualization page."""
    return render(request, 'journal/garden.html')


@login_required
def journal_garden_data(request):
    """Return JSON summary of recent journals for the logged-in user.

    Query params:
      days (int) - number of days back to include (default 180)
    """
    try:
        days = int(request.GET.get('days', 180))
    except Exception:
        days = 180

    cutoff = timezone.now() - timedelta(days=days)
    qs = Journal.objects.filter(user=request.user, created_at__gte=cutoff).order_by('-created_at')[:500]

    out = []
    for j in qs:
        desc = (j.description or '')
        plain = strip_tags(desc)
        word_count = len(plain.split()) if plain.strip() else 0
        snippet = plain.strip()[:140]
        tags = []
        try:
            tags = list(j.tags.values_list('name', flat=True))
        except Exception:
            tags = []

        out.append({
            'id': j.id,
            'title': j.title or '',
            'entry_date': j.entry_date.isoformat() if j.entry_date else None,
            'created_at': j.created_at.isoformat() if j.created_at else None,
            'mood': j.mood or 'neutral',
            'tags': tags,
            'word_count': word_count,
            'snippet': snippet,
            'closing_reflection': (j.closing_reflection or '')[:300],
        })

    return JsonResponse(out, safe=False)


@login_required
def journal_garden_3d(request):
    """Render the 3D garden page (Three.js-based)."""
    return render(request, 'journal/garden_3d.html')


    