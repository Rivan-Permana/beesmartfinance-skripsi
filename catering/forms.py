# keuangan/forms.py
from django import forms
from siswa.models import Kelompok, Periode
import datetime

class KateringFilterForm(forms.Form):
    bulan = forms.CharField(  # "2025-08" dari <input type="month">
        required=False,
        widget=forms.TextInput(attrs={"type": "month", "class": "form-control"})
    )
    kelompok = forms.ModelChoiceField(
        queryset=Kelompok.objects.select_related("jenjang").all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    periode = forms.ModelChoiceField(
        queryset=Periode.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    def clean(self):
        cleaned = super().clean()
        # default: bulan berjalan (first day)
        today = datetime.date.today()
        first_day = today.replace(day=1)

        raw = (cleaned.get("bulan") or "").strip()
        if raw:
            # expect "YYYY-MM"
            try:
                year, month = raw.split("-")
                first_day = datetime.date(int(year), int(month), 1)
            except Exception:
                self.add_error("bulan", "Format bulan tidak valid. Gunakan YYYY-MM.")
        cleaned["bulan"] = first_day  # simpan sebagai date (tgl 1)
        return cleaned
