"""Service registrasi calon siswa: pembayaran sit-in & finalisasi admission."""

from decimal import Decimal

from django.db import transaction

from accounting.models import MsCoa, TrJurnal
from operations.models import PendaftaranSiswa

from .common import akun_rule, audit_user, buat_jurnal


KOMPONEN = {
    "SITIN": ("biaya_sitin", "jurnal_sitin", "SITIN"),
    "FORMULIR": ("biaya_formulir", "jurnal_pendaftaran", "PENDAFTARAN"),
}


def post_pembayaran_pendaftaran(pendaftaran, *, komponen, tanggal, no_bukti, nominal, akun_kas, user=None):
    """Terima komponen penuh yang dipilih; finalisasi administrasi dikerjakan terpisah."""
    with transaction.atomic(), audit_user(user):
        pendaftaran = PendaftaranSiswa.all_objects.select_for_update().get(pk=pendaftaran.pk)
        if pendaftaran.is_deleted or pendaftaran.status == "BATAL":
            raise ValueError("Pendaftaran sudah dibatalkan.")
        if pendaftaran.perlu_rekonsiliasi:
            raise ValueError("Rincian biaya/pembayaran lama perlu dicocokkan sebelum menerima pembayaran baru.")
        if not komponen or len(set(komponen)) != len(komponen) or any(k not in KOMPONEN for k in komponen):
            raise ValueError("Pilih komponen pembayaran yang berbeda dan valid.")
        total = sum((getattr(pendaftaran, KOMPONEN[k][0]) for k in komponen), Decimal(0))
        if not nominal.is_finite() or nominal <= 0 or total != nominal:
            raise ValueError("Nominal harus sama dengan jumlah komponen yang dipilih dan lebih dari nol.")
        if any(getattr(pendaftaran, KOMPONEN[k][0]) <= 0 for k in komponen):
            raise ValueError("Komponen bernilai nol tidak perlu dibayar.")
        paid = [k for k in komponen if pendaftaran.pembayaran_aktif(k)]
        if paid:
            jurnal = getattr(pendaftaran, KOMPONEN[komponen[0]][1])
            if (len(paid) == len(komponen) and jurnal and jurnal.no_bukti == no_bukti
                    and jurnal.tanggal == tanggal
                    and all(getattr(pendaftaran, KOMPONEN[k][1] + "_id") == jurnal.pk for k in komponen)
                    and list(jurnal.detail.filter(debit__gt=0).values_list("kode_akun_id", "debit")) == [(akun_kas, nominal)]
                    and sum(jurnal.detail.values_list("debit", flat=True)) == nominal):
                return jurnal
            raise ValueError("Komponen sudah memiliki penerimaan. Pilih hanya komponen yang belum dibayar.")
        if not MsCoa.objects.filter(pk=akun_kas, is_active=True, kode_akun__in=["111", "112", "1011", "1101", "1102"]).exists():
            raise ValueError("Pilih akun kas/bank aktif yang dipakai sekolah.")
        baris = [(akun_kas, nominal, Decimal(0))]
        for k in komponen:
            akun_pendapatan = akun_rule(KOMPONEN[k][2], event_code="REGISTRASI")
            baris.append((akun_pendapatan, Decimal(0), getattr(pendaftaran, KOMPONEN[k][0])))
        jurnal = buat_jurnal(
            no_bukti=no_bukti, tanggal=tanggal,
            keterangan=f"Penerimaan pendaftaran {pendaftaran.nama_calon} ({', '.join(komponen)})",
            tipe="AUTO_SITIN" if komponen == ["SITIN"] else "AUTO_PENDAFTARAN", baris=baris, user=user,
        )
        fields = ["updated_at"]
        for k in komponen:
            field = KOMPONEN[k][1]
            setattr(pendaftaran, field, jurnal)
            fields.append(field)
        pendaftaran.save(update_fields=fields)
        return jurnal


def post_bayar_sitin(pendaftaran, **kwargs):
    return post_pembayaran_pendaftaran(pendaftaran, komponen=["SITIN"], **kwargs)


def jurnal_pendaftaran_perlu_rekonsiliasi(jurnal):
    if jurnal.status == "VOID" or list(jurnal.reversals.all()):
        return False
    records = {p.pk: p for p in [*jurnal.pendaftaran_sitin.all(), *jurnal.pendaftaran_admission.all()]}
    if len(records) != 1:
        return True
    pendaftaran = next(iter(records.values()))
    if pendaftaran.is_deleted or pendaftaran.perlu_rekonsiliasi:
        return True
    expected = sum((getattr(pendaftaran, fee) for fee, field, _ in KOMPONEN.values()
                    if getattr(pendaftaran, field + "_id") == jurnal.pk), Decimal(0))
    return expected <= 0 or sum((d.debit for d in jurnal.detail.all()), Decimal(0)) != expected


def batalkan_penerimaan_pendaftaran(jurnal, user, alasan):
    with transaction.atomic(), audit_user(user):
        jurnal = TrJurnal.objects.select_for_update().get(pk=jurnal.pk)
        if jurnal.status not in {"DRAFT", "PENDING"} or jurnal_pendaftaran_perlu_rekonsiliasi(jurnal):
            raise ValueError("Hanya penerimaan pendaftaran terverifikasi yang belum POSTED dapat dibatalkan Finance.")
        for p in PendaftaranSiswa.all_objects.select_for_update().filter(
            pk__in={p.pk for p in [*jurnal.pendaftaran_sitin.all(), *jurnal.pendaftaran_admission.all()]}
        ):
            p.save(update_fields=["updated_at"])
        jurnal.status = "VOID"
        jurnal.keterangan = f"{jurnal.keterangan or ''}\nDibatalkan: {alasan}"
        jurnal.save(update_fields=["status", "keterangan"])
        return jurnal


def finalisasi_pendaftaran(pendaftaran, user=None, *, spp_nominal):
    """Finalisasi status calon menjadi siswa tanpa menciptakan penerimaan uang."""
    from operations.models import Siswa

    if not spp_nominal.is_finite() or spp_nominal < 0:
        raise ValueError("Nominal SPP harus berupa angka nonnegatif.")
    with transaction.atomic(), audit_user(user):
        pendaftaran = PendaftaranSiswa.all_objects.select_for_update().get(pk=pendaftaran.pk)
        if pendaftaran.is_deleted or pendaftaran.status == "BATAL":
            raise ValueError("Pendaftaran sudah dibatalkan.")
        if pendaftaran.status == "REGISTERED":
            if not pendaftaran.siswa_id or pendaftaran.siswa.spp_nominal != spp_nominal:
                raise ValueError("Finalisasi sebelumnya berbeda. Ubah SPP melalui data siswa.")
            return pendaftaran
        if pendaftaran.siswa_id:
            raise ValueError("Pendaftaran sudah terhubung ke siswa; periksa data sebelum finalisasi.")
        pendaftaran.siswa = Siswa.objects.create(nama=pendaftaran.nama_calon, spp_nominal=spp_nominal)
        pendaftaran.status = "REGISTERED"
        pendaftaran.save(update_fields=["siswa", "status", "updated_at"])
    return pendaftaran
