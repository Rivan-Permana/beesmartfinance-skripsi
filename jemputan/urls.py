# jemputan/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Sub Menu 1: Data Kendaraan
    path("kendaraan/", views.kendaraan_list, name="kendaraan_list"),
    path("kendaraan/tambah/", views.kendaraan_create, name="kendaraan_create"),
    path("kendaraan/<int:pk>/edit/", views.kendaraan_update, name="kendaraan_update"),
    path("kendaraan/<int:pk>/hapus/", views.kendaraan_delete, name="kendaraan_delete"),

    # Rekapitulasi Jemputan Siswa
    path("rekap/", views.rekap_jemputan, name="rekap_jemputan"),
    path("rekap/bulanan/", views.rekap_jemputan_bulanan, name="rekap_jemputan_bulanan"),
]
