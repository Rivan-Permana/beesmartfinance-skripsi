"""Service registrasi calon siswa: pembayaran sit-in & finalisasi admission."""

from decimal import Decimal

from django.db import transaction

from .common import akun_rule, akun_sistem, audit_user, buat_jurnal


def post_bayar_sitin(pendaftaran, user=None, akun_kas=None):
    """Pembayaran sit-in/trial -> auto-journal pendapatan."""
    if pendaftaran.jurnal_sitin_id:
        raise ValueError("Pembayaran sit-in sudah dijurnal.")
    if pendaftaran.biaya_sitin <= 0:
        raise ValueError("Biaya sit-in nol.")
    akun_kas = akun_kas or akun_sistem("KAS", "1101")
    akun_pendapatan = akun_rule("SITIN", event_code="REGISTRASI")
    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
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


def finalisasi_pendaftaran(pendaftaran, user=None, akun_kas=None, spp_nominal=Decimal(0)):
    """Calon mendaftar resmi: jurnal admission + buat record Siswa."""
    from operations.models import Siswa

    if pendaftaran.status == "REGISTERED":
        raise ValueError("Pendaftaran sudah difinalisasi.")
    if pendaftaran.biaya_pendaftaran <= 0:
        raise ValueError("Biaya pendaftaran nol.")
    akun_kas = akun_kas or akun_sistem("KAS", "1101")
    akun_pendapatan = akun_rule("PENDAFTARAN", event_code="REGISTRASI")

    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
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
