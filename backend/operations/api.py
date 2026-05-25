"""API operasional: master sekolah, layanan, kepegawaian, billing."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import (
    IsAdministration,
    IsFinanceOrReadOnly,
    IsFinanceWriteFinancePrincipalRead,
    IsTeacherOrPrincipal,
)

from .models import (
    AbsenPegawai,
    ArmadaJemputan,
    FixedAsset,
    GajiPegawai,
    Jenjang,
    KehadiranSiswa,
    Kegiatan,
    Kelompok,
    MenuKatering,
    Pegawai,
    PendaftaranJemputan,
    PendaftaranSiswa,
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
    KegiatanSerializer,
    KehadiranSiswaSerializer,
    KelompokSerializer,
    MenuKateringSerializer,
    PegawaiSerializer,
    PendaftaranJemputanSerializer,
    PendaftaranSiswaSerializer,
    PinjamanPegawaiSerializer,
    SiswaSerializer,
    TagihanSerializer,
)
from .services import (
    finalisasi_pendaftaran,
    generate_tagihan,
    post_bayar_sitin,
    post_gaji,
    post_pembayaran_tagihan,
    post_pencairan_kasbon,
    post_penyusutan,
    post_realisasi_kegiatan,
    struk_tagihan,
)


# ---- master & operasional sekolah (Administration) ----
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


class AbsenPegawaiViewSet(viewsets.ModelViewSet):
    queryset = AbsenPegawai.objects.select_related("pegawai").order_by("-tanggal")
    serializer_class = AbsenPegawaiSerializer
    permission_classes = [IsAdministration]


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


class TagihanViewSet(viewsets.ModelViewSet):
    serializer_class = TagihanSerializer
    permission_classes = [IsAdministration]
    filterset_fields = ["status", "periode_tahun", "siswa"]

    def get_queryset(self):
        return Tagihan.objects.select_related("siswa").prefetch_related("detail").order_by("-periode_tahun", "-periode_bulan")

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

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Rekap otomatis tagihan satu siswa per periode (SPP+katering+jemputan)."""
        from decimal import Decimal

        try:
            siswa = Siswa.objects.get(pk=request.data["siswa"])
            tagihan = generate_tagihan(
                siswa,
                int(request.data["periode_bulan"]),
                int(request.data["periode_tahun"]),
                Decimal(str(request.data.get("tarif_katering", 0))),
            )
        except Siswa.DoesNotExist:
            raise ValidationError("Siswa tidak ditemukan.")
        except (KeyError, ValueError) as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(tagihan).data, status=201)

    @action(detail=True, methods=["get"])
    def struk(self, request, pk=None):
        """Data struk/kwitansi untuk dicetak."""
        return Response(struk_tagihan(self.get_object()))


# ---- kepegawaian & aset (Finance) ----
class PegawaiViewSet(viewsets.ModelViewSet):
    queryset = Pegawai.objects.all().order_by("nama")
    serializer_class = PegawaiSerializer
    permission_classes = [IsFinanceOrReadOnly]


class PinjamanPegawaiViewSet(viewsets.ModelViewSet):
    queryset = PinjamanPegawai.objects.select_related("pegawai").order_by("-tanggal_pinjaman")
    serializer_class = PinjamanPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

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
    queryset = GajiPegawai.objects.select_related("pegawai").order_by("-periode_tahun", "-periode_bulan")
    serializer_class = GajiPegawaiSerializer
    permission_classes = [IsFinanceWriteFinancePrincipalRead]

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
    queryset = FixedAsset.objects.all().order_by("nama")
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


# ---- kegiatan sekolah (Teacher in Charge + Principal) ----
class KegiatanViewSet(viewsets.ModelViewSet):
    queryset = Kegiatan.objects.select_related("penanggung_jawab").order_by("-id")
    serializer_class = KegiatanSerializer
    permission_classes = [IsTeacherOrPrincipal]
    filterset_fields = ["status", "penanggung_jawab"]

    @action(detail=True, methods=["post"])
    def realisasi(self, request, pk=None):
        """Catat realisasi/pengeluaran kegiatan -> auto-journal beban (cek pagu)."""
        from datetime import date as _date

        kegiatan = self.get_object()
        try:
            r = post_realisasi_kegiatan(
                kegiatan,
                tanggal=request.data.get("tanggal") or _date.today(),
                deskripsi=request.data.get("deskripsi", ""),
                nominal=request.data["nominal"],
                user=request.user,
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError(str(exc))
        return Response({"realisasi_id": r.id, "jurnal_id": str(r.jurnal_id)}, status=201)

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


# ---- registrasi calon siswa (Administration) ----
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
        from decimal import Decimal

        try:
            p = finalisasi_pendaftaran(
                self.get_object(), user=request.user,
                spp_nominal=Decimal(str(request.data.get("spp_nominal", 0))),
            )
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(p).data)
