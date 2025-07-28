from django import forms
from .models import Pegawai

class PegawaiForm(forms.ModelForm):
    class Meta:
        model = Pegawai
        fields = '__all__'
        widgets = {
            'nik': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'nip': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'nama': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'jabatan': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'work_periode_bulan': forms.NumberInput(attrs={'class': 'form-control w-100'}),
            'work_periode_tahun': forms.NumberInput(attrs={'class': 'form-control w-100'}),
            'nomor_hp': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control w-100', 'rows': 2}),
            'uang_transport': forms.NumberInput(attrs={'class': 'form-control w-100'}),
            'status': forms.Select(attrs={'class': 'form-control w-100'}),
        }
