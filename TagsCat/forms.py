from django import forms
from .models import Category, Tag

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color', 'icon', 'description']
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
                'placeholder': 'Icône (optionnel)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (optionnel)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nom de la catégorie'
        self.fields['color'].label = 'Couleur'
        self.fields['icon'].label = 'Icône'
        self.fields['description'].label = 'Description'
    
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
