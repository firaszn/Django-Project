from django import forms
from .models import Category, Tag
from .ai_utils import generate_icon_from_number

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
                'placeholder': 'Numéro d\'icône (1-30)'
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
        self.fields['icon'].help_text = 'Saisissez un numéro entre 1 et 30 (1=Maison, 2=Travail, 3=École, etc.)'
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
        Valide et génère automatiquement l'icône basée sur le numéro saisi.
        """
        icon_input = self.cleaned_data.get('icon', '').strip()
        
        if not icon_input:
            # Si aucun numéro n'est fourni, utiliser l'icône par défaut
            return 'fas fa-folder'
        
        # Générer l'icône basée sur le numéro
        generated_icon = generate_icon_from_number(icon_input)
        
        # Valider que le numéro est dans la plage valide (1-30)
        try:
            icon_number = int(icon_input)
            if icon_number < 1 or icon_number > 30:
                raise forms.ValidationError(
                    "Le numéro d'icône doit être entre 1 et 30. "
                    "Exemples: 1=Maison, 2=Travail, 3=École, 4=Cœur, 5=Famille..."
                )
        except ValueError:
            raise forms.ValidationError(
                "Veuillez saisir un numéro valide entre 1 et 30. "
                "Exemples: 1=Maison, 2=Travail, 3=École, 4=Cœur, 5=Famille..."
            )
        
        return generated_icon

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du tag'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom du tag'
    
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
