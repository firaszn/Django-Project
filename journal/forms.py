from django import forms
from .models import Journal


class JournalForm(forms.ModelForm):
    """ModelForm for Journal. File uploads are handled in the view via request.FILES.getlist('images')."""

    entry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Choose a date for this entry or leave empty to use today.'
    )

    # Allow description to be optional (Quill will provide HTML; server-side sanitization will handle empty content)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 8}))

    class Meta:
        model = Journal
        fields = ['title', 'description', 'entry_date', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 8}),
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'location': forms.TextInput(attrs={'placeholder': 'Location (optional)'}),
        }

    def clean_entry_date(self):
        data = self.cleaned_data.get('entry_date')
        if not data:
            # if user didn't pick a date, we'll leave it None so view can set default
            return None
        return data
