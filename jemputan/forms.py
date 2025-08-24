# jemputan/forms.py
from django import forms
from .models import Jemputan
from siswa.models import Kelompok, Periode
from django.utils.timezone import now

class KendaraanForm(forms.ModelForm):
    class Meta:
        model = Jemputan
        fields = ["nama_supir", "no_hp", "no_kendaraan", "jenis_mobil", "kapasitas", "pendamping", "keterangan"]
        widgets = {
            "nama_supir": forms.TextInput(attrs={"class": "form-control"}),
            "no_hp": forms.TextInput(attrs={"class": "form-control"}),
            "no_kendaraan": forms.TextInput(attrs={"class": "form-control"}),
            "jenis_mobil": forms.TextInput(attrs={"class": "form-control"}),
            "kapasitas": forms.NumberInput(attrs={"class": "form-control"}),
            "pendamping": forms.TextInput(attrs={"class": "form-control"}),
            "keterangan": forms.TextInput(attrs={"class": "form-control"}),
        }


class RekapJemputanFilterForm(forms.Form):
    tanggal_awal = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    tanggal_akhir = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Nama siswa"}))

    def clean(self):
        cleaned = super().clean()
        today = now().date()
        t1 = cleaned.get("tanggal_awal") or today.replace(day=1)
        t2 = cleaned.get("tanggal_akhir") or today
        if t1 > t2:
            self.add_error("tanggal_akhir", "Tanggal akhir harus >= tanggal awal.")
        cleaned["tanggal_awal"] = t1
        cleaned["tanggal_akhir"] = t2
        return cleaned
    

class RekapJemputanBulananForm(forms.Form):
    # input bulan (YYYY-MM). backend akan hitung first/last day sendiri.
    bulan = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"type": "month", "class": "form-control"})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cari nama siswa"})
    )
    kelompok = forms.ModelChoiceField(
        queryset=Kelompok.objects.select_related("jenjang").order_by("jenjang__kode","nama"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    periode = forms.ModelChoiceField(
        queryset=Periode.objects.order_by("nama"),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    # opsional: helper utk default bulan di template
    def initial_bulan(self):
        try:
            return self.data.get("bulan") or self.initial.get("bulan")
        except Exception:
            return None