from django.shortcuts import render, redirect, get_object_or_404
from .models import Katering
from .forms import KateringForm

def daftar_katering(request):
    katering_list = Katering.objects.all().order_by('-tanggal')
    return render(request, 'katering/daftar_katering.html', {'katering_list': katering_list})

def tambah_katering(request):
    form = KateringForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_katering')
    return render(request, 'katering/form_katering.html', {'form': form})

def edit_katering(request, pk):
    katering = get_object_or_404(Katering, pk=pk)
    form = KateringForm(request.POST or None, instance=katering)
    if form.is_valid():
        form.save()
        return redirect('daftar_katering')
    return render(request, 'katering/form_katering.html', {'form': form})

def hapus_katering(request, pk):
    katering = get_object_or_404(Katering, pk=pk)
    katering.delete()
    return redirect('daftar_katering')
