from django import forms
from .models import Siswa, SiswaKatering, SiswaJemputan

class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = '__all__'
        widgets = {
            'nis': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kelas': forms.TextInput(attrs={'class': 'form-control'}),
            'jenjang': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_lahir': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # ← ini yang penting
            }),
            'nama_wali': forms.TextInput(attrs={'class': 'form-control'}),
            'kontak_wali': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SiswaKateringForm(forms.ModelForm):
    class Meta:
        model = SiswaKatering
        fields = ['siswa', 'katering']
        widgets = {
            'siswa': forms.Select(attrs={'class': 'form-control'}),
            'katering': forms.Select(attrs={'class': 'form-control'}),
        }


class SiswaJemputanForm(forms.ModelForm):
    class Meta:
        model = SiswaJemputan
        fields = ['siswa', 'jemputan']
        widgets = {
            'siswa': forms.Select(attrs={'class': 'form-control'}),
            'jemputan': forms.Select(attrs={'class': 'form-control'}),
        }