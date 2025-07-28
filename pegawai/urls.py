from django.urls import path
from . import views
urlpatterns = [
    path('', views.daftar_pegawai, name='daftar_pegawai'),
    path('tambah/', views.tambah_pegawai, name='tambah_pegawai'),
    path('edit/<int:pk>/', views.edit_pegawai, name='edit_pegawai'),
    path('hapus/<int:pk>/', views.hapus_pegawai, name='hapus_pegawai'),

    path('absen_pegawai_tambah/', views.absen_pegawai_tambah, name='absen_pegawai_tambah'),
    path('absen_pegawai/', views.absen_pegawai, name='absen_pegawai'),
]
