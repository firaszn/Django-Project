from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Memory, MemoryPhoto
from TagsCat.models.tag import Tag
from .forms import MemoryForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden


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
