"""Laporan keuangan & dashboard (read-only).

Mengambil dari view SQL (v_neraca_saldo, v_realisasi_anggaran,
v_dataset_prediksi_kas) yang sudah memfilter jurnal POSTED.
"""

from decimal import Decimal

import django_filters
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


def _saldo_tahun(tahun, bulan=None, kumulatif=False):
    """Saldo akun dari jurnal POSTED dalam tahun (opsional: satu bulan atau kumulatif s.d. bulan)."""
    month_sql = ""
    params: list = [tahun]
    if bulan:
        if kumulatif:
            month_sql = " AND EXTRACT(MONTH FROM j.tanggal) <= %s"
        else:
            month_sql = " AND EXTRACT(MONTH FROM j.tanggal) = %s"
        params.append(bulan)
    return _rows(
        f"""
        SELECT
          c.kode_akun,
          c.nama_akun,
          c.posisi_normal,
          COALESCE(SUM(d.debit), 0) AS total_debit,
          COALESCE(SUM(d.kredit), 0) AS total_kredit,
          CASE
            WHEN c.posisi_normal = 'D'
              THEN COALESCE(SUM(d.debit), 0) - COALESCE(SUM(d.kredit), 0)
            ELSE COALESCE(SUM(d.kredit), 0) - COALESCE(SUM(d.debit), 0)
          END AS saldo_akhir
        FROM ms_coa c
        JOIN tr_jurnal_detail d ON d.kode_akun = c.kode_akun
        JOIN tr_jurnal j ON j.id = d.jurnal_id
          AND j.status = 'POSTED' AND NOT j.is_deleted
          AND EXTRACT(YEAR FROM j.tanggal) = %s{month_sql}
        WHERE c.is_active = TRUE
        GROUP BY c.kode_akun, c.nama_akun, c.posisi_normal
        ORDER BY c.kode_akun
        """,
        params,
    )


def _parse_period_params(request):
    """Query ?tahun=&bulan=&tanggal= (ISO) untuk filter dashboard/laporan."""
    from datetime import date

    today = date.today()
    tanggal_raw = request.query_params.get("tanggal")
    if tanggal_raw:
        d = date.fromisoformat(tanggal_raw)
        return {"mode": "day", "tanggal": d, "bulan": d.month, "tahun": d.year}

    tahun_raw = request.query_params.get("tahun")
    bulan_raw = request.query_params.get("bulan")
    if tahun_raw and bulan_raw:
        return {
            "mode": "month",
            "tahun": int(tahun_raw),
            "bulan": int(bulan_raw),
            "tanggal": None,
        }
    if tahun_raw:
        return {
            "mode": "year",
            "tahun": int(tahun_raw),
            "bulan": None,
            "tanggal": None,
        }
    return {
        "mode": "month",
        "tahun": today.year,
        "bulan": today.month,
        "tanggal": None,
    }


@extend_schema(responses=OpenApiTypes.OBJECT)
class NeracaSaldoView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        tahun = request.query_params.get("tahun")
        if tahun:
            return Response(_saldo_tahun(int(tahun)))
        return Response(_rows("SELECT * FROM v_neraca_saldo ORDER BY kode_akun"))


@extend_schema(responses=OpenApiTypes.OBJECT)
class LabaRugiView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        tahun = request.query_params.get("tahun")
        bulan = request.query_params.get("bulan")
        if tahun:
            data = _saldo_tahun(int(tahun), int(bulan) if bulan else None)
        else:
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
        tahun = request.query_params.get("tahun")
        if tahun:
            data = _saldo_tahun(int(tahun))
        else:
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
        tahun = request.query_params.get("tahun")
        bulan = request.query_params.get("bulan")
        sql = """
            SELECT j.no_bukti, j.tanggal, j.keterangan, d.debit, d.kredit
            FROM tr_jurnal_detail d
            JOIN tr_jurnal j ON j.id = d.jurnal_id
            WHERE d.kode_akun = %s AND j.status = 'POSTED' AND NOT j.is_deleted
        """
        params: list = [kode_akun]
        if tahun:
            sql += " AND EXTRACT(YEAR FROM j.tanggal) = %s"
            params.append(int(tahun))
        if bulan:
            sql += " AND EXTRACT(MONTH FROM j.tanggal) = %s"
            params.append(int(bulan))
        sql += " ORDER BY j.tanggal, j.no_bukti"
        return Response(_rows(sql, params))


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardRingkasanView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        period = _parse_period_params(request)
        saldo = _saldo_tahun(period["tahun"], period.get("bulan"))
        saldo_kas = (
            _saldo_tahun(period["tahun"], period.get("bulan"), kumulatif=True)
            if period.get("bulan")
            else saldo
        )
        kas = sum((r["saldo_akhir"] for r in saldo_kas
                   if str(r["kode_akun"]).startswith("1.1")
                   or str(r["kode_akun"]) in ("1011", "1101", "1102", "111", "112")), Decimal(0))
        pendapatan = sum((r["saldo_akhir"] for r in saldo
                          if str(r["kode_akun"]).startswith("4")), Decimal(0))
        beban = sum((r["saldo_akhir"] for r in saldo
                     if str(r["kode_akun"]).startswith("5")), Decimal(0))
        anggaran = _rows(
            "SELECT COALESCE(SUM(pagu),0) pagu, "
            "COALESCE(SUM(realisasi),0) realisasi FROM v_realisasi_anggaran "
            "WHERE tahun_anggaran = %s",
            [period["tahun"]],
        )

        from datetime import date

        from django.db.models import Sum

        from accounting.models import TrJurnal
        from operations.models import KehadiranSiswa, Siswa, Tagihan

        bulan, tahun = period["bulan"], period["tahun"]
        if period["mode"] == "day" and period["tanggal"]:
            d = period["tanggal"]
            hadir_qs = KehadiranSiswa.objects.filter(tanggal=d, status="hadir")
            ops_label = d.isoformat()
        elif period["mode"] == "year":
            hadir_qs = KehadiranSiswa.objects.filter(
                tanggal__year=tahun, status="hadir",
            )
            ops_label = str(tahun)
        else:
            hadir_qs = KehadiranSiswa.objects.filter(
                tanggal__year=tahun, tanggal__month=bulan, status="hadir",
            )
            ops_label = f"{bulan}/{tahun}"

        tagihan_qs = Tagihan.objects.filter(is_deleted=False)
        if period["mode"] == "year":
            tagihan_qs = tagihan_qs.filter(periode_tahun=tahun)
        elif period["mode"] in ("month", "day"):
            tagihan_qs = tagihan_qs.filter(periode_tahun=tahun, periode_bulan=bulan)

        belum_qs = tagihan_qs.filter(status="BELUM")
        lunas_count = tagihan_qs.filter(status="LUNAS").count()
        total_count = tagihan_qs.count()

        sparkline = []
        if period["mode"] == "day" and period["tanggal"]:
            d = period["tanggal"]
            for i in range(6):
                day = d.fromordinal(d.toordinal() - (5 - i))
                sparkline.append({
                    "bulan": day.month,
                    "tahun": day.year,
                    "label": day.strftime("%d/%m"),
                    "hadir": KehadiranSiswa.objects.filter(
                        tanggal=day, status="hadir",
                    ).count(),
                })
        elif period["mode"] == "year":
            today = date.today()
            end_m = 12 if tahun < today.year else today.month
            start_m = max(1, end_m - 5)
            for m in range(start_m, end_m + 1):
                sparkline.append({
                    "bulan": m,
                    "tahun": tahun,
                    "label": f"{m}/{tahun}",
                    "hadir": KehadiranSiswa.objects.filter(
                        tanggal__year=tahun, tanggal__month=m, status="hadir",
                    ).count(),
                })
        else:
            m, y = bulan or date.today().month, tahun
            for _ in range(6):
                sparkline.append({
                    "bulan": m,
                    "tahun": y,
                    "label": f"{m}/{y}",
                    "hadir": KehadiranSiswa.objects.filter(
                        tanggal__year=y, tanggal__month=m, status="hadir",
                    ).count(),
                })
                m -= 1
                if m <= 0:
                    m += 12
                    y -= 1
            sparkline.reverse()

        operasional = {
            "siswa_aktif": Siswa.objects.filter(status="aktif", is_deleted=False).count(),
            "hadir_bulan_ini": hadir_qs.count(),
            "katering_bulan_ini": hadir_qs.filter(ikut_katering=True).count(),
            "tagihan_belum": belum_qs.count(),
            "tagihan_belum_nominal": belum_qs.aggregate(t=Sum("total"))["t"] or Decimal(0),
            "collection_rate_pct": round(lunas_count / total_count * 100) if total_count else 0,
            "jurnal_menunggu_approve": TrJurnal.objects.filter(
                status="DRAFT", is_deleted=False,
            ).count(),
            "absensi_sparkline": sparkline,
            "periode_ops_label": ops_label,
        }

        if period["mode"] == "day":
            periode_label = period["tanggal"].isoformat()
        elif period["mode"] == "year":
            periode_label = str(tahun)
        else:
            periode_label = f"{bulan}/{tahun}"

        return Response({
            "kas": kas,
            "total_pendapatan": pendapatan,
            "total_beban": beban,
            "surplus_defisit": pendapatan - beban,
            "anggaran": anggaran[0] if anggaran else {"pagu": 0, "realisasi": 0},
            "operasional": operasional,
            "periode_filter": {
                "mode": period["mode"],
                "tahun": tahun,
                "bulan": bulan,
                "tanggal": period["tanggal"].isoformat() if period.get("tanggal") else None,
                "label": periode_label,
            },
        })


@extend_schema(responses=OpenApiTypes.OBJECT)
class PrediksiKasView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        tahun = request.query_params.get("tahun")
        if tahun:
            return Response(_rows(
                "SELECT * FROM v_dataset_prediksi_kas WHERE tahun = %s ORDER BY bulan",
                [int(tahun)],
            ))
        return Response(_rows("SELECT * FROM v_dataset_prediksi_kas"))


@extend_schema(responses=OpenApiTypes.OBJECT)
class LabaRugiBulananView(APIView):
    """Agregasi pendapatan & beban per bulan untuk tahun tertentu."""

    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        try:
            tahun = int(request.query_params.get("tahun") or 0)
        except ValueError:
            tahun = 0
        if not tahun:
            from datetime import date
            tahun = date.today().year

        rows = _rows(
            """
            SELECT
              EXTRACT(MONTH FROM j.tanggal)::int AS bulan,
              substring(c.kode_akun FROM 1 FOR 1) AS gol,
              SUM(d.debit)  AS deb,
              SUM(d.kredit) AS kre
            FROM tr_jurnal_detail d
            JOIN tr_jurnal j ON j.id = d.jurnal_id
            JOIN ms_coa c ON c.kode_akun = d.kode_akun
            WHERE j.status = 'POSTED' AND NOT j.is_deleted
              AND EXTRACT(YEAR FROM j.tanggal) = %s
              AND substring(c.kode_akun FROM 1 FOR 1) IN ('4','5')
            GROUP BY 1, 2
            ORDER BY 1
            """,
            [tahun],
        )

        bulanan = {m: {"bulan": m, "pendapatan": 0, "beban": 0} for m in range(1, 13)}
        for r in rows:
            m = r["bulan"]
            deb, kre = float(r["deb"] or 0), float(r["kre"] or 0)
            if r["gol"] == "4":
                bulanan[m]["pendapatan"] += kre - deb
            else:
                bulanan[m]["beban"] += deb - kre

        return Response({"tahun": tahun, "data": list(bulanan.values())})


@extend_schema(responses=OpenApiTypes.OBJECT)
class MenuKateringHariIniView(APIView):
    """Menu katering hari ini (atau tanggal tertentu) — untuk widget dashboard."""

    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        from datetime import date

        from operations.models import MenuKatering
        from operations.serializers import MenuKateringSerializer

        tanggal_raw = request.query_params.get("tanggal")
        tanggal = date.fromisoformat(tanggal_raw) if tanggal_raw else date.today()
        menu = MenuKatering.objects.filter(tanggal=tanggal).first()
        if not menu:
            return Response({"tanggal": tanggal.isoformat(), "menu": None})
        ser = MenuKateringSerializer(menu, context={"request": request})
        return Response({"tanggal": tanggal.isoformat(), "menu": ser.data})


class AuditLogFilter(django_filters.FilterSet):
    changed_at__gte = django_filters.DateTimeFilter(
        field_name="changed_at", lookup_expr="gte",
    )
    changed_at__lte = django_filters.DateTimeFilter(
        field_name="changed_at", lookup_expr="lte",
    )

    class Meta:
        model = AuditLog
        fields = [
            "table_name", "action", "changed_by",
            "changed_at__gte", "changed_at__lte",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(
        source="changed_by.username", read_only=True, default=None,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id", "table_name", "row_pk", "action",
            "old_data", "new_data", "changed_by", "changed_by_username",
            "changed_at",
        ]


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = AuditLog.objects.select_related("changed_by").order_by("-changed_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsFinanceOrPrincipal]
    filterset_class = AuditLogFilter
    search_fields = ["table_name", "row_pk", "action"]
    ordering_fields = ["changed_at", "table_name", "action"]
