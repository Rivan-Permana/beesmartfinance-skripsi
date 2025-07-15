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

]
