from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_keuangan, name='daftar_keuangan'),
    path('tambah/', views.tambah_keuangan, name='tambah_keuangan'),
    path('edit/<int:pk>/', views.edit_keuangan, name='edit_keuangan'),
    path('hapus/<int:pk>/', views.hapus_keuangan, name='hapus_keuangan'),
]
