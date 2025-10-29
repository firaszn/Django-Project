from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput
import datetime
from .models import Memory


class MemoryForm(forms.ModelForm):
    """Form for Memory with basic validation for user input.

    - title: required, 2-120 chars
    - description: optional but longer than 5 chars if provided
    - tags: handled separately in the view via `tags_input` hidden field
    """
    class Meta:
        model = Memory
        fields = ['title', 'description', 'date', 'tags']
        # Use HTML5 date input for better UX on desktop and mobile
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        if not title or not title.strip():
            raise ValidationError("Le titre est requis.")
        title = title.strip()
        if len(title) < 2:
            raise ValidationError("Le titre doit contenir au moins 2 caractères.")
        if len(title) > 120:
            raise ValidationError("Le titre ne peut pas dépasser 120 caractères.")
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description', '')
        if desc:
            desc = desc.strip()
            if len(desc) < 6:
                raise ValidationError("La description doit contenir au moins 6 caractères si fournie.")
        return desc
