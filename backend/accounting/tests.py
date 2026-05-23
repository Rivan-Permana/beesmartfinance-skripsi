"""Test integritas core accounting.

Membuktikan: DB test dibangun dari migrasi (termasuk RunSQL skema raw),
dan aturan akuntansi yang ditegakkan trigger DB tembus lewat Django ORM.
"""

import uuid
from datetime import date
from decimal import Decimal

from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from accounting.models import (
    AuditLog,
    MsCoa,
    MsGolongan,
    MsSubGolongan,
    TrAnggaran,
    TrJurnal,
    TrJurnalDetail,
)


def _saldo(kode_akun):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT saldo_akhir FROM v_neraca_saldo WHERE kode_akun = %s", [kode_akun]
        )
        row = cur.fetchone()
    return row[0] if row else None


class CoreAccountingTests(TestCase):
    def setUp(self):
        g_beban = MsGolongan.objects.create(kode_golongan="5", nama_golongan="BEBAN")
        sg_beban = MsSubGolongan.objects.create(
            golongan=g_beban, kode_sub="51", nama_sub="BEBAN USAHA"
        )
        MsCoa.objects.create(
            kode_akun="5101", sub_golongan=sg_beban,
            nama_akun="BEBAN GAJI", posisi_normal="D",
        )
        g_aktiva = MsGolongan.objects.create(kode_golongan="1", nama_golongan="AKTIVA")
        sg_aktiva = MsSubGolongan.objects.create(
            golongan=g_aktiva, kode_sub="11", nama_sub="AKTIVA LANCAR"
        )
        MsCoa.objects.create(
            kode_akun="1101", sub_golongan=sg_aktiva,
            nama_akun="KAS", posisi_normal="D",
        )

    def _draft(self, no_bukti, kode_akun, debit):
        jurnal = TrJurnal.objects.create(
            id=uuid.uuid4(), no_bukti=no_bukti,
            tanggal=date(2026, 2, 1), status="DRAFT",
        )
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kode_akun, debit=debit, kredit=0
        )
        return jurnal

    def test_posting_mempengaruhi_saldo(self):
        jurnal = self._draft("T1", "5101", Decimal("500000"))
        jurnal.status = "POSTED"
        jurnal.save()
        self.assertEqual(_saldo("5101"), Decimal("500000"))

    def test_draft_tidak_dihitung_di_saldo(self):
        self._draft("T2", "5101", Decimal("777"))
        self.assertEqual(_saldo("5101"), Decimal("0"))

    def test_jurnal_posted_immutable(self):
        jurnal = self._draft("T3", "5101", Decimal("100"))
        jurnal.status = "POSTED"
        jurnal.save()
        detail = jurnal.detail.first()
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                detail.debit = Decimal("999")
                detail.save()

    def test_anggaran_hard_block(self):
        TrAnggaran.objects.create(
            kode_akun_id="5101", tahun_anggaran=2026,
            nominal_anggaran=Decimal("1000000"),
        )
        jurnal = self._draft("T4", "5101", Decimal("1500000"))  # > pagu
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                jurnal.status = "POSTED"
                jurnal.save()

    def test_audit_log_terisi(self):
        sebelum = AuditLog.objects.count()
        self._draft("T5", "5101", Decimal("1"))
        self.assertGreater(AuditLog.objects.count(), sebelum)
