# siswa/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_siswa, name='daftar_siswa'),
    path('tambah/', views.tambah_siswa, name='tambah_siswa'),
    path('edit/<int:pk>/', views.edit_siswa, name='edit_siswa'),
    path('hapus/<int:pk>/', views.hapus_siswa, name='hapus_siswa'),
    
    path('siswa-katering/', views.daftar_siswa_katering, name='daftar_siswa_katering'),
    path('siswa-katering/tambah/', views.tambah_siswa_katering, name='tambah_siswa_katering'),
    path('siswa-katering/edit/<int:pk>/', views.edit_siswa_katering, name='edit_siswa_katering'),
    path('siswa-katering/hapus/<int:pk>/', views.hapus_siswa_katering, name='hapus_siswa_katering'),

    path('siswa-jemputan/', views.daftar_siswa_jemputan, name='daftar_siswa_jemputan'),
    path('siswa-jemputan/tambah/', views.tambah_siswa_jemputan, name='tambah_siswa_jemputan'),
    path('siswa-jemputan/edit/<int:pk>/', views.edit_siswa_jemputan, name='edit_siswa_jemputan'),
    path('siswa-jemputan/hapus/<int:pk>/', views.hapus_siswa_jemputan, name='hapus_siswa_jemputan'),
    # Jenjang
    path('jenjang/', views.daftar_jenjang, name='daftar_jenjang'),
    path('jenjang/tambah/', views.tambah_jenjang, name='tambah_jenjang'),
    path('jenjang/edit/<int:pk>/', views.edit_jenjang, name='edit_jenjang'),
    path('jenjang/hapus/<int:pk>/', views.hapus_jenjang, name='hapus_jenjang'),

    # Kelompok
    path('kelompok/', views.daftar_kelompok, name='daftar_kelompok'),
    path('kelompok/tambah/', views.tambah_kelompok, name='tambah_kelompok'),
    path('kelompok/edit/<int:pk>/', views.edit_kelompok, name='edit_kelompok'),
    path('kelompok/hapus/<int:pk>/', views.hapus_kelompok, name='hapus_kelompok'),
    # periode
    path('periode/', views.daftar_periode, name='daftar_periode'),
    path('periode/tambah/', views.tambah_periode, name='tambah_periode'),
    path('periode/edit/<int:pk>/', views.edit_periode, name='edit_periode'),
    path('periode/hapus/<int:pk>/', views.hapus_periode, name='hapus_periode'),
    # kehadiran    
    path('kehadiran_tambah/', views.tambah_kehadiran_siswa, name='tambah_kehadiran_siswa'),
    path('kehadiran/simpan/', views.simpan_kehadiran, name='simpan_kehadiran'),
    path('kehadiran_list/', views.tampilkan_kehadiran, name='kehadiran_list'),
    # rekapitulsai
    path('rekapitulasi_siswa/', views.rekapitulasi_siswa, name='rekapitulasi_siswa'),
]
