"""API domain layanan sekolah (katering & jemputan)."""

from rest_framework import viewsets

from accounts.permissions import IsAdministration

from operations.models import ArmadaJemputan, MenuKatering, PendaftaranJemputan
from operations.serializers import (
    ArmadaJemputanSerializer,
    MenuKateringSerializer,
    PendaftaranJemputanSerializer,
)


class MenuKateringViewSet(viewsets.ModelViewSet):
    queryset = MenuKatering.objects.all().order_by("-tanggal")
    serializer_class = MenuKateringSerializer
    permission_classes = [IsAdministration]


class ArmadaJemputanViewSet(viewsets.ModelViewSet):
    queryset = ArmadaJemputan.objects.all().order_by("nama_supir")
    serializer_class = ArmadaJemputanSerializer
    permission_classes = [IsAdministration]


class PendaftaranJemputanViewSet(viewsets.ModelViewSet):
    queryset = PendaftaranJemputan.objects.select_related("siswa", "armada").order_by("-id")
    serializer_class = PendaftaranJemputanSerializer
    permission_classes = [IsAdministration]
