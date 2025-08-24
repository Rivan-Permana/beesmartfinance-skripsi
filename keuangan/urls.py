from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_keuangan, name='daftar_keuangan'),
    path('tambah/', views.tambah_keuangan, name='tambah_keuangan'),
    path('edit/<int:pk>/', views.edit_keuangan, name='edit_keuangan'),
    path('hapus/<int:pk>/', views.hapus_keuangan, name='hapus_keuangan'),

    # coa

    # route generik (punya name 'coa_list')
    path("coa/<slug:slug>/", views.coa_list, name="coa_list"),
    # List (sesuai menu kamu)
    path("coa/tk/", views.coa_list, {"slug": "tk"}, name="coa_tk"),
    path("coa/playgroup/", views.coa_list, {"slug": "playgroup"}, name="coa_playgroup"),

    # CRUD
    path("coa/<slug:slug>/create/", views.coa_create, name="coa_create"),
    path("coa/<slug:slug>/<int:pk>/edit/", views.coa_update, name="coa_update"),
    path("coa/<slug:slug>/<int:pk>/delete/", views.coa_delete, name="coa_delete"),
]
