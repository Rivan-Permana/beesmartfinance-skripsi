from django.shortcuts import render, get_object_or_404, redirect
from .models import Pegawai, AbsenPegawai,GajiPegawai, PinjamanPegawai
from django.utils import timezone
from .forms import PegawaiForm,GajiPegawaiForm, PinjamanPegawaiForm
from datetime import date
from django.contrib import messages
import calendar

from django.db import IntegrityError
def daftar_pegawai(request):
    pegawai_list = Pegawai.objects.all()
    return render(request, 'pegawai/daftar_pegawai.html', {'pegawai_list': pegawai_list})

def tambah_pegawai(request):
    if request.method == "POST":
        form = PegawaiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pegawai berhasil ditambahkan.")
            return redirect("daftar_pegawai")
        messages.error(request, "Periksa kembali isian Anda.")
    else:
        form = PegawaiForm()

    return render(request, "pegawai/form_pegawai.html", {"form": form, "title": "Tambah Pegawai"})

def edit_pegawai(request, pk):
    pegawai = get_object_or_404(Pegawai, pk=pk)
    form = PegawaiForm(request.POST or None, instance=pegawai)
    if form.is_valid():
        form.save()
        return redirect('daftar_pegawai')
    return render(request, 'pegawai/form_pegawai.html', {'form': form})

def hapus_pegawai(request, pk):
    pegawai = get_object_or_404(Pegawai, pk=pk)
    pegawai.delete()
    return redirect('daftar_pegawai')

def absen_pegawai_tambah(request):
    tanggal = request.GET.get('tanggal') or request.POST.get('tanggal')
    if not tanggal:
        tanggal = date.today().isoformat()

    # Ambil semua pegawai aktif
    pegawai_list = Pegawai.objects.filter(status='active')

    # Ambil data kehadiran untuk tanggal tersebut
    absensi_dict = {
        absen.pegawai_id: absen
        for absen in AbsenPegawai.objects.filter(tanggal=tanggal)
    }

    # Tambahkan atribut kehadiran_data ke setiap pegawai
    for pegawai in pegawai_list:
        absen = absensi_dict.get(pegawai.id)
        if absen:
            if absen.hadir:
                pegawai.kehadiran_data = {'kehadiran': 'hadir'}
            elif absen.terlambat:
                pegawai.kehadiran_data = {'kehadiran': 'terlambat'}
            elif absen.tidak_hadir:
                pegawai.kehadiran_data = {'kehadiran': 'tidak_hadir'}
            elif absen.izin:
                pegawai.kehadiran_data = {'kehadiran': 'izin'}
            elif absen.sakit:
                pegawai.kehadiran_data = {'kehadiran': 'sakit'}
        else:
            pegawai.kehadiran_data = None

    # Jika form disubmit
    if request.method == 'POST':
        for pegawai in pegawai_list:
            kehadiran = request.POST.get(f"kehadiran_{pegawai.id}", None)
            if kehadiran:
                try:
                    AbsenPegawai.objects.update_or_create(
                        pegawai=pegawai,
                        tanggal=tanggal,
                        defaults={
                            'hadir': 1 if kehadiran == 'hadir' else 0,
                            'terlambat': 1 if kehadiran == 'terlambat' else 0,
                            'tidak_hadir': 1 if kehadiran == 'tidak_hadir' else 0,
                            'izin': 1 if kehadiran == 'izin' else 0,
                            'sakit': 1 if kehadiran == 'sakit' else 0,
                        }
                    )
                except IntegrityError as e:
                    print(f"Error update {pegawai.nama}: {e}")

        return redirect('absen_pegawai')

    context = {
        'pegawai_list': pegawai_list,
        'tanggal': tanggal,
    }
    return render(request, 'pegawai/form_absen_pegawai.html', context)

def absen_pegawai(request):
    tanggal = request.GET.get('tanggal')
    tgl = tanggal
    if not tanggal:
        tanggal = date.today().isoformat()
    semua_pegawai = Pegawai.objects.filter(status='active')  # jika perlu filter active
    data_absen_dict = { absen.pegawai_id: absen for absen in AbsenPegawai.objects.filter(tanggal=tanggal) }
    
    # print(tanggal,semua_pegawai,data_absen_dict)
    data_absen = []
    for pegawai in semua_pegawai:
        absen = data_absen_dict.get(pegawai.id)
        if absen:
            data_absen.append({
                'pegawai': pegawai,
                'hadir': absen.hadir,
                'tidak_hadir': absen.tidak_hadir,
                'izin': absen.izin,
                'sakit': absen.sakit,
                'terlambat': absen.terlambat,
                'insentif': absen.insentif,
                'total': absen.total
            })
        else:
            data_absen.append({
                'pegawai': pegawai,
                'hadir': 0,
                'tidak_hadir': 0,
                'izin': 0,
                'sakit': 0,
                'terlambat': 0,
                'insentif': 0,
                'total': 0
            })

    context = {
        'data_absen': data_absen,
        'tanggal_filter': tanggal,
        'tgl': tgl,
    }
    print(data_absen)
    return render(request, 'pegawai/absen_pegawai.html', context)

# ===== Gaji =====
def gaji_list(request):
    qs = GajiPegawai.objects.select_related('pegawai').all()

    # ambil dari query, kalau kosong pakai hari ini
    bulan = request.GET.get('bulan')
    tahun = request.GET.get('tahun')

    today = timezone.localdate()  # patuh timezone Django
    if not bulan:
        bulan = str(today.month)   # simpan sebagai string utk binding form
    if not tahun:
        tahun = str(today.year)

    # filter sesuai bulan & tahun terpilih
    qs = qs.filter(periode_bulan=int(bulan), periode_tahun=int(tahun))

    # pilihan bulan (1–12) dengan nama
    bulan_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]

    # kirim juga versi int agar perbandingan di template simpel
    context = {
        "gaji_list": qs,
        "bulan": bulan,                     # "1".."12" (string)
        "bulan_int": int(bulan),            # 1..12 (int) -> jika mau dipakai di template
        "tahun": tahun,
        "bulan_choices": bulan_choices,
    }
    return render(request, "pegawai/gaji_list.html", context)

def gaji_tambah(request):
    if request.method == 'POST':
        form = GajiPegawaiForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()  # trigger auto perhitungan
            messages.success(request, "Gaji berhasil ditambahkan.")
            return redirect('gaji_list')
        messages.error(request, "Periksa kembali isian Anda.")
    else:
        form = GajiPegawaiForm()
    return render(request, 'pegawai/gaji_form.html', {'form': form, 'title': 'Tambah Gaji'})

def gaji_edit(request, pk):
    obj = get_object_or_404(GajiPegawai, pk=pk)
    if request.method == 'POST':
        form = GajiPegawaiForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()  # hitung ulang komponen otomatis
            messages.success(request, "Gaji berhasil diperbarui.")
            return redirect('gaji_list')
        messages.error(request, "Periksa kembali isian Anda.")
    else:
        form = GajiPegawaiForm(instance=obj)
    return render(request, 'pegawai/gaji_form.html', {'form': form, 'title': 'Edit Gaji', 'obj': obj})

def gaji_hapus(request, pk):
    obj = get_object_or_404(GajiPegawai, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Gaji berhasil dihapus.")
        return redirect('gaji_list')
    return render(request, 'pegawai/confirm_delete.html', {'item': obj, 'title': 'Hapus Gaji'})


# ===== Pinjaman =====
def pinjaman_list(request):
    qs = PinjamanPegawai.objects.select_related('pegawai').all()
    return render(request, 'pegawai/pinjaman_list.html', {'pinjaman_list': qs})

def pinjaman_tambah(request):
    if request.method == 'POST':
        form = PinjamanPegawaiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pinjaman berhasil ditambahkan.")
            return redirect('pinjaman_list')
        messages.error(request, "Periksa kembali isian Anda.")
    else:
        form = PinjamanPegawaiForm()
    return render(request, 'pegawai/pinjaman_form.html', {'form': form, 'title': 'Tambah Pinjaman'})

def pinjaman_edit(request, pk):
    obj = get_object_or_404(PinjamanPegawai, pk=pk)
    if request.method == 'POST':
        form = PinjamanPegawaiForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Pinjaman berhasil diperbarui.")
            return redirect('pinjaman_list')
        messages.error(request, "Periksa kembali isian Anda.")
    else:
        form = PinjamanPegawaiForm(instance=obj)
    return render(request, 'pegawai/pinjaman_form.html', {'form': form, 'title': 'Edit Pinjaman'})

def pinjaman_hapus(request, pk):
    obj = get_object_or_404(PinjamanPegawai, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, "Pinjaman berhasil dihapus.")
        return redirect('pinjaman_list')
    return render(request, 'pegawai/confirm_delete.html', {'item': obj, 'title': 'Hapus Pinjaman'})