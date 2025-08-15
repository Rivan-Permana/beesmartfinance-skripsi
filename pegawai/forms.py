from django import forms
from .models import Pegawai,GajiPegawai, PinjamanPegawai


BULAN_CHOICES_ID = [
    (1, "Januari"), (2, "Februari"), (3, "Maret"), (4, "April"),
    (5, "Mei"), (6, "Juni"), (7, "Juli"), (8, "Agustus"),
    (9, "September"), (10, "Oktober"), (11, "November"), (12, "Desember"),
]

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

class GajiPegawaiForm(forms.ModelForm):
    # ganti field periode_bulan di form agar tampil nama bulan
    periode_bulan = forms.TypedChoiceField(
        choices=BULAN_CHOICES_ID,
        coerce=int,  # pastikan disimpan sebagai int
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = GajiPegawai
        fields = [
            'pegawai', 'periode_bulan', 'periode_tahun',
            'gaji_pokok', 'tunjangan_pengabdian', 'tunjangan_jabatan', 'thr',
        ]
        widgets = {
            'pegawai': forms.Select(attrs={'class': 'form-control'}),
            'periode_tahun': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000}),
            'gaji_pokok': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'tunjangan_pengabdian': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'tunjangan_jabatan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'thr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
        }


class PinjamanPegawaiForm(forms.ModelForm):
    class Meta:
        model = PinjamanPegawai
        fields = [
            'pegawai', 'tanggal_pinjaman', 'tenor_cicilan',
            'jumlah_pinjaman', 'angsuran_per_bulan',
            'sudah_terbayar', 'tanggal_pelunasan'
        ]
        widgets = {
            'pegawai': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_pinjaman': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tenor_cicilan': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'jumlah_pinjaman': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'angsuran_per_bulan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'sudah_terbayar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'tanggal_pelunasan': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }