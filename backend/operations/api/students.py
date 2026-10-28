"""API domain siswa."""

import django_filters
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import parsers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import ADMINISTRATION, FINANCE, TEACHER, role_permission

from operations.models import Jenjang, KehadiranSiswa, Kelompok, Siswa, Tagihan
from operations.serializers import (
    BiayaMasukDefaultSerializer,
    ImporBiodataHasilSerializer,
    ImporBiodataInputSerializer,
    ImporSppHasilSerializer,
    ImporSppInputSerializer,
    JenjangSerializer,
    KehadiranSiswaSerializer,
    KelompokSerializer,
    SiswaSerializer,
)
from operations.services import impor_biodata, impor_spp
from operations.services.biaya_masuk import default_biaya_masuk


class KehadiranSiswaFilter(django_filters.FilterSet):
    tanggal__gte = django_filters.DateFilter(field_name="tanggal", lookup_expr="gte")
    tanggal__lte = django_filters.DateFilter(field_name="tanggal", lookup_expr="lte")
    kelompok = django_filters.NumberFilter(field_name="siswa__kelompok")

    class Meta:
        model = KehadiranSiswa
        fields = ["tanggal", "siswa", "status", "tanggal__gte", "tanggal__lte", "kelompok"]


class JenjangViewSet(viewsets.ModelViewSet):
    queryset = Jenjang.objects.all().order_by("kode")
    serializer_class = JenjangSerializer
    permission_classes = [role_permission(read=(ADMINISTRATION, TEACHER, FINANCE), write=(ADMINISTRATION,))]

    def perform_destroy(self, instance):
        if instance.kelompok.exists():
            raise ValidationError(
                "Jenjang masih punya kelompok. Hapus atau pindahkan kelompok terlebih dahulu."
            )
        instance.delete()


class KelompokViewSet(viewsets.ModelViewSet):
    queryset = Kelompok.objects.select_related("jenjang").order_by("jenjang__kode", "nama")
    serializer_class = KelompokSerializer
    permission_classes = [role_permission(read=(ADMINISTRATION, TEACHER, FINANCE), write=(ADMINISTRATION,))]
    filterset_fields = ["jenjang"]

    def perform_destroy(self, instance):
        if instance.siswa.filter(status="aktif").exists():
            raise ValidationError(
                "Kelompok masih punya siswa aktif. Pindahkan siswa ke kelompok lain dulu."
            )
        instance.delete()

    @action(detail=True, methods=["post"], url_path="pindah-siswa")
    def pindah_siswa(self, request, pk=None):
        """Pindahkan beberapa siswa ke kelompok ini."""
        target = self.get_object()
        siswa_ids = request.data.get("siswa_ids") or []
        if not isinstance(siswa_ids, list) or not siswa_ids:
            raise ValidationError("Pilih minimal satu siswa untuk dipindah.")
        updated = Siswa.objects.filter(id__in=siswa_ids).update(kelompok=target)
        return Response({
            "detail": f"{updated} siswa dipindah ke {target.nama} ({target.jenjang.kode}).",
            "updated": updated,
        })


class SiswaViewSet(viewsets.ModelViewSet):
    queryset = Siswa.objects.prefetch_related(
        Prefetch(
            "tagihan",
            queryset=Tagihan.objects.filter(jenis="BIAYA_MASUK").prefetch_related("pembayaran").order_by("-pk"),
            to_attr="tagihan_biaya_masuk",
        )
    ).order_by("nama")
    serializer_class = SiswaSerializer
    permission_classes = [role_permission(read=(ADMINISTRATION, TEACHER, FINANCE), write=(ADMINISTRATION,))]
    filterset_fields = ["status", "kelompok"]
    search_fields = ["nis", "nama"]

    @extend_schema(
        parameters=[OpenApiParameter("kelompok", int), OpenApiParameter("tipe_tp", str)],
        responses=BiayaMasukDefaultSerializer,
    )
    @action(detail=False, methods=["get"], url_path="biaya-masuk-default")
    def biaya_masuk_default(self, request):
        """Nominal daftar harga untuk mengisi awal form biaya masuk."""
        kelompok_id = request.query_params.get("kelompok", "")
        if not kelompok_id.isdigit():
            raise ValidationError({"kelompok": "Pilih kelompok yang valid."})
        kelompok = Kelompok.objects.select_related("jenjang").filter(pk=int(kelompok_id)).first()
        tipe_tp = "lama" if request.query_params.get("tipe_tp") == "lama" else "baru"
        return Response(BiayaMasukDefaultSerializer(default_biaya_masuk(kelompok, tipe_tp)).data)

    @extend_schema(request={"multipart/form-data": ImporBiodataInputSerializer}, responses=ImporBiodataHasilSerializer)
    @action(detail=False, methods=["post"], url_path="impor-biodata", parser_classes=[parsers.MultiPartParser])
    def impor_biodata(self, request):
        """Pratinjau (simpan=false) atau simpan biodata dari CSV rekap kelas. Data keuangan tidak disentuh."""
        data = ImporBiodataInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        kelas_map = data.validated_data.get("kelas_map") or {}
        if not isinstance(kelas_map, dict):
            raise ValidationError({"kelas_map": "Format pemetaan kelas tidak valid."})
        kelompok_ids = set(Kelompok.objects.values_list("pk", flat=True))
        for kelas, kelompok in kelas_map.items():
            if kelompok is not None and kelompok not in kelompok_ids:
                raise ValidationError({"kelas_map": f"Kelompok untuk kelas {kelas} tidak ditemukan."})
        try:
            mentah = impor_biodata.parse_csv(data.validated_data["berkas"])
        except impor_biodata.ImporBiodataError as exc:
            raise ValidationError({"berkas": str(exc)})

        kelompok_list = list(Kelompok.objects.order_by("-pk"))
        kelas_info = {}
        for row in mentah:
            kelas_info.setdefault(row["kelas"], 0)
            kelas_info[row["kelas"]] += 1
        kelas = []
        for nama_kelas, jumlah in kelas_info.items():
            if nama_kelas in kelas_map:
                pilihan = kelas_map[nama_kelas]
            else:
                kunci = impor_biodata.kunci_nama(nama_kelas)
                pilihan = next((k.pk for k in kelompok_list if kunci and impor_biodata.kunci_nama(k.nama).startswith(kunci)), None)
            kelas.append({"kelas": nama_kelas, "jumlah": jumlah, "kelompok": pilihan})

        hasil = impor_biodata.susun_impor(mentah, {k["kelas"]: k["kelompok"] for k in kelas}, Siswa.objects.all())
        disimpan = data.validated_data["simpan"]
        if disimpan:
            impor_biodata.terapkan_impor(hasil, user=request.user)
        for item in hasil:
            item.pop("_nilai")
        return Response(ImporBiodataHasilSerializer({
            "disimpan": disimpan, "ringkasan": impor_biodata.ringkas(hasil), "kelas": kelas, "baris": hasil,
        }).data)

    @extend_schema(request={"multipart/form-data": ImporSppInputSerializer}, responses=ImporSppHasilSerializer)
    @action(detail=False, methods=["post"], url_path="impor-spp", parser_classes=[parsers.MultiPartParser])
    def impor_spp(self, request):
        """Pratinjau (simpan=false) atau isi SPP siswa yang masih Rp 0 dari tab master Recap Cash In."""
        data = ImporSppInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            mentah = impor_spp.parse_master(data.validated_data["berkas"])
        except impor_biodata.ImporBiodataError as exc:
            raise ValidationError({"berkas": str(exc)})
        hasil = impor_spp.susun_spp(mentah, Siswa.objects.all())
        disimpan = data.validated_data["simpan"]
        diisi = impor_spp.terapkan_spp(hasil, user=request.user) if disimpan else 0
        return Response(ImporSppHasilSerializer({
            "disimpan": disimpan, "diisi": diisi, "ringkasan": impor_spp.ringkas_spp(hasil), "baris": hasil,
        }).data)


class KehadiranSiswaViewSet(viewsets.ModelViewSet):
    queryset = KehadiranSiswa.objects.select_related("siswa").order_by("-tanggal")
    serializer_class = KehadiranSiswaSerializer
    # Absensi siswa diisi Staf TU dan Guru.
    permission_classes = [role_permission(read=(ADMINISTRATION, TEACHER), write=(ADMINISTRATION, TEACHER))]
    filterset_class = KehadiranSiswaFilter
