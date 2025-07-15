from django.shortcuts import render, get_object_or_404, redirect
from .models import Pegawai
from .forms import PegawaiForm

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
