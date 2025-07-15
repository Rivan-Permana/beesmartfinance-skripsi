from django import forms
from .models import Pegawai

class PegawaiForm(forms.ModelForm):
    class Meta:
        model = Pegawai
        fields = '__all__'
