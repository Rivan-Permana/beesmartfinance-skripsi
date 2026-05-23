"""API operasional: master sekolah, layanan, kepegawaian, billing."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministration, IsFinanceOrReadOnly

from .models import (
    AbsenPegawai,
    ArmadaJemputan,
    FixedAsset,
    GajiPegawai,
    Jenjang,
    KehadiranSiswa,
    Kelompok,
    MenuKatering,
    Pegawai,
    PendaftaranJemputan,
    PinjamanPegawai,
    Siswa,
    Tagihan,
)
from .serializers import (
    AbsenPegawaiSerializer,
    ArmadaJemputanSerializer,
    FixedAssetSerializer,
    GajiPegawaiSerializer,
    JenjangSerializer,
    KehadiranSiswaSerializer,
    KelompokSerializer,
    MenuKateringSerializer,
    PegawaiSerializer,
    PendaftaranJemputanSerializer,
    PinjamanPegawaiSerializer,
    SiswaSerializer,
    TagihanSerializer,
)
from .services import (
    post_gaji,
    post_pembayaran_tagihan,
    post_pencairan_kasbon,
    post_penyusutan,
)


# ---- master & operasional sekolah (Administration) ----
class JenjangViewSet(viewsets.ModelViewSet):
    queryset = Jenjang.objects.all()
    serializer_class = JenjangSerializer
    permission_classes = [IsAdministration]


class KelompokViewSet(viewsets.ModelViewSet):
    queryset = Kelompok.objects.select_related("jenjang")
    serializer_class = KelompokSerializer
    permission_classes = [IsAdministration]


class SiswaViewSet(viewsets.ModelViewSet):
    queryset = Siswa.objects.all().order_by("nama")
    serializer_class = SiswaSerializer
    permission_classes = [IsAdministration]


class KehadiranSiswaViewSet(viewsets.ModelViewSet):
    queryset = KehadiranSiswa.objects.select_related("siswa")
    serializer_class = KehadiranSiswaSerializer
    permission_classes = [IsAdministration]


class AbsenPegawaiViewSet(viewsets.ModelViewSet):
    queryset = AbsenPegawai.objects.select_related("pegawai")
    serializer_class = AbsenPegawaiSerializer
    permission_classes = [IsAdministration]


class MenuKateringViewSet(viewsets.ModelViewSet):
    queryset = MenuKatering.objects.all()
    serializer_class = MenuKateringSerializer
    permission_classes = [IsAdministration]


class ArmadaJemputanViewSet(viewsets.ModelViewSet):
    queryset = ArmadaJemputan.objects.all()
    serializer_class = ArmadaJemputanSerializer
    permission_classes = [IsAdministration]


class PendaftaranJemputanViewSet(viewsets.ModelViewSet):
    queryset = PendaftaranJemputan.objects.select_related("siswa", "armada")
    serializer_class = PendaftaranJemputanSerializer
    permission_classes = [IsAdministration]


class TagihanViewSet(viewsets.ModelViewSet):
    serializer_class = TagihanSerializer
    permission_classes = [IsAdministration]

    def get_queryset(self):
        return Tagihan.objects.select_related("siswa").prefetch_related("detail")

    @action(detail=True, methods=["post"])
    def bayar(self, request, pk=None):
        """Catat pembayaran -> auto-journal DRAFT (siklus pendapatan)."""
        tagihan = self.get_object()
        try:
            jurnal = post_pembayaran_tagihan(tagihan, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(
            {"tagihan": self.get_serializer(tagihan).data, "jurnal_id": str(jurnal.id)}
        )


# ---- kepegawaian & aset (Finance) ----
class PegawaiViewSet(viewsets.ModelViewSet):
    queryset = Pegawai.objects.all().order_by("nama")
    serializer_class = PegawaiSerializer
    permission_classes = [IsFinanceOrReadOnly]


class PinjamanPegawaiViewSet(viewsets.ModelViewSet):
    queryset = PinjamanPegawai.objects.select_related("pegawai")
    serializer_class = PinjamanPegawaiSerializer
    permission_classes = [IsFinanceOrReadOnly]

    @action(detail=True, methods=["post"])
    def cairkan(self, request, pk=None):
        """Pencairan kasbon -> auto-journal (Dr Piutang, Cr Kas)."""
        pinjaman = self.get_object()
        try:
            jurnal = post_pencairan_kasbon(pinjaman, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})


class GajiPegawaiViewSet(viewsets.ModelViewSet):
    queryset = GajiPegawai.objects.select_related("pegawai")
    serializer_class = GajiPegawaiSerializer
    permission_classes = [IsFinanceOrReadOnly]

    @action(detail=True, methods=["post"])
    def posting(self, request, pk=None):
        """Posting payroll -> auto-journal beban gaji."""
        gaji = self.get_object()
        try:
            jurnal = post_gaji(gaji, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})


class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [IsFinanceOrReadOnly]

    @action(detail=True, methods=["post"])
    def susutkan(self, request, pk=None):
        """Penyusutan periodik -> auto-journal (Dr Beban Depr, Cr Akumulasi)."""
        aset = self.get_object()
        try:
            jurnal = post_penyusutan(aset, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response({"jurnal_id": str(jurnal.id)})
