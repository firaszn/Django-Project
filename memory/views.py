from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Memory, MemoryPhoto
from TagsCat.models.tag import Tag
from .forms import MemoryForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.conf import settings
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# Optional spaCy support for better offline suggestions
try:
    import spacy
    SPACY_AVAILABLE = True
    _spacy_nlp = None
except Exception:
    SPACY_AVAILABLE = False
    _spacy_nlp = None

def get_spacy_nlp():
    """Lazy-load a small spaCy model (fr or en) if available."""
    global _spacy_nlp
    if _spacy_nlp is not None:
        return _spacy_nlp
    if not SPACY_AVAILABLE:
        return None
    # choose model based on project language, fall back to en
    lang = getattr(settings, 'LANGUAGE_CODE', 'en') or 'en'
    model = 'fr_core_news_sm' if str(lang).lower().startswith('fr') else 'en_core_web_sm'
    try:
        _spacy_nlp = spacy.load(model)
        return _spacy_nlp
    except Exception:
        try:
            _spacy_nlp = spacy.load('en_core_web_sm')
            return _spacy_nlp
        except Exception:
            return None

def suggest_with_spacy(text):
    """Return (title, tags) using spaCy if model available, or None."""
    nlp = get_spacy_nlp()
    if not nlp:
        return None
    try:
        doc = nlp(text)
        # Title: first sentence's non-stop lemmas (up to 6 words)
        title = ''
        for sent in doc.sents:
            tokens = [t.lemma_ for t in sent if not t.is_stop and t.is_alpha]
            if tokens:
                title = ' '.join(tokens[:6])
                break
        if not title:
            title = ' '.join([t.lemma_ for t in doc[:6] if not t.is_stop and t.is_alpha])

        # Tags: lemmatized nouns/proper nouns, frequency-ranked
        candidates = [token.lemma_.lower() for token in doc if token.pos_ in ('NOUN', 'PROPN') and not token.is_stop and token.is_alpha and len(token.text) >= 4]
        freq = {}
        for c in candidates:
            freq[c] = freq.get(c, 0) + 1
        tags = [t for t, c in sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])) )][:6]
        return title.strip(), tags
    except Exception:
        return None


@login_required
def memory_management(request):
    """List memories for current user, support filtering by tag (?tag=Travel) and date (?date=YYYY-MM-DD), with pagination."""
    qs = Memory.objects.filter(user=request.user).order_by('-date', '-created_at')
    tag = request.GET.get('tag')
    date = request.GET.get('date')
    if tag:
        qs = qs.filter(tags__name__iexact=tag)
    if date:
        qs = qs.filter(date=date)

    paginator = Paginator(qs, 6)  # 6 memories per page
    page = request.GET.get('page')
    memories = paginator.get_page(page)

    total_memories = qs.count()
    total_photos = MemoryPhoto.objects.filter(memory__user=request.user).count()

    return render(request, 'memory/memory_management.html', {
        'memories': memories,
        'total_memories': total_memories,
        'total_photos': total_photos,
    })


@login_required
def memory_create(request):
    if request.method == 'POST':
        # include files in the form processing so any file-based validators run
        form = MemoryForm(request.POST, request.FILES)
        if form.is_valid():
            # validate tags and uploaded photo before saving
            tag_input = request.POST.get('tags_input', '')
            tag_names = [n.strip() for n in tag_input.split(',') if n.strip()]
            photo_file = request.FILES.get('photo')
            has_error = False

            # Tag limits
            MAX_TAGS = 8
            if len(tag_names) > MAX_TAGS:
                form.add_error(None, f"Vous pouvez ajouter au maximum {MAX_TAGS} tags.")
                has_error = True
            for name in tag_names:
                if len(name) < 2:
                    form.add_error(None, f"Le tag '{name}' est trop court (min 2 caractères).")
                    has_error = True
                if len(name) > 50:
                    form.add_error(None, f"Le tag '{name}' est trop long (max 50 caractères).")
                    has_error = True

            # Photo validation (single file)
            MAX_SIZE = 5 * 1024 * 1024  # 5 MB
            if photo_file:
                content_type = getattr(photo_file, 'content_type', '')
                if not content_type.startswith('image/'):
                    form.add_error(None, f"Le fichier {photo_file.name} n'est pas une image valide.")
                    has_error = True
                if photo_file.size > MAX_SIZE:
                    form.add_error(None, f"Le fichier {photo_file.name} dépasse la taille maximale de 5MB.")
                    has_error = True

            if has_error:
                # render form with errors
                return render(request, 'memory/memory_form.html', {'form': form, 'action': 'create'})

            # all validations passed: save memory
            memory = form.save(commit=False)
            memory.user = request.user
            memory.save()
            # create/get tags and attach
            tag_objs = []
            if tag_names:
                for raw_name in tag_names:
                    name = raw_name.lower()
                    try:
                        tag, created = Tag.objects.get_or_create(user=request.user, name=name)
                    except Exception:
                        continue
                    if created:
                        tag.usage_count = 1
                        tag.save()
                    else:
                        tag.increment_usage()
                    tag_objs.append(tag)
            if tag_objs:
                memory.tags.set(tag_objs)
            else:
                form.save_m2m()

            # save single photo if provided
            if photo_file:
                MemoryPhoto.objects.create(memory=memory, image=photo_file)

            messages.success(request, 'Souvenir créé avec succès')
            return redirect('memory:memory_detail', pk=memory.pk)
    else:
        form = MemoryForm()

    return render(request, 'memory/memory_form.html', {'form': form, 'action': 'create'})


@login_required
def memory_edit(request, pk):
    memory = get_object_or_404(Memory, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MemoryForm(request.POST, request.FILES, instance=memory)
        if form.is_valid():
            # validate tags and file before saving
            tag_input = request.POST.get('tags_input', '')
            tag_names = [n.strip() for n in tag_input.split(',') if n.strip()]
            photo_file = request.FILES.get('photo')
            has_error = False
            MAX_TAGS = 8
            if len(tag_names) > MAX_TAGS:
                form.add_error(None, f"Vous pouvez ajouter au maximum {MAX_TAGS} tags.")
                has_error = True
            for name in tag_names:
                if len(name) < 2:
                    form.add_error(None, f"Le tag '{name}' est trop court (min 2 caractères).")
                    has_error = True
                if len(name) > 50:
                    form.add_error(None, f"Le tag '{name}' est trop long (max 50 caractères).")
                    has_error = True

            MAX_SIZE = 5 * 1024 * 1024
            if photo_file:
                content_type = getattr(photo_file, 'content_type', '')
                if not content_type.startswith('image/'):
                    form.add_error(None, f"Le fichier {photo_file.name} n'est pas une image valide.")
                    has_error = True
                if photo_file.size > MAX_SIZE:
                    form.add_error(None, f"Le fichier {photo_file.name} dépasse la taille maximale de 5MB.")
                    has_error = True

            if has_error:
                return render(request, 'memory/memory_form.html', {'form': form, 'memory': memory, 'action': 'edit'})

            memory = form.save()
            # Sync tags from comma-separated input
            old_tags = list(memory.tags.all())
            new_tag_objs = []
            if tag_names:
                for raw_name in tag_names:
                    name = raw_name.lower()
                    try:
                        tag, created = Tag.objects.get_or_create(user=request.user, name=name)
                    except Exception:
                        continue
                    new_tag_objs.append(tag)
            # set m2m
            memory.tags.set(new_tag_objs)
            # update usage counts
            old_set = set(t.pk for t in old_tags)
            new_set = set(t.pk for t in new_tag_objs)
            for t in new_tag_objs:
                if t.pk not in old_set:
                    t.increment_usage()
            for t in old_tags:
                if t.pk not in new_set:
                    t.decrement_usage()

            # add new photo if provided
            if photo_file:
                MemoryPhoto.objects.create(memory=memory, image=photo_file)

            messages.success(request, 'Souvenir mis à jour')
            return redirect('memory:memory_detail', pk=memory.pk)
    else:
        form = MemoryForm(instance=memory)

    return render(request, 'memory/memory_form.html', {'form': form, 'memory': memory, 'action': 'edit'})


@login_required
def memory_detail(request, pk):
    memory = get_object_or_404(Memory, pk=pk, user=request.user)
    photos = memory.photos.all()
    return render(request, 'memory/memory_detail.html', {'memory': memory, 'photos': photos})


@login_required
def memory_delete(request, pk):
    memory = get_object_or_404(Memory, pk=pk, user=request.user)
    if request.method == 'POST':
        memory.delete()
        messages.success(request, 'Souvenir supprimé')
        return redirect('memory:memory_management')

    return render(request, 'memory/memory_confirm_delete.html', {'memory': memory})


@login_required
@require_POST
def memory_photo_delete(request, pk, photo_pk):
    memory = get_object_or_404(Memory, pk=pk, user=request.user)
    photo = get_object_or_404(MemoryPhoto, pk=photo_pk, memory=memory)
    # Only owner can delete
    if photo.memory.user != request.user:
        return HttpResponseForbidden()
    photo.delete()
    messages.success(request, 'Photo supprimée')
    return redirect('memory:memory_edit', pk=memory.pk)


@login_required
def memory_ai_suggest(request):
    """Return AI-based suggestions (title and tags) for a given description.

    If OpenAI is configured (OPENAI_API_KEY in settings or env and openai library installed),
    use it. Otherwise fall back to a simple heuristic.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    description = request.POST.get('description') or request.POST.get('desc') or ''
    if not description:
        return JsonResponse({'error': 'Description manquante'}, status=400)

    # Try OpenAI if available and key present
    api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    if OPENAI_AVAILABLE and api_key:
        try:
            openai.api_key = api_key
            # Stronger system/user prompt to force clean JSON and short titles
            system_msg = (
                "You are a JSON-only generator. Read a user's memory description and produce a short, catchy title (3-6 words) and up to 6 relevant tags."
                " Output ONLY valid JSON with two keys: \"title\" (string) and \"tags\" (array of strings)."
                " Do not add any extra explanation, commentary or markdown. Keep tags short (single words) and in lowercase."
            )
            user_msg = "Description:\n" + description
            resp = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{'role': 'system', 'content': system_msg}, {'role': 'user', 'content': user_msg}],
                max_tokens=150,
                temperature=0.6,
            )
            text = resp['choices'][0]['message']['content']
            # Attempt to parse JSON from the model output robustly
            import json, re
            m = re.search(r'\{[\s\S]*\}', text)
            if m:
                try:
                    obj = json.loads(m.group(0))
                    title = obj.get('title', '') or ''
                    tags = obj.get('tags', []) or []
                    if isinstance(tags, str):
                        tags = [t.strip().lower() for t in tags.split(',') if t.strip()]
                    tags = [t.lower() for t in tags][:6]
                    # normalize title: trim to 6 words
                    title = ' '.join(title.split()[:6]).strip()
                    return JsonResponse({'title': title, 'tags': tags})
                except Exception:
                    # fallthrough to simpler parsing
                    pass
            # If parsing failed, try to extract a short line from the raw text
            single_line = text.strip().split('\n')[0]
            title_guess = ' '.join(single_line.split()[:6])
            return JsonResponse({'title': title_guess, 'tags': []})
        except Exception:
            # fallback silently to heuristic below
            pass

        # If spaCy is available, try it before the simple heuristic
        if SPACY_AVAILABLE:
            try:
                spacy_result = suggest_with_spacy(description)
                if spacy_result:
                    title, tags = spacy_result
                    return JsonResponse({'title': title, 'tags': tags})
            except Exception:
                pass

    # Improved fallback heuristic: short title from first meaningful sentence, and tag extraction by simple frequency
    import re
    txt = description.strip()
    # pick the first non-empty sentence-like fragment
    parts = [p.strip() for p in re.split(r'[\.\n\!\?]+', txt) if p.strip()]
    first_sent = parts[0] if parts else txt
    words = re.findall(r"[\wÀ-ÿ'-]+", first_sent)
    # build a readable title of up to 6 words
    title = ' '.join(words[:6]).strip()

    # tag candidates: take all words length>=4, lowercase, count frequency across whole description
    tokens = [w.lower() for w in re.findall(r"[\wÀ-ÿ'-]{4,}", txt)]
    # small bilingual stoplist
    stop = set([ 'avec','les','une','des','le','la','et','que','pour','qui','ont','été',
                 'that','this','have','from','will','your','about','there','their','what' ])
    freq = {}
    for t in tokens:
        clean = t.strip("'\"")
        if clean in stop: continue
        freq[clean] = freq.get(clean, 0) + 1

    # sort by frequency then length, pick top 6
    sorted_tags = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))
    tags = [t for t,c in sorted_tags][:6]

    return JsonResponse({'title': title, 'tags': tags})
