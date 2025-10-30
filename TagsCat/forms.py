from django import forms
from .models import Category, Tag

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color', 'icon', 'description', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#4a90e2'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'icône (ex: heart, home, work, school...)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (optionnel)'
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom de la catégorie'
        self.fields['color'].label = 'Couleur'
        self.fields['icon'].label = 'Icône'
        self.fields['icon'].help_text = 'Saisissez le nom de l\'icône FontAwesome (ex: heart, home, briefcase, graduation-cap, users, etc.)'
        self.fields['description'].label = 'Description'
        self.fields['tags'].label = 'Tags associés'
        
        # Filtrer les tags pour cet utilisateur
        if self.user:
            self.fields['tags'].queryset = Tag.objects.filter(user=self.user).order_by('name')
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and self.user:
            # Vérifier l'unicité pour cet utilisateur
            existing = Category.objects.filter(user=self.user, name__iexact=name.strip())
            if self.instance and self.instance.pk:
                # Si on modifie une catégorie existante, exclure cette instance
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"Une catégorie avec le nom '{name}' existe déjà. "
                    "Veuillez choisir un nom différent."
                )
        return name
    
    def clean_icon(self):
        """
        Valide le nom de l'icône FontAwesome saisi.
        """
        icon_input = self.cleaned_data.get('icon', '').strip()
        
        if not icon_input:
            # Si aucune icône n'est fournie, utiliser l'icône par défaut
            return 'folder'
        
        # Nettoyer le nom de l'icône (supprimer les préfixes s'ils existent)
        icon_name = icon_input.lower()
        
        # Supprimer les préfixes courants si présents
        prefixes_to_remove = ['fas fa-', 'far fa-', 'fab fa-', 'fa-', 'fa ']
        for prefix in prefixes_to_remove:
            if icon_name.startswith(prefix):
                icon_name = icon_name[len(prefix):]
                break
        
        # Liste des icônes populaires et valides pour validation
        valid_icons = [
            'home', 'heart', 'briefcase', 'graduation-cap', 'users', 'dumbbell', 'plane', 
            'utensils', 'film', 'book', 'music', 'gamepad', 'shopping-cart', 'car', 
            'hospital', 'calendar', 'gift', 'camera', 'laptop', 'coffee', 'tree', 
            'paint-brush', 'tools', 'bicycle', 'dog', 'star', 'lightbulb', 'money-bill',
            'envelope', 'phone', 'folder', 'tag', 'clock', 'map', 'key', 'shield',
            'fire', 'leaf', 'sun', 'moon', 'cloud', 'bolt', 'snowflake', 'umbrella',
            'anchor', 'rocket', 'gem', 'crown', 'trophy', 'medal', 'flag', 'bell',
            'headphones', 'microphone', 'video', 'image', 'file', 'folder-open',
            'save', 'download', 'upload', 'share', 'link', 'paperclip', 'scissors',
            'pen', 'pencil', 'eraser', 'ruler', 'calculator', 'chart-bar', 'chart-pie',
            'chart-line', 'table', 'list', 'th', 'th-list', 'search', 'filter',
            'sort', 'eye', 'eye-slash', 'lock', 'unlock', 'user', 'user-plus',
            'user-minus', 'user-check', 'user-times', 'cog', 'cogs', 'wrench',
            'hammer', 'magic', 'wand-sparkles', 'palette', 'brush', 'spray-can'
        ]
        
        # Validation basique du format
        if not icon_name.replace('-', '').replace('_', '').isalnum():
            raise forms.ValidationError(
                "Le nom de l'icône ne peut contenir que des lettres, chiffres, tirets et underscores. "
                "Exemples: heart, home, briefcase, graduation-cap"
            )
        
        # Avertissement si l'icône n'est pas dans la liste des icônes courantes
        if icon_name not in valid_icons:
            # On n'empêche pas l'utilisation, mais on avertit
            pass  # L'utilisateur peut utiliser n'importe quelle icône FontAwesome
        
        return icon_name

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du tag'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#FF6B6B'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom du tag'
        self.fields['color'].label = 'Couleur'
        self.fields['color'].help_text = 'Couleur automatique si vide'
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and self.user:
            # Vérifier l'unicité pour cet utilisateur
            existing = Tag.objects.filter(user=self.user, name__iexact=name.strip())
            if self.instance and self.instance.pk:
                # Si on modifie un tag existant, exclure cette instance
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"Un tag avec le nom '{name}' existe déjà. "
                    "Veuillez choisir un nom différent."
                )
        return name
