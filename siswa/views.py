# siswa/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Siswa, SiswaKatering, SiswaJemputan
from .forms import SiswaForm, SiswaKateringForm, SiswaJemputanForm
from django.contrib import messages

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