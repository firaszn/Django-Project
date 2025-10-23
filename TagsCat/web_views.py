from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import models
import json
from .models import Category, Tag
from .forms import CategoryForm, TagForm

@login_required
def category_list(request):
    """Liste des catégories de l'utilisateur"""
    categories = Category.objects.filter(user=request.user).order_by('name')
    return render(request, 'TagsCat/category_list.html', {
        'categories': categories
    })

@login_required
def category_create(request):
    """Créer une nouvelle catégorie"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Catégorie "{category.name}" créée avec succès!')
            return redirect('TagsCat:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'TagsCat/category_form.html', {
        'form': form,
        'title': 'Créer une catégorie'
    })

@login_required
def category_edit(request, pk):
    """Modifier une catégorie"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Catégorie "{category.name}" modifiée avec succès!')
            return redirect('TagsCat:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'TagsCat/category_form.html', {
        'form': form,
        'title': f'Modifier la catégorie "{category.name}"',
        'category': category
    })

@login_required
def category_delete(request, pk):
    """Supprimer une catégorie"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category_name = category.name
        entry_count = category.get_entry_count()
        category.delete()
        messages.success(request, f'Catégorie "{category_name}" supprimée avec succès!')
        if entry_count > 0:
            messages.info(request, f'{entry_count} entrée(s) ont été déliées de cette catégorie.')
        return redirect('TagsCat:category_list')
    
    return render(request, 'TagsCat/category_confirm_delete.html', {
        'category': category
    })

@login_required
def tag_list(request):
    """Liste des tags de l'utilisateur"""
    tags = Tag.objects.filter(user=request.user).order_by('-usage_count', 'name')
    return render(request, 'TagsCat/tag_list.html', {
        'tags': tags
    })

@login_required
def tag_create(request):
    """Créer un nouveau tag"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            tag.save()
            messages.success(request, f'Tag "{tag.name}" créé avec succès!')
            return redirect('TagsCat:tag_list')
    else:
        form = TagForm()
    
    return render(request, 'TagsCat/tag_form.html', {
        'form': form,
        'title': 'Créer un tag'
    })

@login_required
def tag_edit(request, pk):
    """Modifier un tag"""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tag "{tag.name}" modifié avec succès!')
            return redirect('TagsCat:tag_list')
    else:
        form = TagForm(instance=tag)
    
    return render(request, 'TagsCat/tag_form.html', {
        'form': form,
        'title': f'Modifier le tag "{tag.name}"',
        'tag': tag
    })

@login_required
def tag_delete(request, pk):
    """Supprimer un tag"""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    if request.method == 'POST':
        tag_name = tag.name
        entry_count = tag.entries.count()
        tag.delete()
        messages.success(request, f'Tag "{tag_name}" supprimé avec succès!')
        if entry_count > 0:
            messages.info(request, f'{entry_count} entrée(s) ont été déliées de ce tag.')
        return redirect('TagsCat:tag_list')
    
    return render(request, 'TagsCat/tag_confirm_delete.html', {
        'tag': tag
    })

@login_required
def dashboard(request):
    """Tableau de bord avec statistiques"""
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Statistiques
    total_categories = categories.count()
    total_tags = tags.count()
    categories_with_entries = categories.filter(entries__isnull=False).distinct().count()
    most_used_tag = tags.order_by('-usage_count').first()
    most_used_category = categories.annotate(
        entry_count=models.Count('entries')
    ).order_by('-entry_count').first()
    
    return render(request, 'TagsCat/dashboard.html', {
        'total_categories': total_categories,
        'total_tags': total_tags,
        'categories_with_entries': categories_with_entries,
        'most_used_tag': most_used_tag,
        'most_used_category': most_used_category,
        'recent_categories': categories.order_by('-created_at')[:5],
        'popular_tags': tags.order_by('-usage_count')[:10]
    })
