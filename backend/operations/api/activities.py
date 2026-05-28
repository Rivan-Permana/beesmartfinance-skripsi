"""API domain kegiatan sekolah (Teacher in Charge + Principal)."""

from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsTeacherOrPrincipal

from operations.models import Kegiatan
from operations.serializers import KegiatanSerializer
from operations.services import post_realisasi_kegiatan


class KegiatanViewSet(viewsets.ModelViewSet):
    queryset = Kegiatan.objects.select_related("penanggung_jawab").order_by("-id")
    serializer_class = KegiatanSerializer
    permission_classes = [IsTeacherOrPrincipal]
    filterset_fields = ["status", "penanggung_jawab"]

    @action(detail=True, methods=["post"])
    def realisasi(self, request, pk=None):
        """Catat realisasi/pengeluaran kegiatan -> auto-journal beban (cek pagu)."""
        kegiatan = self.get_object()
        try:
            r = post_realisasi_kegiatan(
                kegiatan,
                tanggal=request.data.get("tanggal") or date.today(),
                deskripsi=request.data.get("deskripsi", ""),
                nominal=request.data["nominal"],
                user=request.user,
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Realisasi kegiatan tercatat dan dijurnal sebagai DRAFT.",
            "realisasi_id": r.id,
            "jurnal_id": str(r.jurnal_id),
        }, status=201)

    @action(detail=True, methods=["get"])
    def laporan(self, request, pk=None):
        """Laporan utilisasi anggaran kegiatan (activity report)."""
        k = self.get_object()
        return Response({
            "kegiatan": k.nama, "pagu": k.pagu, "realisasi": k.realisasi,
            "sisa_pagu": k.sisa_pagu, "rasio_utilisasi": k.rasio_utilisasi,
            "rincian": [
                {"tanggal": x.tanggal, "deskripsi": x.deskripsi, "nominal": x.nominal}
                for x in k.realisasi_list.all()
            ],
        })
