"""Laporan keuangan & dashboard (read-only).

Mengambil dari view SQL (v_neraca_saldo, v_realisasi_anggaran,
v_dataset_prediksi_kas) yang sudah memfilter jurnal POSTED.
"""

from decimal import Decimal

from django.db import connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFinanceOrPrincipal, IsPrincipal

from .models import AuditLog


def _rows(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@extend_schema(responses=OpenApiTypes.OBJECT)
class NeracaSaldoView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        return Response(_rows("SELECT * FROM v_neraca_saldo ORDER BY kode_akun"))


@extend_schema(responses=OpenApiTypes.OBJECT)
class LabaRugiView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        data = _rows("SELECT * FROM v_neraca_saldo ORDER BY kode_akun")
        pendapatan = [r for r in data if str(r["kode_akun"]).startswith("4")]
        beban = [r for r in data if str(r["kode_akun"]).startswith("5")]
        total_pendapatan = sum((r["saldo_akhir"] for r in pendapatan), Decimal(0))
        total_beban = sum((r["saldo_akhir"] for r in beban), Decimal(0))
        return Response({
            "pendapatan": pendapatan,
            "beban": beban,
            "total_pendapatan": total_pendapatan,
            "total_beban": total_beban,
            "laba_rugi": total_pendapatan - total_beban,
        })


@extend_schema(responses=OpenApiTypes.OBJECT)
class PosisiKeuanganView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        data = _rows("SELECT * FROM v_neraca_saldo ORDER BY kode_akun")
        bucket = {"aset": [], "liabilitas": [], "ekuitas": []}
        for r in data:
            k = str(r["kode_akun"])[0]
            if k == "1":
                bucket["aset"].append(r)
            elif k == "2":
                bucket["liabilitas"].append(r)
            elif k == "3":
                bucket["ekuitas"].append(r)
        return Response(bucket)


@extend_schema(responses=OpenApiTypes.OBJECT)
class RealisasiAnggaranView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        tahun = request.query_params.get("tahun")
        if tahun:
            return Response(_rows(
                "SELECT * FROM v_realisasi_anggaran WHERE tahun_anggaran = %s "
                "ORDER BY kode_akun", [tahun]))
        return Response(_rows("SELECT * FROM v_realisasi_anggaran ORDER BY kode_akun"))


@extend_schema(responses=OpenApiTypes.OBJECT)
class BukuBesarView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request, kode_akun):
        return Response(_rows(
            """
            SELECT j.no_bukti, j.tanggal, j.keterangan, d.debit, d.kredit
            FROM tr_jurnal_detail d
            JOIN tr_jurnal j ON j.id = d.jurnal_id
            WHERE d.kode_akun = %s AND j.status = 'POSTED' AND NOT j.is_deleted
            ORDER BY j.tanggal, j.no_bukti
            """, [kode_akun]))


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardRingkasanView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        saldo = _rows("SELECT * FROM v_neraca_saldo")
        kas = sum((r["saldo_akhir"] for r in saldo
                   if str(r["kode_akun"]).startswith("1.1")
                   or str(r["kode_akun"]) in ("1101", "1102")), Decimal(0))
        pendapatan = sum((r["saldo_akhir"] for r in saldo
                          if str(r["kode_akun"]).startswith("4")), Decimal(0))
        beban = sum((r["saldo_akhir"] for r in saldo
                     if str(r["kode_akun"]).startswith("5")), Decimal(0))
        anggaran = _rows("SELECT COALESCE(SUM(pagu),0) pagu, "
                         "COALESCE(SUM(realisasi),0) realisasi FROM v_realisasi_anggaran")
        return Response({
            "kas": kas,
            "total_pendapatan": pendapatan,
            "total_beban": beban,
            "surplus_defisit": pendapatan - beban,
            "anggaran": anggaran[0] if anggaran else {"pagu": 0, "realisasi": 0},
        })


@extend_schema(responses=OpenApiTypes.OBJECT)
class PrediksiKasView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        return Response(_rows("SELECT * FROM v_dataset_prediksi_kas"))


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "table_name", "row_pk", "action",
                  "old_data", "new_data", "changed_by", "changed_at"]


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = AuditLog.objects.order_by("-changed_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsPrincipal]
