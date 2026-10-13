"""Service siklus pendapatan: rekap tagihan, pembayaran, struk."""

import uuid
from datetime import date
from decimal import Decimal

from django.db import transaction

from accounting.models import TrJurnal, TrJurnalDetail

from .common import akun_rule, akun_sistem, audit_user

BULAN_NAMA = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

KATEGORI_LABELS = {
    "BULANAN": "Biaya Bulanan",
    "TAHUNAN": "Biaya Tahunan",
    "LAIN": "Lain-lain",
}


def _default_kategori(komponen):
    if komponen in ("SPP", "KATERING", "JEMPUTAN"):
        return "BULANAN"
    return "LAIN"


def _default_keterangan(
    komponen,
    *,
    hari_sen_kam=0,
    hari_jumat=0,
    tarif_sen_kam=Decimal(0),
    tarif_jumat=Decimal(0),
    hari_katering=0,
    tarif_katering=Decimal(0),
):
    if komponen == "SPP":
        return "SPP (Sumbangan Pembinaan Pendidikan)"
    if komponen == "KATERING":
        if hari_sen_kam or hari_jumat:
            parts = []
            if hari_sen_kam:
                parts.append(f"{hari_sen_kam}×Rp {int(tarif_sen_kam):,}".replace(",", "."))
            if hari_jumat:
                parts.append(f"{hari_jumat} Jumat×Rp {int(tarif_jumat):,}".replace(",", "."))
            return f"Katering ({' + '.join(parts)})"
        if hari_katering:
            return f"Katering ({hari_katering} hari × Rp {int(tarif_katering):,})".replace(",", ".")
        return "Katering"
    if komponen == "JEMPUTAN":
        return "Jemputan (antar jemput)"
    return komponen


def _jemput_keterangan(*, datang: int, pulang: int, tarif: Decimal) -> str:
    parts = []
    if datang:
        parts.append(f"{datang} datang")
    if pulang:
        parts.append(f"{pulang} pulang")
    trip_label = " + ".join(parts) if parts else "0 trip"
    tarif_fmt = f"Rp {int(tarif):,}".replace(",", ".")
    return f"Jemputan ({trip_label} × {tarif_fmt})"


def build_tagihan_komponen(siswa, periode_bulan, periode_tahun, tarif_katering=Decimal(0)):
    """Hitung komponen tagihan tanpa menyimpan ke DB."""
    from operations.models import KehadiranSiswa, PendaftaranJemputan
    from operations.services.katering_tarif import (
        get_tarif_katering_period,
        katering_breakdown_for_siswa,
    )
    from operations.services.tp_templates import annual_komponen_lines

    tarif_katering = Decimal(tarif_katering or 0)
    lines = list(annual_komponen_lines(siswa, periode_bulan, periode_tahun))
    h_sen = h_jum = h_all = 0
    period = get_tarif_katering_period(periode_bulan, periode_tahun)

    if siswa.spp_nominal and siswa.spp_nominal > 0:
        lines.append({
            "komponen": "SPP",
            "kategori": "BULANAN",
            "keterangan": _default_keterangan("SPP"),
            "akun_pendapatan": akun_rule("SPP"),
            "nominal": Decimal(siswa.spp_nominal),
        })

    kat_total, h_sen, h_jum, h_all, period = katering_breakdown_for_siswa(
        siswa, periode_bulan, periode_tahun,
    )
    if kat_total > 0:
        lines.append({
            "komponen": "KATERING",
            "kategori": "BULANAN",
            "keterangan": _default_keterangan(
                "KATERING",
                hari_sen_kam=h_sen,
                hari_jumat=h_jum,
                tarif_sen_kam=period.tarif_sen_kam,
                tarif_jumat=period.tarif_jumat,
            ),
            "akun_pendapatan": akun_rule("KATERING"),
            "nominal": kat_total,
        })
    elif tarif_katering > 0:
        hari_katering = KehadiranSiswa.objects.filter(
            siswa=siswa, tanggal__year=periode_tahun, tanggal__month=periode_bulan,
            ikut_katering=True,
        ).count()
        if hari_katering:
            lines.append({
                "komponen": "KATERING",
                "kategori": "BULANAN",
                "keterangan": _default_keterangan(
                    "KATERING", hari_katering=hari_katering, tarif_katering=tarif_katering,
                ),
                "akun_pendapatan": akun_rule("KATERING"),
                "nominal": tarif_katering * hari_katering,
            })
            kat_total = tarif_katering * hari_katering
            h_all = hari_katering

    jemput_regs = list(
        PendaftaranJemputan.objects.filter(siswa=siswa).order_by("-id")
    )
    j_datang = j_pulang = 0
    j_total = Decimal(0)
    j_tarif = Decimal(0)
    if jemput_regs:
        qs = KehadiranSiswa.objects.filter(
            siswa=siswa,
            tanggal__year=periode_tahun,
            tanggal__month=periode_bulan,
        )
        j_datang = qs.filter(jemput_datang=True).count()
        j_pulang = qs.filter(jemput_pulang=True).count()
        trips = j_datang + j_pulang
        if trips:
            j_tarif = jemput_regs[0].harga
            j_total = j_tarif * trips

    if j_total > 0:
        lines.append({
            "komponen": "JEMPUTAN",
            "kategori": "BULANAN",
            "keterangan": _jemput_keterangan(
                datang=j_datang, pulang=j_pulang, tarif=j_tarif,
            ),
            "akun_pendapatan": akun_rule("JEMPUTAN"),
            "nominal": j_total,
        })

    total = sum((line["nominal"] for line in lines), Decimal(0))
    meta = {
        "hari_katering": h_all,
        "hari_katering_sen_kam": h_sen,
        "hari_katering_jumat": h_jum,
        "tarif_sen_kam": str(period.tarif_sen_kam),
        "tarif_jumat": str(period.tarif_jumat),
        "tarif_katering": str(period.tarif_sen_kam),
        "jemput_datang": j_datang,
        "jemput_pulang": j_pulang,
        "tarif_jemput": str(j_tarif),
        "siswa_nama": str(siswa),
        "nis": siswa.nis,
        "kelompok": str(siswa.kelompok) if siswa.kelompok_id else None,
    }
    return lines, total, meta


def preview_tagihan(siswa, periode_bulan, periode_tahun, tarif_katering=Decimal(0)):
    """Preview tagihan — sama logika generate, tanpa simpan."""
    lines, total, meta = build_tagihan_komponen(
        siswa, periode_bulan, periode_tahun, tarif_katering,
    )
    if not lines:
        raise ValueError("Tidak ada komponen tagihan untuk siswa/periode ini.")

    return {
        "siswa": siswa.id,
        "periode_bulan": periode_bulan,
        "periode_tahun": periode_tahun,
        "periode_label": f"{BULAN_NAMA[periode_bulan - 1]} {periode_tahun}",
        "detail": [
            {**line, "nominal": str(line["nominal"])}
            for line in lines
        ],
        "total": str(total),
        "meta": meta,
    }


def generate_tagihan(siswa, periode_bulan, periode_tahun, tarif_katering=Decimal(0)):
    """Rekap otomatis komponen tagihan satu siswa untuk satu periode."""
    from operations.models import Tagihan, TagihanDetail

    if Tagihan.objects.filter(
        siswa=siswa, periode_bulan=periode_bulan, periode_tahun=periode_tahun
    ).exists():
        raise ValueError("Tagihan periode ini sudah ada untuk siswa tersebut.")

    lines, total, _meta = build_tagihan_komponen(
        siswa, periode_bulan, periode_tahun, tarif_katering,
    )
    if not lines:
        raise ValueError("Tidak ada komponen tagihan untuk siswa/periode ini.")

    with transaction.atomic():
        tagihan = Tagihan.objects.create(
            siswa=siswa, periode_bulan=periode_bulan,
            periode_tahun=periode_tahun, total=total, status="BELUM",
        )
        for line in lines:
            TagihanDetail.objects.create(
                tagihan=tagihan,
                komponen=line["komponen"],
                kategori=line["kategori"],
                keterangan=line["keterangan"],
                akun_pendapatan_id=line["akun_pendapatan"],
                nominal=line["nominal"],
            )
    return tagihan


def _siswa_queryset_for_batch(*, jenjang_id=None, kelompok_id=None):
    from operations.models import Siswa

    qs = Siswa.objects.filter(status="aktif").select_related("kelompok__jenjang")
    if kelompok_id:
        return qs.filter(kelompok_id=kelompok_id)
    if jenjang_id:
        return qs.filter(kelompok__jenjang_id=jenjang_id)
    return qs


def preview_batch_tagihan(
    *,
    periode_bulan: int,
    periode_tahun: int,
    tarif_katering=Decimal(0),
    jenjang_id=None,
    kelompok_id=None,
):
    """Preview tagihan untuk banyak siswa (filter jenjang/kelompok)."""
    from operations.models import Tagihan

    previews = []
    skipped = []
    for siswa in _siswa_queryset_for_batch(jenjang_id=jenjang_id, kelompok_id=kelompok_id):
        if Tagihan.objects.filter(
            siswa=siswa,
            periode_bulan=periode_bulan,
            periode_tahun=periode_tahun,
        ).exists():
            skipped.append({"siswa": siswa.id, "nama": siswa.nama, "reason": "sudah ada tagihan"})
            continue
        try:
            previews.append(preview_tagihan(
                siswa, periode_bulan, periode_tahun, tarif_katering,
            ))
        except ValueError as exc:
            skipped.append({"siswa": siswa.id, "nama": siswa.nama, "reason": str(exc)})
    return {"previews": previews, "skipped": skipped, "count": len(previews)}


def generate_batch_tagihan(
    *,
    periode_bulan: int,
    periode_tahun: int,
    tarif_katering=Decimal(0),
    jenjang_id=None,
    kelompok_id=None,
):
    """Generate tagihan batch; return created + skipped."""
    from operations.models import Tagihan

    created = []
    skipped = []
    for siswa in _siswa_queryset_for_batch(jenjang_id=jenjang_id, kelompok_id=kelompok_id):
        if Tagihan.objects.filter(
            siswa=siswa,
            periode_bulan=periode_bulan,
            periode_tahun=periode_tahun,
        ).exists():
            skipped.append({"siswa": siswa.id, "nama": siswa.nama, "reason": "sudah ada tagihan"})
            continue
        try:
            tagihan = generate_tagihan(
                siswa, periode_bulan, periode_tahun, tarif_katering,
            )
            created.append(tagihan.id)
        except ValueError as exc:
            skipped.append({"siswa": siswa.id, "nama": siswa.nama, "reason": str(exc)})
    return {"created_ids": created, "skipped": skipped, "count": len(created)}


def post_pembayaran_tagihan(tagihan, user=None, akun_kas_kode=None):
    """Jurnal DRAFT saat tagihan dibayar (Dr Kas, Cr Pendapatan per komponen)."""
    if tagihan.jurnal_id:
        raise ValueError("Tagihan ini sudah memiliki jurnal.")
    akun_kas_kode = akun_kas_kode or akun_sistem("KAS", "1101")

    detail = list(tagihan.detail.all())
    if not detail:
        raise ValueError("Tagihan tidak memiliki rincian komponen.")

    total_kredit = sum((d.nominal for d in detail), Decimal(0))

    with transaction.atomic():
        with audit_user(user):
            jurnal = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"BL-{tagihan.id}-{tagihan.periode_tahun}{tagihan.periode_bulan:02d}",
                tanggal=date.today(),
                keterangan=f"Pembayaran tagihan {tagihan.siswa} "
                           f"periode {tagihan.periode_bulan}/{tagihan.periode_tahun}",
                tipe_sumber="AUTO_BILLING", status="DRAFT", created_by=user,
            )
            TrJurnalDetail.objects.create(
                jurnal=jurnal, kode_akun_id=akun_kas_kode, debit=total_kredit, kredit=0
            )
            for d in detail:
                TrJurnalDetail.objects.create(
                    jurnal=jurnal, kode_akun=d.akun_pendapatan, debit=0, kredit=d.nominal
                )
            tagihan.jurnal = jurnal
            tagihan.status = "LUNAS"
            tagihan.total = total_kredit
            tagihan.save(update_fields=["jurnal", "status", "total", "updated_at"])
    return jurnal


def _struk_sections(details):
    sections = []
    for kat in ("TAHUNAN", "BULANAN", "LAIN"):
        lines = [d for d in details if d.kategori == kat]
        if not lines:
            continue
        sections.append({
            "kategori": kat,
            "label": KATEGORI_LABELS[kat],
            "lines": [
                {
                    "komponen": d.komponen,
                    "label": d.keterangan or d.get_komponen_display(),
                    "nominal": d.nominal,
                }
                for d in lines
            ],
        })
    return sections


def struk_tagihan(tagihan):
    """Data struk/kwitansi tagihan untuk dicetak frontend."""
    details = list(tagihan.detail.all())
    bulan = BULAN_NAMA[tagihan.periode_bulan - 1]
    return {
        "no_tagihan": tagihan.id,
        "sekolah": "TK Lebah Madu",
        "siswa": str(tagihan.siswa),
        "nis": tagihan.siswa.nis,
        "kelompok": str(tagihan.siswa.kelompok) if tagihan.siswa.kelompok_id else None,
        "periode": f"{bulan} {tagihan.periode_tahun}",
        "periode_bulan": tagihan.periode_bulan,
        "periode_tahun": tagihan.periode_tahun,
        "status": tagihan.status,
        "sections": _struk_sections(details),
        "rincian": [
            {
                "komponen": d.komponen,
                "label": d.keterangan or d.get_komponen_display(),
                "nominal": d.nominal,
            }
            for d in details
        ],
        "total": tagihan.total,
        "no_jurnal": str(tagihan.jurnal_id) if tagihan.jurnal_id else None,
    }
