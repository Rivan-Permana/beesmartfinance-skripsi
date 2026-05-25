"""Service siklus pendapatan: rekap tagihan, pembayaran, struk."""

import uuid
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from accounting.models import TrJurnal, TrJurnalDetail

from .common import akun_rule, audit_user


def generate_tagihan(siswa, periode_bulan, periode_tahun, tarif_katering=Decimal(0)):
    """Rekap otomatis komponen tagihan satu siswa untuk satu periode.

    - SPP      : dari siswa.spp_nominal
    - Katering : jumlah hari ikut katering (absensi) x tarif_katering
    - Jemputan : total harga pendaftaran jemputan aktif (flat/bulan)
    Akun pendapatan tiap komponen diambil dari MsPostingRule.
    """
    from operations.models import KehadiranSiswa, PendaftaranJemputan, Tagihan, TagihanDetail

    if Tagihan.objects.filter(
        siswa=siswa, periode_bulan=periode_bulan, periode_tahun=periode_tahun
    ).exists():
        raise ValueError("Tagihan periode ini sudah ada untuk siswa tersebut.")

    tarif_katering = Decimal(tarif_katering or 0)
    komponen = []

    if siswa.spp_nominal and siswa.spp_nominal > 0:
        komponen.append(("SPP", akun_rule("SPP"), Decimal(siswa.spp_nominal)))

    hari_katering = KehadiranSiswa.objects.filter(
        siswa=siswa, tanggal__year=periode_tahun, tanggal__month=periode_bulan,
        ikut_katering=True,
    ).count()
    if hari_katering and tarif_katering > 0:
        komponen.append(("KATERING", akun_rule("KATERING"),
                         tarif_katering * hari_katering))

    jemput = (
        PendaftaranJemputan.objects.filter(siswa=siswa)
        .aggregate(t=Sum("harga"))["t"] or Decimal(0)
    )
    if jemput > 0:
        komponen.append(("JEMPUTAN", akun_rule("JEMPUTAN"), jemput))

    if not komponen:
        raise ValueError("Tidak ada komponen tagihan untuk siswa/periode ini.")

    total = sum((k[2] for k in komponen), Decimal(0))
    with transaction.atomic():
        tagihan = Tagihan.objects.create(
            siswa=siswa, periode_bulan=periode_bulan,
            periode_tahun=periode_tahun, total=total, status="BELUM",
        )
        for nama, akun_id, nominal in komponen:
            TagihanDetail.objects.create(
                tagihan=tagihan, komponen=nama,
                akun_pendapatan_id=akun_id, nominal=nominal,
            )
    return tagihan


def post_pembayaran_tagihan(tagihan, user=None, akun_kas_kode="1101"):
    """Jurnal DRAFT saat tagihan dibayar (Dr Kas, Cr Pendapatan per komponen)."""
    if tagihan.jurnal_id:
        raise ValueError("Tagihan ini sudah memiliki jurnal.")

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


def struk_tagihan(tagihan):
    """Data struk/kwitansi tagihan untuk dicetak frontend."""
    return {
        "no_tagihan": tagihan.id,
        "siswa": str(tagihan.siswa),
        "nis": tagihan.siswa.nis,
        "periode": f"{tagihan.periode_bulan:02d}/{tagihan.periode_tahun}",
        "status": tagihan.status,
        "rincian": [
            {"komponen": d.komponen, "nominal": d.nominal}
            for d in tagihan.detail.all()
        ],
        "total": tagihan.total,
        "no_jurnal": str(tagihan.jurnal_id) if tagihan.jurnal_id else None,
    }
