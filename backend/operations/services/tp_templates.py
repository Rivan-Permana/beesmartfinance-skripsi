"""Template komponen biaya TP + integrasi tagihan tahunan (E10 / story 10.2)."""

from __future__ import annotations

from decimal import Decimal

from operations.models import KomponenBiayaTemplate, TagihanDetail

# Nilai canonical dari PDF TA 2025/26 (guide §2.2)
TP_TEMPLATE_ROWS: list[dict] = [
    # PG Semester I — siswa baru
    {"kode": "UANG_MASUK", "nama": "Uang Masuk PG", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "700000", "urutan": 1},
    {"kode": "KEGIATAN", "nama": "Uang Kegiatan Semester I", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "2500000", "urutan": 2},
    {"kode": "PENGEMBANGAN", "nama": "Uang Pengembangan Semester I", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "1000000", "urutan": 3},
    {"kode": "SERAGAM", "nama": "Seragam Sekolah (1 stel)", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "200000", "urutan": 4},
    {"kode": "PORTOFOLIO", "nama": "Portofolio & Rapor", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "300000", "urutan": 5},
    {"kode": "KOMITE", "nama": "Iuran Komite (1 semester)", "jenjang": "PG", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "375000", "urutan": 6},
    # RA tahun pertama — siswa baru
    {"kode": "UANG_MASUK", "nama": "Uang Masuk RA", "jenjang": "RA", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "3200000", "urutan": 1},
    {"kode": "KEGIATAN", "nama": "Uang Kegiatan Ananda", "jenjang": "RA", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "4500000", "urutan": 2},
    {"kode": "PENGEMBANGAN", "nama": "Uang Pengembangan", "jenjang": "RA", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "1650000", "urutan": 3},
    {"kode": "SERAGAM", "nama": "Seragam (2 stel + Batik IGRA)", "jenjang": "RA", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "400000", "urutan": 4},
    {"kode": "KOMITE", "nama": "Iuran Komite (1 tahun)", "jenjang": "RA", "tipe_siswa": "baru", "tahun_ke": 1, "nominal": "750000", "urutan": 5},
    # RA tahun kedua — daftar ulang
    {"kode": "KEGIATAN", "nama": "Uang Kegiatan", "jenjang": "RA", "tipe_siswa": "lama", "tahun_ke": 2, "nominal": "4500000", "urutan": 1},
    {"kode": "PENGEMBANGAN", "nama": "Uang Pengembangan", "jenjang": "RA", "tipe_siswa": "lama", "tahun_ke": 2, "nominal": "1650000", "urutan": 2},
    {"kode": "KOMITE", "nama": "Iuran Komite (1 tahun)", "jenjang": "RA", "tipe_siswa": "lama", "tahun_ke": 2, "nominal": "750000", "urutan": 3},
]


def ensure_tp_templates(*, bulan_tagih: int = 7) -> int:
    """Idempotent seed template TP dari PDF. Return jumlah baris upsert."""
    count = 0
    for row in TP_TEMPLATE_ROWS:
        KomponenBiayaTemplate.objects.update_or_create(
            kode=row["kode"],
            jenjang=row["jenjang"],
            tipe_siswa=row["tipe_siswa"],
            tahun_ke=row["tahun_ke"],
            defaults={
                "nama": row["nama"],
                "nominal": Decimal(row["nominal"]),
                "bulan_tagih": bulan_tagih,
                "urutan": row["urutan"],
                "aktif": True,
            },
        )
        count += 1
    return count


def _jenjang_template_key(siswa) -> str | None:
    if not siswa.kelompok_id:
        return None
    kode = siswa.kelompok.jenjang.kode
    if kode == "PG":
        return "PG"
    if kode in ("TKA", "TKB"):
        return "RA"
    return None


def _tahun_ke_for_siswa(siswa) -> int:
    if siswa.tipe_tp == "lama":
        return 2
    return 1


def _already_billed(siswa, kode: str, tahun: int) -> bool:
    return TagihanDetail.objects.filter(
        tagihan__siswa=siswa,
        tagihan__periode_tahun=tahun,
        komponen=kode,
    ).exists()


def _akun_for_komponen(kode: str):
    from operations.services.common import akun_rule

    try:
        return akun_rule(kode)
    except ValueError:
        return akun_rule("LAIN")


def annual_komponen_lines(siswa, periode_bulan: int, periode_tahun: int) -> list[dict]:
    """Komponen tahunan TP yang belum ditagih untuk siswa & periode."""
    jk = _jenjang_template_key(siswa)
    if not jk:
        return []

    tipe = siswa.tipe_tp or "baru"
    tahun_ke = _tahun_ke_for_siswa(siswa)

    templates = KomponenBiayaTemplate.objects.filter(
        aktif=True,
        jenjang=jk,
        bulan_tagih=periode_bulan,
        tahun_ke=tahun_ke,
    ).filter(tipe_siswa__in=[tipe, "all"]).order_by("urutan", "kode")

    lines: list[dict] = []
    for tpl in templates:
        if tpl.nominal == 0:
            continue
        if _already_billed(siswa, tpl.kode, periode_tahun):
            continue
        lines.append({
            "komponen": tpl.kode,
            "kategori": "TAHUNAN",
            "keterangan": tpl.nama,
            "akun_pendapatan": _akun_for_komponen(tpl.kode),
            "nominal": tpl.nominal,
        })
    return lines
