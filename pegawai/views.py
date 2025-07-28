from django.shortcuts import render, get_object_or_404, redirect
from .models import Pegawai, AbsenPegawai
from django.utils import timezone
from .forms import PegawaiForm
from datetime import date

from django.db import IntegrityError
def daftar_pegawai(request):
    pegawai_list = Pegawai.objects.all()
    return render(request, 'pegawai/daftar_pegawai.html', {'pegawai_list': pegawai_list})

def tambah_pegawai(request):
    form = PegawaiForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_pegawai')
    return render(request, 'pegawai/form_pegawai.html', {'form': form})

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