"""Invoice gabungan, data perlu dilengkapi, ukuran seragam, kode pengeluaran. Semua data rekaan."""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from operations.models import Jenjang, Kelompok, KodePengeluaran, Siswa, Tagihan, TagihanDetail
from operations.test_api import _coa


def _user(name, role):
    user = get_user_model().objects.create_user(name)
    user.groups.add(Group.objects.get(name=role))
    return user


class TindakLanjutSheetTests(APITestCase):
    def setUp(self):
        self.tu = _user("tl-tu", "Administration")
        self.finance = _user("tl-finance", "Finance")
        self.guru = _user("tl-guru", "TeacherInCharge")
        _coa("1101", "Kas", "D")
        _coa("4101", "Pendapatan SPP", "K")
        _coa("5901", "Beban uji", "D")
        self.jenjang = Jenjang.objects.create(
            kode="TKX", nama="TK uji", rekening_bank="Bank Uji", rekening_nomor="000111",
            rekening_atas_nama="Sekolah Uji", kontak_nama="Bu Kontak", kontak_wa="081200000000",
        )
        self.kelompok = Kelompok.objects.create(jenjang=self.jenjang, nama="A1")
        self.client.force_authenticate(self.tu)

    def _siswa(self, nama, spp="1000000", kelompok=True, **extra):
        extra.setdefault("kontak_ibu", "081234567890")
        return Siswa.objects.create(
            nama=nama, spp_nominal=Decimal(spp), kelompok=self.kelompok if kelompok else None, **extra,
        )

    def _tagihan(self, siswa, bulan, nominal, **extra):
        tagihan = Tagihan.objects.create(siswa=siswa, periode_bulan=bulan, periode_tahun=2026, total=Decimal(nominal), **extra)
        detail = TagihanDetail.objects.create(tagihan=tagihan, komponen="SPP", akun_pendapatan_id="4101", nominal=Decimal(nominal))
        return tagihan, detail

    def test_perlu_dilengkapi_menandai_masalah_dan_menyembunyikan_dari_guru(self):
        for i in range(3):
            self._siswa(f"Normal {i}")
        kosong = self._siswa("Spp Kosong", "0")
        janggal = self._siswa("Spp Janggal", "300000")
        tanpa = self._siswa("Tanpa Kelompok", kelompok=False)
        hp = self._siswa("Hp Janggal", kontak_ibu="12345")
        nokontak = self._siswa("Tanpa Kontak", kontak_ibu=None)
        self._siswa("Sudah Lulus", "0", status="lulus")

        res = self.client.get("/api/v1/siswa/perlu-dilengkapi/")
        self.assertEqual(res.status_code, 200, res.data)
        kode = {row["id"]: {m["kode"] for m in row["masalah"]} for row in res.data["baris"]}
        self.assertEqual(kode[kosong.pk], {"spp_kosong"})
        self.assertEqual(kode[janggal.pk], {"spp_janggal"})
        self.assertEqual(kode[tanpa.pk], {"tanpa_kelompok"})
        self.assertEqual(kode[hp.pk], {"hp_janggal"})
        self.assertEqual(kode[nokontak.pk], {"kontak_kosong"})
        self.assertEqual(len(res.data["baris"]), 5)  # siswa normal dan lulus tidak ikut
        self.assertEqual(res.data["ringkasan"]["spp_janggal"], 1)

        self.client.force_authenticate(self.guru)
        self.assertEqual(self.client.get("/api/v1/siswa/perlu-dilengkapi/").status_code, 403)

    def test_invoice_gabungan_menjumlah_sisa_semua_tagihan(self):
        siswa = self._siswa("Anak Invoice")
        t1, d1 = self._tagihan(siswa, 9, "1000000")
        self._tagihan(siswa, 10, "1000000")
        lunas, _ = self._tagihan(siswa, 8, "500000")
        self._tagihan(siswa, 7, "700000", perlu_rekonsiliasi=True)
        bayar = lambda tagihan, detail, nominal, bukti: self.client.post(  # noqa: E731
            f"/api/v1/tagihan/{tagihan.pk}/bayar/",
            {"tanggal": "2026-10-01", "no_bukti": bukti, "nominal": nominal, "akun_kas": "1101",
             "request_id": str(uuid.uuid4()), "alokasi": [{"detail": detail.pk, "nominal": nominal}]},
            format="json",
        )
        self.assertEqual(bayar(t1, d1, "400000", "B-1").status_code, 200)
        self.assertEqual(bayar(lunas, lunas.detail.get(), "500000", "B-2").status_code, 200)

        res = self.client.get(f"/api/v1/siswa/{siswa.pk}/invoice-gabungan/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["total"], "1600000.00")
        lines = res.data["sections"][0]["lines"]
        self.assertEqual([(line["periode"], line["nominal"]) for line in lines],
                         [("September 2026", "600000.00"), ("Oktober 2026", "1000000.00")])
        self.assertEqual(len(res.data["perlu_dicocokkan"]), 1)
        self.assertEqual(res.data["rekening"]["nomor"], "000111")
        self.assertEqual(res.data["kontak"]["nama"], "Bu Kontak")
        self.assertEqual(res.data["kontak_ortu"], [{"label": "Ibu", "nomor": "081234567890"}])

        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.get(f"/api/v1/siswa/{siswa.pk}/invoice-gabungan/").status_code, 200)
        self.client.force_authenticate(self.guru)
        self.assertEqual(self.client.get(f"/api/v1/siswa/{siswa.pk}/invoice-gabungan/").status_code, 403)

    def test_invoice_tanpa_rekening_dan_alokasi_tidak_lengkap(self):
        jenjang = Jenjang.objects.create(kode="PGX", nama="PG uji")
        siswa = Siswa.objects.create(nama="Anak Lama", kelompok=Kelompok.objects.create(jenjang=jenjang, nama="P1"))
        tagihan, detail = self._tagihan(siswa, 9, "900000")
        TagihanDetail.objects.create(tagihan=tagihan, komponen="KATERING", akun_pendapatan_id="4101", nominal=Decimal("100000"))
        tagihan.total = Decimal("1000000")
        tagihan.save()
        res = self.client.get(f"/api/v1/siswa/{siswa.pk}/invoice-gabungan/")
        self.assertIsNone(res.data["rekening"])
        self.assertIsNone(res.data["kontak"])
        self.assertEqual(res.data["total"], "1000000.00")

    def test_rekening_jenjang_dan_ukuran_seragam_disimpan_tu(self):
        res = self.client.patch(f"/api/v1/jenjang/{self.jenjang.pk}/", {"rekening_nomor": "999", "catatan_invoice": "Dapat dicicil"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["catatan_invoice"], "Dapat dicicil")
        siswa = self._siswa("Anak Seragam")
        res = self.client.patch(f"/api/v1/siswa/{siswa.pk}/", {"ukuran_seragam_putih": "M", "ukuran_seragam_olga": "L"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        siswa.refresh_from_db()
        self.assertEqual((siswa.ukuran_seragam_putih, siswa.ukuran_seragam_olga), ("M", "L"))
        self.client.force_authenticate(self.guru)
        self.assertEqual(self.client.get(f"/api/v1/siswa/{siswa.pk}/").data["ukuran_seragam_putih"], "M")

    def test_kode_pengeluaran_ditulis_keuangan_dan_dibaca_tu(self):
        self.assertTrue(KodePengeluaran.objects.filter(kode="PLN", unit="UMUM").exists())  # seed migrasi
        payload = {"kode": " zzx ", "unit": "TK", "nama": "Uji", "akun": "5901"}
        self.assertEqual(self.client.post("/api/v1/kode-pengeluaran/", payload, format="json").status_code, 403)
        self.client.force_authenticate(self.finance)
        res = self.client.post("/api/v1/kode-pengeluaran/", payload, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual((res.data["kode"], res.data["akun_nama"]), ("ZZX", "Beban uji"))
        dobel = self.client.post("/api/v1/kode-pengeluaran/", payload, format="json")
        self.assertEqual(dobel.status_code, 400)
        self.assertIn("kode", dobel.data)
        spasi = self.client.post("/api/v1/kode-pengeluaran/", {**payload, "kode": "STR TK"}, format="json")
        self.assertEqual(spasi.status_code, 400)
        self.client.force_authenticate(self.tu)
        daftar = self.client.get("/api/v1/kode-pengeluaran/")
        self.assertEqual(daftar.status_code, 200)
        self.assertIn("ZZX", [row["kode"] for row in daftar.data])
