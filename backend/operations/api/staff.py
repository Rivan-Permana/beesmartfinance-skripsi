"""API domain kepegawaian (master & absensi)."""

from rest_framework import viewsets

from accounts.permissions import IsAdministration, IsFinanceOrReadOnly

from operations.models import AbsenPegawai, Pegawai
from operations.serializers import AbsenPegawaiSerializer, PegawaiSerializer


class PegawaiViewSet(viewsets.ModelViewSet):
    queryset = Pegawai.objects.all().order_by("nama")
    serializer_class = PegawaiSerializer
    permission_classes = [IsFinanceOrReadOnly]


class AbsenPegawaiViewSet(viewsets.ModelViewSet):
    queryset = AbsenPegawai.objects.select_related("pegawai").order_by("-tanggal")
    serializer_class = AbsenPegawaiSerializer
    permission_classes = [IsAdministration]
