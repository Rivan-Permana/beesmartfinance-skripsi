"""Tests jemput per-trip billing (E10 story 10.4)."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from operations.models import ArmadaJemputan, KehadiranSiswa, MsPostingRule, PendaftaranJemputan, Siswa
from operations.services.billing import build_tagihan_komponen


def _coa(kode, nama, posisi):
    g, _ = MsGolongan.objects.get_or_create(
        kode_golongan=kode[0], defaults={"nama_golongan": "G" + kode[0]}
    )
    sg, _ = MsSubGolongan.objects.get_or_create(
        kode_sub=kode[:2], defaults={"golongan": g, "nama_sub": "SG"}
    )
    return MsCoa.objects.create(
        kode_akun=kode, sub_golongan=sg, nama_akun=nama, posisi_normal=posisi
    )


class JemputPerTripBillingTests(TestCase):
    def setUp(self):
        kas = _coa("1101", "KAS", "D")
        spp = _coa("4101", "SPP", "K")
        jemput = _coa("4103", "JEMPUT", "K")
        for komponen, akun in (("SPP", spp), ("JEMPUTAN", jemput)):
            MsPostingRule.objects.create(
                event_code="TAGIHAN", komponen=komponen,
                akun_debit=kas, akun_kredit=akun,
            )

    def test_jemput_nominal_from_trips(self):
        siswa = Siswa.objects.create(nama="Anak Jemput", spp_nominal=Decimal(0))
        armada = ArmadaJemputan.objects.create(nama_supir="Pak Ali")
        PendaftaranJemputan.objects.create(
            siswa=siswa, armada=armada, harga=Decimal("18000"),
        )
        KehadiranSiswa.objects.create(
            siswa=siswa, tanggal=date(2026, 6, 3), status="hadir",
            jemput_datang=True, jemput_pulang=False,
        )
        KehadiranSiswa.objects.create(
            siswa=siswa, tanggal=date(2026, 6, 4), status="hadir",
            jemput_datang=True, jemput_pulang=True,
        )

        lines, total, meta = build_tagihan_komponen(siswa, 6, 2026)
        jemput = next(line for line in lines if line["komponen"] == "JEMPUTAN")

        self.assertEqual(jemput["nominal"], Decimal("54000"))
        self.assertEqual(meta["jemput_datang"], 2)
        self.assertEqual(meta["jemput_pulang"], 1)
        self.assertEqual(total, Decimal("54000"))

    def test_no_jemput_line_without_trips(self):
        siswa = Siswa.objects.create(nama="Tanpa Trip", spp_nominal=Decimal("1000000"))
        armada = ArmadaJemputan.objects.create(nama_supir="Om Bob")
        PendaftaranJemputan.objects.create(
            siswa=siswa, armada=armada, harga=Decimal("20000"),
        )

        lines, _total, _meta = build_tagihan_komponen(siswa, 6, 2026)
        komponen = {line["komponen"] for line in lines}

        self.assertNotIn("JEMPUTAN", komponen)
