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
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django import forms
from django.conf import settings
import requests


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
    journals = Journal.objects.filter(user=request.user, hidden=False).prefetch_related('related_goals', 'images')
    
    context = {
        'journals': journals,
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


@login_required
def journal_create(request):
    """Create a new journal entry."""
    if request.method == 'POST':
        form = JournalForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            # If no entry_date provided, use today
            if not form.cleaned_data.get('entry_date'):
                journal.entry_date = timezone.localdate()
            else:
                journal.entry_date = form.cleaned_data.get('entry_date')
            journal.save()


            # Handle multiple images
            images = request.FILES.getlist('images')
            for img in images:
                JournalImage.objects.create(journal=journal, image=img)

            messages.success(request, 'Journal entry created.')
            return redirect('journal_detail', journal_id=journal.id)
    else:
        form = JournalForm(user=request.user)

    return render(request, 'journal/journal_form.html', {'form': form, 'create': True})


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
        journal.delete()
        messages.success(request, 'Journal entry deleted.')
        return redirect('journal_list')

    return render(request, 'journal/journal_confirm_delete.html', {'journal': journal})


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
    gemini_model = getattr(settings, 'GEMINI_MODEL', os.environ.get('GEMINI_MODEL', 'models/text-bison-001'))
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
                    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta2/{gemini_model}:generateText?key={gemini_key}"
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


    