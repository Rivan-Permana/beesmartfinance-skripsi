"""API domain kepegawaian-keuangan (kasbon & payroll)."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsFinanceWriteFinancePrincipalRead

from operations.models import GajiPegawai, PinjamanPegawai
from operations.serializers import GajiPegawaiSerializer, PinjamanPegawaiSerializer
from operations.services import post_gaji, post_pencairan_kasbon


class PinjamanPegawaiViewSet(viewsets.ModelViewSet):
    queryset = PinjamanPegawai.objects.select_related("pegawai").order_by("-tanggal_pinjaman")
    serializer_class = PinjamanPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

    @action(detail=True, methods=["post"])
    def cairkan(self, request, pk=None):
        """Pencairan kasbon -> auto-journal (Dr Piutang, Cr Kas)."""
        try:
            jurnal = post_pencairan_kasbon(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})


class GajiPegawaiViewSet(viewsets.ModelViewSet):
    queryset = GajiPegawai.objects.select_related("pegawai").order_by("-periode_tahun", "-periode_bulan")
    serializer_class = GajiPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

    @action(detail=True, methods=["post"])
    def posting(self, request, pk=None):
        """Posting payroll -> auto-journal beban gaji."""
        try:
            jurnal = post_gaji(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})
