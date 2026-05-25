"""API domain registrasi calon siswa (sit-in -> admission)."""

from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministration

from operations.models import PendaftaranSiswa
from operations.serializers import PendaftaranSiswaSerializer
from operations.services import finalisasi_pendaftaran, post_bayar_sitin


class PendaftaranSiswaViewSet(viewsets.ModelViewSet):
    queryset = PendaftaranSiswa.objects.select_related("siswa", "jenjang").order_by("-tanggal_daftar")
    serializer_class = PendaftaranSiswaSerializer
    permission_classes = [IsAdministration]
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"], url_path="bayar-sitin")
    def bayar_sitin(self, request, pk=None):
        """Pembayaran sit-in/trial -> auto-journal pendapatan."""
        try:
            jurnal = post_bayar_sitin(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})

    @action(detail=True, methods=["post"])
    def finalisasi(self, request, pk=None):
        """Calon mendaftar resmi -> jurnal admission + buat Siswa."""
        try:
            p = finalisasi_pendaftaran(
                self.get_object(), user=request.user,
                spp_nominal=Decimal(str(request.data.get("spp_nominal", 0))),
            )
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(p).data)
