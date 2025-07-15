from django.shortcuts import render, get_object_or_404, redirect
from .models import Keuangan
from .forms import KeuanganForm

def daftar_keuangan(request):
    keuangan_list = Keuangan.objects.all().order_by('-tanggal')
    return render(request, 'keuangan/daftar_keuangan.html', {'keuangan_list': keuangan_list})

def tambah_keuangan(request):
    form = KeuanganForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_keuangan')
    return render(request, 'keuangan/form_keuangan.html', {'form': form})

def edit_keuangan(request, pk):
    keuangan = get_object_or_404(Keuangan, pk=pk)
    form = KeuanganForm(request.POST or None, instance=keuangan)
    if form.is_valid():
        form.save()
        return redirect('daftar_keuangan')
    return render(request, 'keuangan/form_keuangan.html', {'form': form})

def hapus_keuangan(request, pk):
    keuangan = get_object_or_404(Keuangan, pk=pk)
    keuangan.delete()
    return redirect('daftar_keuangan')
