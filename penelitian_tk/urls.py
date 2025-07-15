from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin_doanks/', admin.site.urls),
    path('', include('core.urls')), 
    path('catering/', include('catering.urls')), 
    path('jemputan/', include('jemputan.urls')), 
    path('keuangan/', include('keuangan.urls')), 
    path('pegawai/', include('pegawai.urls')), 
    path('siswa/', include('siswa.urls')), 
]
