"""Service layer: auto-posting siklus operasional -> core accounting.

Aturan akuntansi (balance, immutability, anggaran) tetap dijaga trigger DB;
service ini menyusun jurnal yang benar lalu menyerahkan ke core sebagai DRAFT
(menunggu approval Principal sesuai alur maker-checker).
"""

import uuid
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from accounting.models import TrJurnal, TrJurnalDetail
from accounting.utils import audit_user


def _akun_rule(komponen):
    """Ambil akun pendapatan utk komponen tagihan dari MsPostingRule."""
    from .models import MsPostingRule

    rule = MsPostingRule.objects.filter(komponen=komponen, aktif=True).first()
    if not rule:
        raise ValueError(f"MsPostingRule untuk komponen {komponen} belum diset.")
    return rule.akun_kredit_id


def generate_tagihan(siswa, periode_bulan, periode_tahun, tarif_katering=Decimal(0)):
    """Rekap otomatis komponen tagihan satu siswa untuk satu periode.

    - SPP      : dari siswa.spp_nominal
    - Katering : jumlah hari ikut katering (absensi) x tarif_katering
    - Jemputan : total harga pendaftaran jemputan aktif (flat/bulan)
    Akun pendapatan tiap komponen diambil dari MsPostingRule.
    """
    from .models import (
        KehadiranSiswa,
        PendaftaranJemputan,
        Tagihan,
        TagihanDetail,
    )

    if Tagihan.objects.filter(
        siswa=siswa, periode_bulan=periode_bulan, periode_tahun=periode_tahun
    ).exists():
        raise ValueError("Tagihan periode ini sudah ada untuk siswa tersebut.")

    tarif_katering = Decimal(tarif_katering or 0)
    komponen = []

    if siswa.spp_nominal and siswa.spp_nominal > 0:
        komponen.append(("SPP", _akun_rule("SPP"), Decimal(siswa.spp_nominal)))

    hari_katering = KehadiranSiswa.objects.filter(
        siswa=siswa, tanggal__year=periode_tahun, tanggal__month=periode_bulan,
        ikut_katering=True,
    ).count()
    if hari_katering and tarif_katering > 0:
        komponen.append(("KATERING", _akun_rule("KATERING"),
                         tarif_katering * hari_katering))

    jemput = (
        PendaftaranJemputan.objects.filter(siswa=siswa)
        .aggregate(t=Sum("harga"))["t"] or Decimal(0)
    )
    if jemput > 0:
        komponen.append(("JEMPUTAN", _akun_rule("JEMPUTAN"), jemput))

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


def post_realisasi_kegiatan(kegiatan, tanggal, deskripsi, nominal, user=None,
                            akun_kas="1101"):
    """Realisasi (pengeluaran) kegiatan -> auto-journal beban.

    Cek pagu kegiatan di service (selain hard-block anggaran akun di trigger DB).
    """
    from .models import RealisasiKegiatan

    nominal = Decimal(str(nominal))
    if nominal <= 0:
        raise ValueError("Nominal realisasi harus > 0.")
    if kegiatan.realisasi + nominal > kegiatan.pagu:
        raise ValueError(
            f"Melebihi pagu kegiatan (pagu {kegiatan.pagu}, "
            f"terpakai {kegiatan.realisasi})."
        )

    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"KG-{kegiatan.id}-{RealisasiKegiatan.objects.filter(kegiatan=kegiatan).count() + 1}",
                tanggal=tanggal,
                keterangan=f"Realisasi {kegiatan.nama}: {deskripsi}",
                tipe="AUTO_KEGIATAN",
                baris=[
                    (kegiatan.akun_beban_id, nominal, Decimal(0)),
                    (akun_kas, Decimal(0), nominal),
                ],
                user=user,
            )
            realisasi = RealisasiKegiatan.objects.create(
                kegiatan=kegiatan, tanggal=tanggal, deskripsi=deskripsi,
                nominal=nominal, jurnal=jurnal,
            )
    return realisasi


def post_bayar_sitin(pendaftaran, user=None, akun_kas="1101"):
    """Pembayaran sit-in/trial -> auto-journal pendapatan."""
    if pendaftaran.jurnal_sitin_id:
        raise ValueError("Pembayaran sit-in sudah dijurnal.")
    if pendaftaran.biaya_sitin <= 0:
        raise ValueError("Biaya sit-in nol.")
    akun_pendapatan = _akun_rule("SITIN")
    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"SIT-{pendaftaran.id}",
                tanggal=pendaftaran.tanggal_daftar,
                keterangan=f"Pembayaran sit-in {pendaftaran.nama_calon}",
                tipe="AUTO_SITIN",
                baris=[
                    (akun_kas, pendaftaran.biaya_sitin, Decimal(0)),
                    (akun_pendapatan, Decimal(0), pendaftaran.biaya_sitin),
                ],
                user=user,
            )
            pendaftaran.jurnal_sitin = jurnal
            pendaftaran.save(update_fields=["jurnal_sitin", "updated_at"])
    return jurnal


def finalisasi_pendaftaran(pendaftaran, user=None, akun_kas="1101", spp_nominal=Decimal(0)):
    """Calon mendaftar resmi: jurnal admission + buat record Siswa."""
    from .models import Siswa

    if pendaftaran.status == "REGISTERED":
        raise ValueError("Pendaftaran sudah difinalisasi.")
    if pendaftaran.biaya_pendaftaran <= 0:
        raise ValueError("Biaya pendaftaran nol.")
    akun_pendapatan = _akun_rule("PENDAFTARAN")

    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"REG-{pendaftaran.id}",
                tanggal=pendaftaran.tanggal_daftar,
                keterangan=f"Biaya pendaftaran {pendaftaran.nama_calon}",
                tipe="AUTO_PENDAFTARAN",
                baris=[
                    (akun_kas, pendaftaran.biaya_pendaftaran, Decimal(0)),
                    (akun_pendapatan, Decimal(0), pendaftaran.biaya_pendaftaran),
                ],
                user=user,
            )
            siswa = Siswa.objects.create(
                nama=pendaftaran.nama_calon, spp_nominal=spp_nominal or Decimal(0),
            )
            pendaftaran.siswa = siswa
            pendaftaran.status = "REGISTERED"
            pendaftaran.jurnal_pendaftaran = jurnal
            pendaftaran.save(update_fields=[
                "siswa", "status", "jurnal_pendaftaran", "updated_at"
            ])
    return pendaftaran


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


def post_pembayaran_tagihan(tagihan, user=None, akun_kas_kode="1101"):
    """Buat jurnal DRAFT saat tagihan dibayar lunas (siklus pendapatan).

    Debit  : Kas/Bank (akun_kas_kode)        sebesar total tagihan
    Kredit : akun pendapatan tiap komponen   sesuai TagihanDetail
    """
    if tagihan.jurnal_id:
        raise ValueError("Tagihan ini sudah memiliki jurnal.")

    detail = list(tagihan.detail.all())
    if not detail:
        raise ValueError("Tagihan tidak memiliki rincian komponen.")

    total_kredit = sum((d.nominal for d in detail), start=tagihan.total.__class__(0))

    with transaction.atomic():
        with audit_user(user):
            jurnal = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"BL-{tagihan.id}-{tagihan.periode_tahun}{tagihan.periode_bulan:02d}",
                tanggal=date.today(),
                keterangan=f"Pembayaran tagihan {tagihan.siswa} "
                           f"periode {tagihan.periode_bulan}/{tagihan.periode_tahun}",
                tipe_sumber="AUTO_BILLING",
                status="DRAFT",
                created_by=user,
            )
            TrJurnalDetail.objects.create(
                jurnal=jurnal, kode_akun_id=akun_kas_kode,
                debit=total_kredit, kredit=0,
            )
            for d in detail:
                TrJurnalDetail.objects.create(
                    jurnal=jurnal, kode_akun=d.akun_pendapatan,
                    debit=0, kredit=d.nominal,
                )

            tagihan.jurnal = jurnal
            tagihan.status = "LUNAS"
            tagihan.total = total_kredit
            tagihan.save(update_fields=["jurnal", "status", "total", "updated_at"])

    return jurnal


def _buat_jurnal(no_bukti, tanggal, keterangan, tipe, baris, user):
    """Helper: buat 1 jurnal DRAFT dari daftar baris (kode_akun, debit, kredit).

    Memvalidasi keseimbangan sebelum menyentuh DB.
    """
    total_debit = sum((b[1] for b in baris), start=Decimal(0))
    total_kredit = sum((b[2] for b in baris), start=Decimal(0))
    if total_debit != total_kredit:
        raise ValueError(f"Jurnal tidak seimbang: D={total_debit} K={total_kredit}")

    jurnal = TrJurnal.objects.create(
        id=uuid.uuid4(), no_bukti=no_bukti, tanggal=tanggal,
        keterangan=keterangan, tipe_sumber=tipe, status="DRAFT", created_by=user,
    )
    for kode_akun, debit, kredit in baris:
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kode_akun, debit=debit, kredit=kredit
        )
    return jurnal


def post_pencairan_kasbon(pinjaman, user=None, akun_piutang="1103", akun_kas="1101"):
    """Pencairan kasbon pegawai (Dr Piutang Karyawan, Cr Kas)."""
    if pinjaman.jurnal_id:
        raise ValueError("Pinjaman ini sudah dijurnal.")
    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"KB-{pinjaman.id}",
                tanggal=pinjaman.tanggal_pinjaman,
                keterangan=f"Pencairan kasbon {pinjaman.pegawai}",
                tipe="AUTO_KASBON",
                baris=[
                    (akun_piutang, pinjaman.jumlah_pinjaman, Decimal(0)),
                    (akun_kas, Decimal(0), pinjaman.jumlah_pinjaman),
                ],
                user=user,
            )
            pinjaman.jurnal = jurnal
            pinjaman.save(update_fields=["jurnal", "updated_at"])
    return jurnal


def post_gaji(gaji, user=None, akun_beban="5201", akun_kas="1101",
              akun_piutang="1103", akun_utang_asuransi="2101"):
    """Payroll (siklus pengeluaran).

    Dr Beban Gaji (bruto)
    Cr Kas (netto), Cr Piutang Karyawan (potongan pinjaman),
    Cr Utang Asuransi (potongan asuransi)
    """
    if gaji.jurnal_id:
        raise ValueError("Gaji periode ini sudah dijurnal.")
    from datetime import date

    baris = [(akun_beban, gaji.total_bruto, Decimal(0)),
             (akun_kas, Decimal(0), gaji.total_netto)]
    if gaji.potongan_pinjaman:
        baris.append((akun_piutang, Decimal(0), gaji.potongan_pinjaman))
    if gaji.potongan_asuransi:
        baris.append((akun_utang_asuransi, Decimal(0), gaji.potongan_asuransi))

    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"GJ-{gaji.id}-{gaji.periode_tahun}{gaji.periode_bulan:02d}",
                tanggal=date(gaji.periode_tahun, gaji.periode_bulan, 28),
                keterangan=f"Gaji {gaji.pegawai} {gaji.periode_bulan}/{gaji.periode_tahun}",
                tipe="AUTO_PAYROLL", baris=baris, user=user,
            )
            gaji.jurnal = jurnal
            gaji.save(update_fields=["jurnal", "updated_at"])
    return jurnal


def post_penyusutan(asset, user=None, tanggal=None):
    """Penyusutan periodik (Dr Beban Depresiasi, Cr Akumulasi Penyusutan)."""
    from datetime import date

    nominal = asset.penyusutan_per_bulan
    if nominal <= 0:
        raise ValueError("Nominal penyusutan nol.")
    tanggal = tanggal or date.today()
    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"DP-{asset.id}-{tanggal:%Y%m}",
                tanggal=tanggal,
                keterangan=f"Penyusutan {asset.nama} {tanggal:%m/%Y}",
                tipe="AUTO_DEPRESIASI",
                baris=[
                    (asset.akun_beban_depr_id, nominal, Decimal(0)),
                    (asset.akun_akumulasi_id, Decimal(0), nominal),
                ],
                user=user,
            )
            asset.akumulasi_penyusutan = asset.akumulasi_penyusutan + nominal
            asset.save(update_fields=["akumulasi_penyusutan", "updated_at"])
    return jurnal
