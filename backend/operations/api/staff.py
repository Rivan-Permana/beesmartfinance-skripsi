"""API domain kepegawaian (master & absensi)."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministrationOrFinance, IsAdministrationOrFinanceOrPrincipalRead

from operations.models import AbsenPegawai, Pegawai
from operations.serializers import AbsenPegawaiSerializer, PegawaiSerializer


class PegawaiViewSet(viewsets.ModelViewSet):
    queryset = Pegawai.objects.all().order_by("nama", "pk")
    serializer_class = PegawaiSerializer
    permission_classes = [IsAdministrationOrFinanceOrPrincipalRead]


class AbsenPegawaiViewSet(viewsets.ModelViewSet):
    queryset = AbsenPegawai.objects.select_related("pegawai").order_by("-tanggal")
    serializer_class = AbsenPegawaiSerializer
    permission_classes = [IsAdministrationOrFinance]
    filterset_fields = ["pegawai", "tanggal"]

    @action(detail=False, methods=["post"], url_path="bulk-save")
    def bulk_save(self, request):
        """Simpan absensi harian banyak pegawai sekaligus."""
        tanggal = request.data.get("tanggal")
        items = request.data.get("items", [])
        if not tanggal:
            raise ValidationError("tanggal wajib diisi.")
        saved = []
        for item in items:
            pegawai_id = item.get("pegawai")
            if not pegawai_id:
                continue
            defaults = {
                "hadir": int(item.get("hadir") or 0),
                "izin": int(item.get("izin") or 0),
                "sakit": int(item.get("sakit") or 0),
                "terlambat": int(item.get("terlambat") or 0),
            }
            if sum(defaults.values()) == 0:
                AbsenPegawai.objects.filter(pegawai_id=pegawai_id, tanggal=tanggal).delete()
                continue
            obj, _ = AbsenPegawai.objects.update_or_create(
                pegawai_id=pegawai_id, tanggal=tanggal, defaults=defaults,
            )
            saved.append(obj)
        return Response({
            "detail": f"{len(saved)} absensi tersimpan.",
            "count": len(saved),
        })

    @action(detail=False, methods=["get"], url_path="rekap-bulanan")
    def rekap_bulanan(self, request):
        """Agregat hadir/izin/sakit/terlambat per pegawai dalam satu bulan."""
        try:
            bulan = int(request.query_params.get("bulan", 0))
            tahun = int(request.query_params.get("tahun", 0))
        except ValueError:
            raise ValidationError("bulan dan tahun harus angka.")
        if not bulan or not tahun:
            raise ValidationError("bulan dan tahun wajib diisi.")

        qs = AbsenPegawai.objects.filter(
            tanggal__year=tahun, tanggal__month=bulan,
        ).select_related("pegawai")
        agg: dict[int, dict] = {}
        for row in qs:
            pid = row.pegawai_id
            if pid not in agg:
                agg[pid] = {
                    "pegawai": pid,
                    "nama": str(row.pegawai),
                    "hadir": 0, "izin": 0, "sakit": 0, "terlambat": 0,
                }
            agg[pid]["hadir"] += row.hadir
            agg[pid]["izin"] += row.izin
            agg[pid]["sakit"] += row.sakit
            agg[pid]["terlambat"] += row.terlambat
        return Response(sorted(agg.values(), key=lambda x: x["nama"]))
