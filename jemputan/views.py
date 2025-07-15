from django.shortcuts import render, get_object_or_404, redirect
from .models import Jemputan
from .forms import JemputanForm

def daftar_jemputan(request):
    jemputan_list = Jemputan.objects.all()
    return render(request, 'jemputan/daftar.html', {'jemputan_list': jemputan_list})

def tambah_jemputan(request):
    form = JemputanForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_jemputan')
    return render(request, 'jemputan/form.html', {'form': form})

def edit_jemputan(request, pk):
    jemputan = get_object_or_404(Jemputan, pk=pk)
    form = JemputanForm(request.POST or None, instance=jemputan)
    if form.is_valid():
        form.save()
        return redirect('daftar_jemputan')
    return render(request, 'jemputan/form.html', {'form': form})

def hapus_jemputan(request, pk):
    jemputan = get_object_or_404(Jemputan, pk=pk)
    jemputan.delete()
    return redirect('daftar_jemputan')
