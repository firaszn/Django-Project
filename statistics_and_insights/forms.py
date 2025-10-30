from django import forms
from .models import CustomReport, AIGeneratedReport

class CustomReportForm(forms.ModelForm):
    class Meta:
        model = CustomReport
        fields = ['title', 'description', 'report_type', 'date_range_start', 'date_range_end']
        widgets = {
            'date_range_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_range_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('date_range_start')
        end_date = cleaned_data.get('date_range_end')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("La date de début doit être avant la date de fin.")
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("La période ne peut pas dépasser 1 an.")
        
        return cleaned_data

class AIGeneratedReportForm(forms.ModelForm):
    """Formulaire pour les rapports IA (principalement en lecture)"""
    class Meta:
        model = AIGeneratedReport
        fields = ['title', 'report_type', 'period_start', 'period_end']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'report_type': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'period_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': 'readonly'}),
            'period_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': 'readonly'}),
        }