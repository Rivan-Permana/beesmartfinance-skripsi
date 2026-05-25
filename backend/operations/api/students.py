"""API domain siswa."""

from rest_framework import viewsets

from accounts.permissions import IsAdministration

from operations.models import Jenjang, KehadiranSiswa, Kelompok, Siswa
from operations.serializers import (
    JenjangSerializer,
    KehadiranSiswaSerializer,
    KelompokSerializer,
    SiswaSerializer,
)


class JenjangViewSet(viewsets.ModelViewSet):
    queryset = Jenjang.objects.all().order_by("kode")
    serializer_class = JenjangSerializer
    permission_classes = [IsAdministration]


class KelompokViewSet(viewsets.ModelViewSet):
    queryset = Kelompok.objects.select_related("jenjang").order_by("nama")
    serializer_class = KelompokSerializer
    permission_classes = [IsAdministration]


class SiswaViewSet(viewsets.ModelViewSet):
    queryset = Siswa.objects.all().order_by("nama")
    serializer_class = SiswaSerializer
    permission_classes = [IsAdministration]
    filterset_fields = ["status", "kelompok"]
    search_fields = ["nis", "nama"]


class KehadiranSiswaViewSet(viewsets.ModelViewSet):
    queryset = KehadiranSiswa.objects.select_related("siswa").order_by("-tanggal")
    serializer_class = KehadiranSiswaSerializer
    permission_classes = [IsAdministration]
