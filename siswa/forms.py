from django import forms
from .models import Siswa, SiswaKatering, SiswaJemputan, Jenjang, Kelompok, Periode, Kehadiran

class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = '__all__'
        widgets = {
            'nis': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kelompok': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_lahir': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nama_ayah': forms.TextInput(attrs={'class': 'form-control'}),
            'kontak_ayah': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_ibu': forms.TextInput(attrs={'class': 'form-control'}),
            'kontak_ibu': forms.TextInput(attrs={'class': 'form-control'}),
            'spp': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'periode': forms.Select(attrs={'class': 'form-control'}),  # <-- diperbaiki di sini
            
            'katering': forms.Select(attrs={'class': 'form-control'}),
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

class JenjangForm(forms.ModelForm):
    class Meta:
        model = Jenjang
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
        }

class KelompokForm(forms.ModelForm):
    class Meta:
        model = Kelompok
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'jenjang': forms.Select(attrs={'class': 'form-control'}),
        }


class PeriodeForm(forms.ModelForm):
    class Meta:
        model = Periode
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
        }

class KehadiranForm(forms.ModelForm):
    class Meta:
        model = Kehadiran
        fields = ['siswa', 'tanggal', 'kehadiran', 'katering', 'jemput_datang', 'jemput_pulang']