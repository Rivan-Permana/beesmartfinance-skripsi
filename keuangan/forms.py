from django import forms
from .models import Keuangan

class KeuanganForm(forms.ModelForm):
    class Meta:
        model = Keuangan
        fields = '__all__'
        widgets = {
            'tanggal': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'deskripsi': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis': forms.Select(attrs={'class': 'form-control'}),
            'jumlah': forms.NumberInput(attrs={'class': 'form-control'}),
        }
