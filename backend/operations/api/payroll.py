"""API domain kepegawaian-keuangan (kasbon & payroll)."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsFinanceWriteFinancePrincipalRead

from operations.models import GajiPegawai, PinjamanPegawai
from operations.serializers import GajiPegawaiSerializer, PinjamanPegawaiSerializer
from operations.services import post_gaji, post_pencairan_kasbon
from operations.services.payroll import apply_potongan_pinjaman


# Data sumber yang sudah dijurnal dikoreksi lewat jurnal pembalik, bukan diedit.
class _TerkunciSetelahJurnal:
    pesan_terkunci = ""

    def _tolak_bila_dijurnal(self, instance):
        if instance.jurnal_id:
            raise ValidationError(self.pesan_terkunci)

    def perform_update(self, serializer):
        self._tolak_bila_dijurnal(serializer.instance)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self._tolak_bila_dijurnal(instance)
        super().perform_destroy(instance)


class PinjamanPegawaiViewSet(_TerkunciSetelahJurnal, viewsets.ModelViewSet):
    pesan_terkunci = "Kasbon yang sudah dicairkan tidak dapat diubah atau dihapus."
    queryset = PinjamanPegawai.objects.select_related("pegawai", "jurnal").prefetch_related("jurnal__reversals").order_by("-tanggal_pinjaman")
    serializer_class = PinjamanPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

    @action(detail=True, methods=["post"])
    def cairkan(self, request, pk=None):
        """Pencairan kasbon -> auto-journal (Dr Piutang, Cr Kas)."""
        try:
            jurnal = post_pencairan_kasbon(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Kasbon berhasil dicairkan dan dijurnal sebagai DRAFT.",
            "jurnal_id": str(jurnal.id),
        })


class GajiPegawaiViewSet(_TerkunciSetelahJurnal, viewsets.ModelViewSet):
    pesan_terkunci = "Slip gaji yang sudah diposting tidak dapat diubah atau dihapus."
    queryset = GajiPegawai.objects.select_related("pegawai").order_by("-periode_tahun", "-periode_bulan")
    serializer_class = GajiPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

    def perform_create(self, serializer):
        gaji = serializer.save()
        apply_potongan_pinjaman(gaji, save=True)

    def perform_update(self, serializer):
        self._tolak_bila_dijurnal(serializer.instance)
        gaji = serializer.save()
        apply_potongan_pinjaman(gaji, save=True)

    @action(detail=True, methods=["post"])
    def posting(self, request, pk=None):
        """Posting payroll -> auto-journal beban gaji."""
        try:
            jurnal = post_gaji(self.get_object(), user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({
            "detail": "Gaji berhasil dijurnal sebagai DRAFT — menunggu approval.",
            "jurnal_id": str(jurnal.id),
        })
