from django.urls import path
from . import views

urlpatterns = [

    path("katering/daftar/", views.daftar_siswa_katering, name="katering_daftar"),
]
