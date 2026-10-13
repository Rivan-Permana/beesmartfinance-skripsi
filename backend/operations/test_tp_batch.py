"""Tests template TP + batch tagihan (E10 stories 10.2, 10.5)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APITestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from operations.models import Jenjang, Kelompok, MsPostingRule, Siswa
from operations.services.billing import build_tagihan_komponen, generate_batch_tagihan
from operations.services.tp_templates import ensure_tp_templates

User = get_user_model()


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


def _posting_rules():
    kas = _coa("1101", "KAS", "D")
    pend = _coa("4101", "PENDAPATAN", "K")
    for komp in ("SPP", "KATERING", "JEMPUTAN", "UANG_MASUK", "KEGIATAN", "LAIN"):
        MsPostingRule.objects.create(
            event_code="TAGIHAN", komponen=komp,
            akun_debit=kas, akun_kredit=pend,
        )


class TpTemplateBillingTests(TestCase):
    def setUp(self):
        _posting_rules()
        ensure_tp_templates()
        j = Jenjang.objects.create(kode="TKA", nama="TK A")
        k = Kelompok.objects.create(jenjang=j, nama="TKA Melati")
        self.siswa = Siswa.objects.create(
            nama="RA Baru", kelompok=k, tipe_tp="baru", spp_nominal=Decimal("1300000"),
        )

    def test_annual_komponen_in_july(self):
        lines, total, _meta = build_tagihan_komponen(self.siswa, 7, 2026)
        kodes = {line["komponen"] for line in lines}
        self.assertIn("SPP", kodes)
        self.assertIn("UANG_MASUK", kodes)
        self.assertIn("KEGIATAN", kodes)
        self.assertGreater(total, Decimal("10000000"))

    def test_no_annual_in_non_july(self):
        lines, _total, _meta = build_tagihan_komponen(self.siswa, 6, 2026)
        kodes = {line["komponen"] for line in lines}
        self.assertNotIn("UANG_MASUK", kodes)
        self.assertIn("SPP", kodes)


class BatchTagihanApiTests(APITestCase):
    def setUp(self):
        _posting_rules()
        ensure_tp_templates()
        self.admin = User.objects.create_user("admin_batch", password="x")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        j = Jenjang.objects.create(kode="PG", nama="Playgroup")
        k = Kelompok.objects.create(jenjang=j, nama="PG Merah")
        Siswa.objects.create(
            nama="PG A", kelompok=k, tipe_tp="baru", spp_nominal=Decimal("850000"),
        )
        Siswa.objects.create(
            nama="PG B", kelompok=k, tipe_tp="baru", spp_nominal=Decimal("850000"),
        )
        self.client.force_authenticate(self.admin)

    def test_preview_batch(self):
        r = self.client.post("/api/v1/tagihan/preview-batch/", {
            "periode_bulan": 7,
            "periode_tahun": 2026,
            "kelompok": Kelompok.objects.first().id,
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 2)

    def test_generate_batch(self):
        r = self.client.post("/api/v1/tagihan/generate-batch/", {
            "periode_bulan": 7,
            "periode_tahun": 2026,
            "jenjang": Jenjang.objects.first().id,
        }, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["count"], 2)
