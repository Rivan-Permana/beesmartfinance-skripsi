"""Biaya masuk siswa: isian manual + diskon -> satu tagihan jenis BIAYA_MASUK."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .common import audit_user

# Urutan juga menjadi urutan pemotongan diskon.
KOMPONEN_BIAYA_MASUK = [
    ("UANG_MASUK", "uang_masuk", "Uang Masuk"),
    ("PENGEMBANGAN", "uang_pengembangan", "Uang Pengembangan"),
    ("KEGIATAN", "uang_kegiatan", "Uang Kegiatan"),
    ("SERAGAM", "uang_seragam", "Uang Seragam"),
]


def _rp(nominal):
    return f"Rp {int(nominal):,}".replace(",", ".")


def periode_index(bulan, tahun):
    return tahun * 12 + bulan


def default_biaya_masuk(kelompok, tipe_tp="baru"):
    """Nominal daftar harga untuk prefill form (None bila tidak ada)."""
    from operations.models import KomponenBiayaTemplate

    kode_jenjang = kelompok.jenjang.kode if kelompok else None
    jenjang = "PG" if kode_jenjang == "PG" else "RA" if kode_jenjang in ("TKA", "TKB") else None
    hasil = {field: None for _kode, field, _label in KOMPONEN_BIAYA_MASUK}
    if not jenjang:
        return hasil
    templates = KomponenBiayaTemplate.objects.filter(
        aktif=True, jenjang=jenjang, tahun_ke=2 if tipe_tp == "lama" else 1,
        tipe_siswa__in=[tipe_tp, "all"],
    )
    by_kode = {t.kode: t.nominal for t in templates}
    for kode, field, _label in KOMPONEN_BIAYA_MASUK:
        hasil[field] = by_kode.get(kode)
    return hasil


def rincian_biaya_masuk(siswa):
    """Baris netto setelah diskon, berurutan Uang Masuk -> Pengembangan -> Kegiatan -> Seragam."""
    sisa_diskon = Decimal(siswa.diskon_nominal or 0)
    if sisa_diskon < 0:
        raise ValueError("Nominal diskon tidak boleh negatif.")
    label_diskon = ", ".join(siswa.diskon_kategori or []) or "manual"
    lines = []
    for kode, field, label in KOMPONEN_BIAYA_MASUK:
        bruto = Decimal(getattr(siswa, field) or 0)
        if bruto < 0:
            raise ValueError(f"{label} tidak boleh negatif.")
        if bruto == 0:
            continue
        potong = min(bruto, sisa_diskon)
        sisa_diskon -= potong
        keterangan = label if not potong else f"{label} (diskon {label_diskon} {_rp(potong)} dari {_rp(bruto)})"
        lines.append({"komponen": kode, "keterangan": keterangan, "nominal": bruto - potong})
    if sisa_diskon > 0:
        raise ValueError("Diskon melebihi total biaya masuk.")
    return [line for line in lines if line["nominal"] > 0]


def _sudah_ditagih_bulanan(siswa, kode, bulan, tahun):
    """Komponen sudah ada di tagihan bulanan dalam 12 bulan terakhir (mis. tagihan Juli dari daftar harga)."""
    from operations.models import TagihanDetail

    target = periode_index(bulan, tahun)
    for b, t in TagihanDetail.objects.filter(
        tagihan__siswa=siswa, tagihan__is_deleted=False, tagihan__jenis="BULANAN",
        komponen=kode, nominal__gt=0,
    ).values_list("tagihan__periode_bulan", "tagihan__periode_tahun"):
        if target - 11 <= periode_index(b, t) <= target:
            return f"{b}/{t}"
    return None


def sinkron_tagihan_biaya_masuk(siswa, user=None, today=None):
    """Buat/perbarui tagihan biaya masuk dari isian siswa. Komponen yang sudah dibayar dikunci."""
    from operations.models import Tagihan, TagihanDetail
    from operations.services.billing import perbarui_status_tagihan
    from operations.services.tp_templates import _akun_for_komponen

    today = today or timezone.localdate()
    with transaction.atomic(), audit_user(user):
        tagihan = (
            Tagihan.objects.select_for_update()
            .filter(siswa=siswa, jenis="BIAYA_MASUK").order_by("-pk").first()
        )
        lines = rincian_biaya_masuk(siswa)
        bulan, tahun = (tagihan.periode_bulan, tagihan.periode_tahun) if tagihan else (today.month, today.year)
        labels = {kode: label for kode, _f, label in KOMPONEN_BIAYA_MASUK}
        for line in lines:
            ditagih = _sudah_ditagih_bulanan(siswa, line["komponen"], bulan, tahun)
            if ditagih:
                raise ValueError(f"{labels[line['komponen']]} sudah ditagih di tagihan {ditagih}. Kosongkan isian ini.")
        if tagihan is None and not lines:
            return None
        if tagihan is None:
            tagihan = Tagihan.objects.create(
                siswa=siswa, periode_bulan=bulan, periode_tahun=tahun,
                jenis="BIAYA_MASUK", total=0, status="BELUM",
            )
        if tagihan.perlu_rekonsiliasi:
            raise ValueError("Tagihan biaya masuk perlu direkonsiliasi sebelum diubah.")

        baru = {line["komponen"]: line for line in lines}
        for detail in tagihan.detail.prefetch_related("alokasi__pembayaran"):
            line = baru.pop(detail.komponen, None)
            terbayar = detail.total_terbayar
            if terbayar > 0 and (line is None or line["nominal"] != detail.nominal):
                raise ValueError(f"{labels.get(detail.komponen, detail.komponen)} sudah ada penerimaan; nominalnya tidak bisa diubah.")
            if line is None:
                if detail.alokasi.exists():
                    raise ValueError(f"{labels.get(detail.komponen, detail.komponen)} punya riwayat penerimaan; tidak bisa dihapus.")
                detail.delete()
                continue
            detail.nominal, detail.keterangan = line["nominal"], line["keterangan"]
            detail.save(update_fields=["nominal", "keterangan"])
        for line in baru.values():
            TagihanDetail.objects.create(
                tagihan=tagihan, komponen=line["komponen"], kategori="TAHUNAN",
                keterangan=line["keterangan"], akun_pendapatan_id=_akun_for_komponen(line["komponen"]),
                nominal=line["nominal"],
            )

        if not tagihan.detail.exists() and not tagihan.pembayaran.exists():
            tagihan.delete()
            return None
        tagihan.total = sum((d.nominal for d in tagihan.detail.all()), Decimal(0))
        tagihan.save(update_fields=["total", "updated_at"])
        perbarui_status_tagihan(tagihan)
        return tagihan
