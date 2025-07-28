# siswa/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Siswa, SiswaKatering, SiswaJemputan, Periode , Kehadiran
from .forms import SiswaForm, SiswaKateringForm, SiswaJemputanForm, PeriodeForm
from django.contrib import messages
from .models import Jenjang, Kelompok
from django.forms import modelform_factory
from django import forms
from datetime import date
from django.utils import timezone
from datetime import datetime
from django.db.models import Count

JenjangForm = modelform_factory(Jenjang, fields='__all__', widgets={'nama': forms.TextInput(attrs={'class': 'form-control'})})
KelompokForm = modelform_factory(Kelompok, fields='__all__', widgets={
    'jenjang': forms.Select(attrs={'class': 'form-control'}),
    'nama': forms.TextInput(attrs={'class': 'form-control'}),
})


# Menampilkan daftar semua siswa
def daftar_siswa(request):
    siswa_list = Siswa.objects.all()
    return render(request, 'siswa/daftar.html', {'siswa_list': siswa_list})

# Tambah siswa (digunakan untuk master dan katering)
def tambah_siswa(request, redirect_name='daftar_siswa'):
    form = SiswaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Data siswa berhasil ditambahkan.')
        return redirect(redirect_name)
    return render(request, 'siswa/form.html', {'form': form})

# Edit siswa
def edit_siswa(request, pk, redirect_name='daftar_siswa'):
    siswa = get_object_or_404(Siswa, pk=pk)
    form = SiswaForm(request.POST or None, instance=siswa)
    if form.is_valid():
        form.save()
        messages.success(request, 'Data siswa berhasil diperbarui.')
        return redirect(redirect_name)
    return render(request, 'siswa/form.html', {'form': form})

# Hapus siswa
def hapus_siswa(request, pk, redirect_name='daftar_siswa'):
    siswa = get_object_or_404(Siswa, pk=pk)
    siswa.delete()
    messages.success(request, 'Data siswa berhasil dihapus.')
    return redirect(redirect_name)


def daftar_siswa_katering(request):
    siswa_katering_list = SiswaKatering.objects.select_related('siswa', 'katering')
    return render(request, 'siswa/daftar_siswa_katering.html', {'siswa_list': siswa_katering_list})

def tambah_siswa_katering(request):
    form = SiswaKateringForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Siswa katering berhasil ditambahkan.')
        return redirect('daftar_siswa_katering')
    return render(request, 'siswa/form_siswa_katering.html', {'form': form})

def edit_siswa_katering(request, pk):
    instance = get_object_or_404(SiswaKatering, pk=pk)
    form = SiswaKateringForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, 'Data siswa katering berhasil diperbarui.')
        return redirect('daftar_siswa_katering')
    return render(request, 'siswa/form_siswa_katering.html', {'form': form})

def hapus_siswa_katering(request, pk):
    instance = get_object_or_404(SiswaKatering, pk=pk)
    instance.delete()
    messages.success(request, 'Data siswa katering berhasil dihapus.')
    return redirect('daftar_siswa_katering')

def daftar_siswa_jemputan(request):
    siswa_list = SiswaJemputan.objects.select_related('siswa', 'jemputan')
    return render(request, 'siswa/daftar_siswa_jemputan.html', {'siswa_list': siswa_list})

def tambah_siswa_jemputan(request):
    form = SiswaJemputanForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Data siswa jemputan berhasil ditambahkan.")
        return redirect('daftar_siswa_jemputan')  # GANTI INI SESUAI NAME YANG BENAR
    return render(request, 'siswa/form_siswa_jemputan.html', {'form': form})

def edit_siswa_jemputan(request, pk):
    instance = get_object_or_404(SiswaJemputan, pk=pk)
    form = SiswaJemputanForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, "Data siswa jemputan berhasil diperbarui.")
        return redirect('daftar_siswa_jemputan')
    return render(request, 'siswa/form_siswa_jemputan.html', {'form': form})

def hapus_siswa_jemputan(request, pk):
    instance = get_object_or_404(SiswaJemputan, pk=pk)
    instance.delete()
    messages.success(request, "Data siswa jemputan berhasil dihapus.")
    return redirect('daftar_siswa_jemputan')

# Jenjang views
def daftar_jenjang(request):
    data = Jenjang.objects.all()
    return render(request, 'siswa/daftar_jenjang.html', {'data': data})

def tambah_jenjang(request):
    form = JenjangForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_jenjang')
    return render(request, 'siswa/form_jenjang.html', {'form': form})

def edit_jenjang(request, pk):
    obj = get_object_or_404(Jenjang, pk=pk)
    form = JenjangForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('daftar_jenjang')
    return render(request, 'siswa/form_jenjang.html', {'form': form})

def hapus_jenjang(request, pk):
    obj = get_object_or_404(Jenjang, pk=pk)
    obj.delete()
    return redirect('daftar_jenjang')

# Kelompok views
def daftar_kelompok(request):
    data = Kelompok.objects.select_related('jenjang').all()
    return render(request, 'siswa/daftar_kelompok.html', {'data': data})

def tambah_kelompok(request):
    form = KelompokForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_kelompok')
    return render(request, 'siswa/form_kelompok.html', {'form': form})

def edit_kelompok(request, pk):
    obj = get_object_or_404(Kelompok, pk=pk)
    form = KelompokForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('daftar_kelompok')
    return render(request, 'siswa/form_kelompok.html', {'form': form})

def hapus_kelompok(request, pk):
    obj = get_object_or_404(Kelompok, pk=pk)
    obj.delete()
    return redirect('daftar_kelompok')

# periode

def daftar_periode(request):
    periode_list = Periode.objects.all()
    return render(request, 'siswa/daftar_periode.html', {
        'periode_list': periode_list
    })

def tambah_periode(request):
    form = PeriodeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_periode')
    return render(request, 'siswa/form_periode.html', {'form': form})

def edit_periode(request, pk):
    periode = get_object_or_404(Periode, pk=pk)
    form = PeriodeForm(request.POST or None, instance=periode)
    if form.is_valid():
        form.save()
        return redirect('daftar_periode')
    return render(request, 'siswa/form_periode.html', {'form': form})

def hapus_periode(request, pk):
    periode = get_object_or_404(Periode, pk=pk)
    periode.delete()
    return redirect('daftar_periode')

def tambah_kehadiran_siswa(request):
    tanggal = request.GET.get('tanggal')
    kelompok = request.GET.get('kelompok')
    periode = request.GET.get('periode')

    if not tanggal or not kelompok or not periode:
        messages.error(request, "Parameter tidak lengkap.")
        return redirect('kehadiran_list')

    try:
        tanggal_obj = timezone.datetime.strptime(tanggal, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('kehadiran_list')

    siswa_list = Siswa.objects.select_related('kelompok__jenjang') \
                              .filter(status='aktif', kelompok_id=kelompok) \
                              .order_by('kelompok__jenjang__nama', 'kelompok__nama', 'nama')

    kehadiran_qs = Kehadiran.objects.filter(tanggal=tanggal_obj)
    kehadiran_dict = {k.siswa_id: k for k in kehadiran_qs}

    for siswa in siswa_list:
        siswa.kehadiran_data = kehadiran_dict.get(siswa.id)

    context = {
        'siswa_list': siswa_list,
        'tanggal': tanggal_obj,
        'kelompok_id': kelompok,
        'periode_id': periode,
    }
    return render(request, 'siswa/form_kehadiran_siswa.html', context)

def simpan_kehadiran(request):
    if request.method == 'POST':
        tanggal = request.POST.get('tanggal')
        kelompok = request.POST.get('kelompok')
        periode = request.POST.get('periode')

        if not tanggal or not kelompok or not periode:
            messages.error(request, "Data tidak lengkap untuk menyimpan kehadiran.")
            return redirect('kehadiran_list')

        try:
            tanggal_obj = timezone.datetime.strptime(tanggal, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Format tanggal tidak valid.")
            return redirect('kehadiran_list')

        siswa_list = Siswa.objects.filter(status='aktif', kelompok_id=kelompok)

        for siswa in siswa_list:
            kehadiran = request.POST.get(f'kehadiran_{siswa.id}')
            katering_ikut = request.POST.get(f'katering_{siswa.id}')
            katering_tidak = request.POST.get(f'katering_{siswa.id}_tidak')
            jemput_datang = request.POST.get(f'jemput_datang_{siswa.id}') == 'ya'
            jemput_pulang = request.POST.get(f'jemput_pulang_{siswa.id}') == 'ya'

            katering_status = ''
            if katering_ikut:
                katering_status = 'ikut'
            elif katering_tidak:
                katering_status = 'tidak_ikut'

            if kehadiran:
                Kehadiran.objects.update_or_create(
                    siswa=siswa,
                    tanggal=tanggal_obj,
                    defaults={
                        'kehadiran': kehadiran,
                        'katering': katering_status,
                        'jemput_datang': jemput_datang,
                        'jemput_pulang': jemput_pulang,
                    }
                )

        messages.success(request, "Data kehadiran berhasil disimpan.")
        return redirect(f'/siswa/kehadiran_list/?tanggal={tanggal}&kelompok={kelompok}&periode={periode}')

    return redirect('kehadiran_list')


def tampilkan_kehadiran(request):
    tanggal_str = request.GET.get('tanggal')
    
    kelompok_id = request.GET.get('kelompok')
    periode_id = request.GET.get('periode')
    jenjang = ""

    # Konversi ke integer (jika ada)
    try:
        kelompok_id = int(kelompok_id) if kelompok_id else None
    except ValueError:
        kelompok_id = None

    try:
        periode_id = int(periode_id) if periode_id else None
    except ValueError:
        periode_id = None

    print(tanggal_str,kelompok_id,periode_id)

    if tanggal_str:
        tanggal_obj = timezone.datetime.strptime(tanggal_str, "%Y-%m-%d").date()
    else:
        tanggal_obj = timezone.now().date()

    # Konversi ke int jika ada nilai
    kelompok_id_int = int(kelompok_id) if kelompok_id else None
    periode_id_int = int(periode_id) if periode_id else None

    # Ambil semua siswa aktif
    semua_siswa = Siswa.objects.select_related('kelompok__jenjang').filter(status='aktif')

    # Filter kehadiran jika kelompok dan periode dipilih
    if kelompok_id_int and periode_id_int:
        kehadiran_qs = Kehadiran.objects.select_related('siswa').filter(
            tanggal=tanggal_obj,
            siswa__kelompok_id=kelompok_id_int,
            siswa__periode_id=periode_id_int
        )
        kehadiran_map = {k.siswa: k for k in kehadiran_qs}
        semua_siswa = semua_siswa.filter(kelompok_id=kelompok_id_int, periode_id=periode_id_int)
        jenjang = semua_siswa.first().kelompok.jenjang.nama if semua_siswa.exists() else ""
    else:
        kehadiran_map = {}

    for siswa in semua_siswa:
        siswa.kehadiran_data = kehadiran_map.get(siswa)

    context = {
        'tanggal': tanggal_obj,
        'semua_siswa': semua_siswa,
        'semua_kelompok': Kelompok.objects.all(),
        'semua_periode': Periode.objects.all(),
        'kelompok_id': kelompok_id,
        'periode_id': periode_id,
        'kelompok_id_int': kelompok_id_int,
        'periode_id_int': periode_id_int,
        "jenjang": jenjang,
    }

    return render(request, 'siswa/kehadiran_list.html', context)

def rekapitulasi_siswa(request):
    tanggal_dari = request.GET.get('tanggal_dari')
    tanggal_sampai = request.GET.get('tanggal_sampai')
    kelompok_id = request.GET.get('kelompok')
    periode_id = request.GET.get('periode')
    jenjang =""
    kemlompok = ""

    semua_siswa = Siswa.objects.select_related("kelompok__jenjang").all()
    semua_kelompok = Kelompok.objects.all()
    semua_periode = Periode.objects.all()

    if kelompok_id:
        semua_siswa = semua_siswa.filter(kelompok_id=kelompok_id)
    if periode_id:
        semua_siswa = semua_siswa.filter(periode_id=periode_id)

    filter_tanggal = {}
    if tanggal_dari:
        filter_tanggal['tanggal__gte'] = tanggal_dari
    if tanggal_sampai:
        filter_tanggal['tanggal__lte'] = tanggal_sampai

    kehadiran_qs = Kehadiran.objects.filter(
        siswa__in=semua_siswa,
        **filter_tanggal
    ).select_related("siswa", "siswa__kelompok", "siswa__kelompok__jenjang").order_by("siswa__nama", "tanggal")

    # Rekap per siswa
    rekap_per_siswa = {}
    for kehadiran in kehadiran_qs:
        siswa = kehadiran.siswa
        if siswa.id not in rekap_per_siswa:
            rekap_per_siswa[siswa.id] = {
                "nama": siswa.nama,
                "kelompok": siswa.kelompok.nama if siswa.kelompok else "-",
                "jenjang": siswa.kelompok.jenjang.nama if siswa.kelompok and siswa.kelompok.jenjang else "-",
                "hadir": 0,
                "tidak_hadir": 0,
                "izin": 0,
                "sakit": 0,
                "total": 0,
                "tanggal_dari": tanggal_dari,
                "tanggal_sampai": tanggal_sampai,   
                "kelompok_id": kelompok_id,
                "periode_id": periode_id,
            }
            jenjang = siswa.kelompok.jenjang.nama if siswa.kelompok and siswa.kelompok.jenjang else "-"
            kelompok = siswa.kelompok.nama if siswa.kelompok else "-"


        status = kehadiran.kehadiran.lower()
        if status in rekap_per_siswa[siswa.id]:
            rekap_per_siswa[siswa.id][status] += 1
        rekap_per_siswa[siswa.id]["total"] += 1

    context = {
        "semua_siswa": semua_siswa,
        "semua_kelompok": semua_kelompok,
        "semua_periode": semua_periode,
        "kelompok_id": int(kelompok_id) if kelompok_id else "",
        "periode_id": int(periode_id) if periode_id else "",
        "tanggal_dari": tanggal_dari,
        "tanggal_sampai": tanggal_sampai,
        "rekap_list": rekap_per_siswa.values(),
        "jenjang": jenjang,
        "kelompok": kelompok,
    }
    return render(request, "siswa/rekapitulasi_siswa.html", context)

