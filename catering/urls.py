from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_katering, name='daftar_katering'),
    path('tambah/', views.tambah_katering, name='tambah_katering'),
    path('edit/<int:pk>/', views.edit_katering, name='edit_katering'),
    path('hapus/<int:pk>/', views.hapus_katering, name='hapus_katering'),
]
