from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_jemputan, name='daftar_jemputan'),
    path('tambah/', views.tambah_jemputan, name='tambah_jemputan'),
    path('edit/<int:pk>/', views.edit_jemputan, name='edit_jemputan'),
    path('hapus/<int:pk>/', views.hapus_jemputan, name='hapus_jemputan'),
]
