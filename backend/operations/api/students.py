"""API domain siswa."""

import django_filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministrationOrTeacherReadOnly

from operations.models import Jenjang, KehadiranSiswa, Kelompok, Siswa
from operations.serializers import (
    JenjangSerializer,
    KehadiranSiswaSerializer,
    KelompokSerializer,
    SiswaSerializer,
)


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
    permission_classes = [IsAdministrationOrTeacherReadOnly]

    def perform_destroy(self, instance):
        if instance.kelompok.exists():
            raise ValidationError(
                "Jenjang masih punya kelompok. Hapus atau pindahkan kelompok terlebih dahulu."
            )
        instance.delete()


class KelompokViewSet(viewsets.ModelViewSet):
    queryset = Kelompok.objects.select_related("jenjang").order_by("jenjang__kode", "nama")
    serializer_class = KelompokSerializer
    permission_classes = [IsAdministrationOrTeacherReadOnly]
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
    queryset = Siswa.objects.all().order_by("nama")
    serializer_class = SiswaSerializer
    permission_classes = [IsAdministrationOrTeacherReadOnly]
    filterset_fields = ["status", "kelompok"]
    search_fields = ["nis", "nama"]


class KehadiranSiswaViewSet(viewsets.ModelViewSet):
    queryset = KehadiranSiswa.objects.select_related("siswa").order_by("-tanggal")
    serializer_class = KehadiranSiswaSerializer
    permission_classes = [IsAdministrationOrTeacherReadOnly]
    filterset_class = KehadiranSiswaFilter
