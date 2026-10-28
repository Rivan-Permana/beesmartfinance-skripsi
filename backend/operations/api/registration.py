"""API domain registrasi calon siswa (sit-in -> admission)."""

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import ADMINISTRATION, FINANCE, role_permission

from operations.models import PendaftaranSiswa
from operations.serializers import PendaftaranSiswaSerializer, BayarPendaftaranInputSerializer, BayarPendaftaranResponseSerializer, FinalisasiPendaftaranInputSerializer
from operations.services import finalisasi_pendaftaran, post_pembayaran_pendaftaran


class PendaftaranSiswaViewSet(viewsets.ModelViewSet):
    queryset = PendaftaranSiswa.objects.select_related("siswa", "jenjang", "jurnal_sitin", "jurnal_pendaftaran").prefetch_related(
        "jurnal_sitin__detail", "jurnal_pendaftaran__detail", "jurnal_sitin__reversals", "jurnal_pendaftaran__reversals",
    ).order_by("-tanggal_daftar", "pk")
    serializer_class = PendaftaranSiswaSerializer
    # Staf TU kelola; Keuangan hanya lihat.
    permission_classes = [role_permission(read=(ADMINISTRATION, FINANCE), write=(ADMINISTRATION,))]
    filterset_fields = ["status"]

    @extend_schema(request=BayarPendaftaranInputSerializer, responses=BayarPendaftaranResponseSerializer)
    @action(detail=True, methods=["post"])
    def bayar(self, request, pk=None):
        payload = BayarPendaftaranInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            jurnal = post_pembayaran_pendaftaran(self.get_object(), user=request.user, **payload.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})
        return Response({
            "detail": "Penerimaan tersimpan. Finance dapat mencatat jurnal ke buku besar.",
            "jurnal_id": str(jurnal.id),
            "pendaftaran": self.get_serializer(self.get_object()).data,
        })

    @extend_schema(request=BayarPendaftaranInputSerializer, responses=BayarPendaftaranResponseSerializer)
    @action(detail=True, methods=["post"], url_path="bayar-sitin")
    def bayar_sitin(self, request, pk=None):
        if request.data.get("komponen") != ["SITIN"]:
            raise ValidationError("Gunakan komponen SITIN beserta rincian penerimaan yang lengkap.")
        return self.bayar(request, pk)

    @extend_schema(request=FinalisasiPendaftaranInputSerializer)
    @action(detail=True, methods=["post"])
    def finalisasi(self, request, pk=None):
        """Finalisasi administrasi tanpa menciptakan penerimaan uang."""
        payload = FinalisasiPendaftaranInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            p = finalisasi_pendaftaran(
                self.get_object(), user=request.user,
                spp_nominal=payload.validated_data["spp_nominal"],
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(self.get_serializer(p).data)

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance = PendaftaranSiswa.objects.select_for_update().get(pk=instance.pk)
            if instance.status != "TRIAL" or instance.siswa_id or instance.jurnal_sitin_id or instance.jurnal_pendaftaran_id:
                raise ValidationError("Pendaftaran dengan siswa atau riwayat penerimaan tidak dapat dihapus.")
            instance.delete()
