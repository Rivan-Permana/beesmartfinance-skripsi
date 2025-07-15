from django import forms
from .models import Jemputan

class JemputanForm(forms.ModelForm):
    class Meta:
        model = Jemputan
        fields = '__all__'
        widgets = {
            'nama_supir': forms.TextInput(attrs={'class': 'form-control'}),
            'no_kendaraan': forms.TextInput(attrs={'class': 'form-control'}),
            'kapasitas': forms.NumberInput(attrs={'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
