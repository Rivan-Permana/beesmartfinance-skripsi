"""Laporan keuangan & dashboard (read-only).

Mengambil dari view SQL (v_neraca_saldo, v_realisasi_anggaran,
v_dataset_prediksi_kas) yang sudah memfilter jurnal POSTED.
"""

from datetime import date
from decimal import Decimal

import django_filters
from django.db import connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFinanceOrPrincipal, IsPrincipal

from .models import AuditLog


def _rows(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _bulan_berikut(tahun, bulan):
    return date(tahun + 1, 1, 1) if bulan == 12 else date(tahun, bulan + 1, 1)


def _saldo_tahun(tahun, bulan=None, kumulatif=False, dengan_saldo_awal=True):
    """Mutasi periode atau saldo kumulatif sampai akhir periode, termasuk saldo awal bertanggal."""
    awal = date(tahun, bulan or 1, 1)
    akhir = _bulan_berikut(tahun, bulan) if bulan else date(tahun + 1, 1, 1)
    return _saldo_range(awal, akhir, kumulatif=kumulatif, dengan_saldo_awal=dengan_saldo_awal)


def _saldo_range(awal, akhir, kumulatif=False, dengan_saldo_awal=True):
    """Seperti _saldo_tahun untuk rentang tanggal [awal, akhir)."""
    mutasi_mulai = "" if kumulatif else " AND j.tanggal >= %s"
    opening_mulai = "" if kumulatif else " AND c.tanggal_saldo_awal >= %s"
    params: list = [akhir]
    if not kumulatif:
        params.append(awal)
    params.extend([dengan_saldo_awal, akhir])
    if not kumulatif:
        params.append(awal)
    return _rows(
        f"""
        WITH mutasi AS (
          SELECT d.kode_akun, SUM(d.debit) AS debit, SUM(d.kredit) AS kredit
          FROM tr_jurnal_detail d JOIN tr_jurnal j ON j.id = d.jurnal_id
          JOIN ms_coa c ON c.kode_akun = d.kode_akun
          WHERE j.status = 'POSTED' AND NOT j.is_deleted
            AND j.tanggal < %s{mutasi_mulai}
            AND (c.tanggal_saldo_awal IS NULL OR j.tanggal >= c.tanggal_saldo_awal)
          GROUP BY d.kode_akun
        ), saldo AS (
          SELECT c.kode_akun, c.nama_akun, c.posisi_normal,
            COALESCE(m.debit, 0) AS debit, COALESCE(m.kredit, 0) AS kredit,
            CASE WHEN %s AND c.tanggal_saldo_awal < %s{opening_mulai}
              THEN c.saldo_awal ELSE 0 END AS opening
          FROM ms_coa c LEFT JOIN mutasi m ON m.kode_akun = c.kode_akun
        )
        SELECT kode_akun, nama_akun, posisi_normal,
          debit + GREATEST(CASE WHEN posisi_normal = 'D' THEN opening ELSE -opening END, 0) AS total_debit,
          kredit + GREATEST(CASE WHEN posisi_normal = 'K' THEN opening ELSE -opening END, 0) AS total_kredit,
          opening + CASE WHEN posisi_normal = 'D' THEN debit - kredit ELSE kredit - debit END AS saldo_akhir
        FROM saldo ORDER BY kode_akun
        """,
        params,
    )


def _parse_period_params(request):
    """Query ?periode=<id> | ?tanggal= (ISO) | ?tahun=&bulan= untuk filter dashboard/laporan.

    Selalu menyertakan rentang tanggal ``awal``..``akhir`` (akhir eksklusif).
    """
    today = date.today()
    try:
        periode_raw = request.query_params.get("periode")
        if periode_raw:
            from .models import MsPeriodeAkuntansi
            periode = MsPeriodeAkuntansi.objects.filter(pk=int(periode_raw)).first()
            if not periode:
                raise ValidationError({"periode": "Periode akuntansi tidak ditemukan."})
            return {
                "mode": "period", "tanggal": None, "bulan": None,
                "tahun": periode.tgl_mulai.year, "periode": periode,
                "awal": periode.tgl_mulai, "akhir": date.fromordinal(periode.tgl_selesai.toordinal() + 1),
            }

        tanggal_raw = request.query_params.get("tanggal")
        if tanggal_raw:
            d = date.fromisoformat(tanggal_raw)
            return {
                "mode": "day", "tanggal": d, "bulan": d.month, "tahun": d.year,
                "awal": d, "akhir": date.fromordinal(d.toordinal() + 1),
            }

        tahun_raw = request.query_params.get("tahun")
        bulan_raw = request.query_params.get("bulan")
        if tahun_raw and bulan_raw:
            tahun, bulan = int(tahun_raw), int(bulan_raw)
            return {
                "mode": "month", "tahun": tahun, "bulan": bulan, "tanggal": None,
                "awal": date(tahun, bulan, 1), "akhir": _bulan_berikut(tahun, bulan),
            }
        if tahun_raw:
            tahun = int(tahun_raw)
            return {
                "mode": "year", "tahun": tahun, "bulan": None, "tanggal": None,
                "awal": date(tahun, 1, 1), "akhir": date(tahun + 1, 1, 1),
            }
    except ValueError:
        raise ValidationError({"detail": "Parameter periode, tanggal, tahun, atau bulan tidak valid."})
    return {
        "mode": "month", "tahun": today.year, "bulan": today.month, "tanggal": None,
        "awal": date(today.year, today.month, 1), "akhir": _bulan_berikut(today.year, today.month),
    }


def _bulan_dalam_rentang(awal, akhir):
    """Pasangan (tahun, bulan) yang beririsan dengan [awal, akhir)."""
    out, y, m = [], awal.year, awal.month
    while date(y, m, 1) < akhir:
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


@extend_schema(responses=OpenApiTypes.OBJECT)
class NeracaSaldoView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        tahun = request.query_params.get("tahun")
        if tahun:
            return Response(_saldo_tahun(int(tahun), kumulatif=True))
        return Response(_rows("SELECT * FROM v_neraca_saldo ORDER BY kode_akun"))


@extend_schema(responses=OpenApiTypes.OBJECT)
class LabaRugiView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        if any(request.query_params.get(key) for key in ("tahun", "tanggal", "periode")):
            period = _parse_period_params(request)
            data = _saldo_range(period["awal"], period["akhir"])
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
            data = _saldo_tahun(int(tahun), kumulatif=True)
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
            JOIN ms_coa c ON c.kode_akun = d.kode_akun
            WHERE d.kode_akun = %s AND j.status = 'POSTED' AND NOT j.is_deleted
              AND (c.tanggal_saldo_awal IS NULL OR j.tanggal >= c.tanggal_saldo_awal)
        """
        params: list = [kode_akun]
        if tahun:
            sql += " AND EXTRACT(YEAR FROM j.tanggal) = %s"
            params.append(int(tahun))
        if bulan:
            sql += " AND EXTRACT(MONTH FROM j.tanggal) = %s"
            params.append(int(bulan))
        sql += " ORDER BY j.tanggal, j.no_bukti"
        rows = _rows(sql, params)
        from .models import MsCoa

        akun = MsCoa.objects.filter(pk=kode_akun).first()
        if akun:
            mulai = date(int(tahun), int(bulan) if bulan else 1, 1) if tahun else akun.tanggal_saldo_awal
            raw_opening = akun.saldo_awal if akun.posisi_normal == "D" else -akun.saldo_awal
            if mulai and akun.tanggal_saldo_awal and akun.tanggal_saldo_awal > mulai:
                raw_opening = Decimal(0)
            if mulai and tahun:
                prior = _rows(
                    "SELECT COALESCE(SUM(d.debit - d.kredit), 0) AS saldo "
                    "FROM tr_jurnal_detail d JOIN tr_jurnal j ON j.id = d.jurnal_id "
                    "WHERE d.kode_akun = %s AND j.status = 'POSTED' AND NOT j.is_deleted "
                    "AND j.tanggal < %s AND (%s::date IS NULL OR j.tanggal >= %s::date)",
                    [kode_akun, mulai, akun.tanggal_saldo_awal, akun.tanggal_saldo_awal],
                )[0]["saldo"]
                raw_opening += prior
            if raw_opening and mulai:
                rows.insert(0, {"no_bukti": "SALDO-AWAL", "tanggal": mulai,
                    "keterangan": "Saldo awal periode", "debit": max(raw_opening, Decimal(0)),
                    "kredit": max(-raw_opening, Decimal(0))})
            if tahun and akun.tanggal_saldo_awal and akun.tanggal_saldo_awal > mulai:
                tanggal = akun.tanggal_saldo_awal
                if tanggal.year == int(tahun) and (not bulan or tanggal.month == int(bulan)) and akun.saldo_awal:
                    raw = akun.saldo_awal if akun.posisi_normal == "D" else -akun.saldo_awal
                    rows.append({"no_bukti": "SALDO-AWAL", "tanggal": tanggal,
                        "keterangan": "Saldo awal akun", "debit": max(raw, Decimal(0)),
                        "kredit": max(-raw, Decimal(0))})
                    rows.sort(key=lambda row: (row["tanggal"], row["no_bukti"] != "SALDO-AWAL", row["no_bukti"]))
        return Response(rows)


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardRingkasanView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        period = _parse_period_params(request)
        awal, akhir = period["awal"], period["akhir"]
        saldo = _saldo_range(awal, akhir, dengan_saldo_awal=False)
        saldo_kas = _saldo_range(awal, akhir, kumulatif=True)
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

        from django.db.models import Q

        from accounting.models import TrJurnal
        from operations.models import KehadiranSiswa, Siswa, Tagihan

        bulan, tahun = period["bulan"], period["tahun"]
        if period["mode"] == "day" and period["tanggal"]:
            d = period["tanggal"]
            hadir_qs = KehadiranSiswa.objects.filter(tanggal=d, status="hadir")
            ops_label = d.isoformat()
        elif period["mode"] == "period":
            hadir_qs = KehadiranSiswa.objects.filter(tanggal__gte=awal, tanggal__lt=akhir, status="hadir")
            ops_label = period["periode"].kode
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
        if period["mode"] == "period":
            bulan_q = Q(pk__in=[])
            for y, m in _bulan_dalam_rentang(awal, akhir):
                bulan_q |= Q(periode_tahun=y, periode_bulan=m)
            tagihan_qs = tagihan_qs.filter(bulan_q)
        elif period["mode"] == "year":
            tagihan_qs = tagihan_qs.filter(periode_tahun=tahun)
        elif period["mode"] in ("month", "day"):
            tagihan_qs = tagihan_qs.filter(periode_tahun=tahun, periode_bulan=bulan)

        belum_qs = tagihan_qs.filter(status__in=["BELUM", "SEBAGIAN"], perlu_rekonsiliasi=False).prefetch_related("pembayaran")
        lunas_count = tagihan_qs.filter(status="LUNAS", perlu_rekonsiliasi=False).count()
        total_count = tagihan_qs.filter(perlu_rekonsiliasi=False).count()

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
        elif period["mode"] == "period":
            today = date.today()
            pairs = [(y, m) for y, m in _bulan_dalam_rentang(awal, akhir) if date(y, m, 1) <= today]
            for y, m in pairs[-6:]:
                sparkline.append({
                    "bulan": m,
                    "tahun": y,
                    "label": f"{m}/{y}",
                    "hadir": KehadiranSiswa.objects.filter(
                        tanggal__year=y, tanggal__month=m, status="hadir",
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
            "tagihan_belum_nominal": sum((t.sisa_tagihan for t in belum_qs), Decimal(0)),
            "tagihan_perlu_rekonsiliasi": tagihan_qs.filter(perlu_rekonsiliasi=True).count(),
            "collection_rate_pct": round(lunas_count / total_count * 100) if total_count else 0,
            "jurnal_menunggu_approve": TrJurnal.objects.filter(
                status__in=["DRAFT", "PENDING"], is_deleted=False,
            ).count(),
            "absensi_sparkline": sparkline,
            "periode_ops_label": ops_label,
        }

        if period["mode"] == "day":
            periode_label = period["tanggal"].isoformat()
        elif period["mode"] == "period":
            periode_label = f"Periode {period['periode'].kode}"
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
                "periode": period["periode"].pk if period.get("periode") else None,
                "awal": awal.isoformat(),
                "akhir": date.fromordinal(akhir.toordinal() - 1).isoformat(),
                "label": periode_label,
            },
        })


@extend_schema(responses=OpenApiTypes.OBJECT)
class PrediksiKasView(APIView):
    permission_classes = [IsFinanceOrPrincipal]

    def get(self, request):
        if request.query_params.get("periode"):
            period = _parse_period_params(request)
            pairs = _bulan_dalam_rentang(period["awal"], period["akhir"])
            return Response(_rows(
                "SELECT * FROM v_dataset_prediksi_kas WHERE tahun * 100 + bulan BETWEEN %s AND %s "
                "ORDER BY tahun, bulan",
                [pairs[0][0] * 100 + pairs[0][1], pairs[-1][0] * 100 + pairs[-1][1]],
            ))
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
        if request.query_params.get("periode"):
            period = _parse_period_params(request)
            rows = _rows(
                """
                SELECT
                  EXTRACT(YEAR FROM j.tanggal)::int AS tahun,
                  EXTRACT(MONTH FROM j.tanggal)::int AS bulan,
                  substring(c.kode_akun FROM 1 FOR 1) AS gol,
                  SUM(d.debit)  AS deb,
                  SUM(d.kredit) AS kre
                FROM tr_jurnal_detail d
                JOIN tr_jurnal j ON j.id = d.jurnal_id
                JOIN ms_coa c ON c.kode_akun = d.kode_akun
                WHERE j.status = 'POSTED' AND NOT j.is_deleted
                  AND j.tanggal >= %s AND j.tanggal < %s
                  AND substring(c.kode_akun FROM 1 FOR 1) IN ('4','5')
                GROUP BY 1, 2, 3
                """,
                [period["awal"], period["akhir"]],
            )
            bulanan = {
                (y, m): {"tahun": y, "bulan": m, "pendapatan": 0, "beban": 0}
                for y, m in _bulan_dalam_rentang(period["awal"], period["akhir"])
            }
            for r in rows:
                item = bulanan[(r["tahun"], r["bulan"])]
                deb, kre = float(r["deb"] or 0), float(r["kre"] or 0)
                if r["gol"] == "4":
                    item["pendapatan"] += kre - deb
                else:
                    item["beban"] += deb - kre
            return Response({"tahun": period["tahun"], "periode": period["periode"].kode, "data": list(bulanan.values())})

        try:
            tahun = int(request.query_params.get("tahun") or 0)
        except ValueError:
            tahun = 0
        if not tahun:
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

        bulanan = {m: {"tahun": tahun, "bulan": m, "pendapatan": 0, "beban": 0} for m in range(1, 13)}
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
