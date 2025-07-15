from django import forms
from .models import Katering

class KateringForm(forms.ModelForm):
    class Meta:
        model = Katering
        fields = '__all__'
        widgets = {
            'tanggal': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'menu': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'jumlah_porsi': forms.NumberInput(attrs={'class': 'form-control'}),
            'keterangan': forms.TextInput(attrs={'class': 'form-control'}),
            'katering': forms.Select(attrs={'class': 'form-control'}),
        }
