from django import forms
from .models import Keuangan, COA

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


class COAForm(forms.ModelForm):
    class Meta:
        model = COA
        fields = ["nomor_akun", "tipe_akun", "nama_akun", "is_active"]
        widgets = {
            "nomor_akun": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Mis: 1101"
            }),
            "tipe_akun": forms.TextInput(attrs={
                "class": "form-control text-uppercase",  # otomatis uppercase di form
                "style": "text-transform:uppercase",
                "placeholder": "Contoh: ASET LANCAR"
            }),
            "nama_akun": forms.TextInput(attrs={
                "class": "form-control text-uppercase",  # otomatis uppercase di form
                "style": "text-transform:uppercase",
                "placeholder": "Contoh: Kas di Tangan"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }