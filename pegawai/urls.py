from django.urls import path
from . import views
urlpatterns = [
    path('', views.daftar_pegawai, name='daftar_pegawai'),
    path('tambah/', views.tambah_pegawai, name='tambah_pegawai'),
    path('edit/<int:pk>/', views.edit_pegawai, name='edit_pegawai'),
    path('hapus/<int:pk>/', views.hapus_pegawai, name='hapus_pegawai'),

    path('absen_pegawai_tambah/', views.absen_pegawai_tambah, name='absen_pegawai_tambah'),
    path('absen_pegawai/', views.absen_pegawai, name='absen_pegawai'),

    # Gaji
    path('gaji/', views.gaji_list, name='gaji_list'),
    path('gaji/tambah/', views.gaji_tambah, name='gaji_tambah'),
    path('gaji/<int:pk>/edit/', views.gaji_edit, name='gaji_edit'),
    path('gaji/<int:pk>/hapus/', views.gaji_hapus, name='gaji_hapus'),

    # Pinjaman
    path('pinjaman/', views.pinjaman_list, name='pinjaman_list'),
    path('pinjaman/tambah/', views.pinjaman_tambah, name='pinjaman_tambah'),
    path('pinjaman/<int:pk>/edit/', views.pinjaman_edit, name='pinjaman_edit'),
    path('pinjaman/<int:pk>/hapus/', views.pinjaman_hapus, name='pinjaman_hapus'),
]
