"""Persiapan cut-over Januari: Komite/Portofolio per siswa, penerimaan saldo awal, impor biaya masuk."""

import csv
import io
import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from accounting.models import TrJurnal
from operations.models import Jenjang, Kelompok, MsPostingRule, PembayaranTagihan, Siswa, Tagihan
from operations.services.billing import build_tagihan_komponen, catat_saldo_awal_tagihan
from operations.services.tp_templates import ensure_tp_templates
from operations.test_tp_batch import _coa

JUDUL = ["", "", "Nama", "PUTIH", "Jenis", "KELAS", "STATUS", "STATUS", "JML", "UANG MASUK", "PORTOFOLIO",
         "KEGIATAN", "PENGEMBANGAN", "KOMITE", "SERAGAM", "JML sblm", "JML stlh", "CICILAN", "", "", "", "", "Juli"]
SUB = ["", "", "", "", "Kelamin", "", "", "DISKON", "DISKON", "", "PG", "", "", "", "", "DISKON", "DISKON",
       "TGL", "CIL 1", "TGL", "CIL 2", "LUNAS/BLM?", "SPP"]


def _baris(no, nama, kelas, kategori, diskon, komponen, cicilan, netto=None, lunas=None):
    um, porto, keg, peng, kom, srg = komponen
    bruto = sum(v or 0 for v in komponen)
    netto = bruto - diskon if netto is None else netto
    lunas = sum(cicilan) if lunas is None else lunas
    rp = lambda v: f"{v:,}".replace(",", ".") if v else ""  # noqa: E731
    cil = (list(cicilan) + [0, 0])[:2]
    return ["", str(no), nama, "S", "P", kelas, "BARU", kategori, f"-{rp(diskon)}" if diskon else "0",
            rp(um), rp(porto), rp(keg), rp(peng), rp(kom), rp(srg), rp(bruto), rp(netto),
            "1-Jul", rp(cil[0]), "2-Agu", rp(cil[1]), rp(lunas), "1.000.000"]


class CutoverBaseTest(APITestCase):
    def setUp(self):
        kas = _coa("1101", "KAS", "D")
        for kode, nama in (("411", "SPP"), ("412", "Uang Masuk"), ("413", "Pengembangan"), ("414", "Komite"), ("417", "Lain")):
            _coa(kode, nama, "K")
        for komp, akun in (("SPP", "411"), ("UANG_MASUK", "412"), ("PENGEMBANGAN", "413"), ("KEGIATAN", "417"),
                           ("SERAGAM", "417"), ("KOMITE", "414"), ("PORTOFOLIO", "417"), ("LAIN", "417")):
            MsPostingRule.objects.create(event_code="TAGIHAN", komponen=komp, akun_debit=kas, akun_kredit_id=akun)
        ensure_tp_templates()
        self.tka = Kelompok.objects.create(nama="TKA Melati", jenjang=Jenjang.objects.create(kode="TKA", nama="TK A"))
        self.pg = Kelompok.objects.create(nama="PG Lebah", jenjang=Jenjang.objects.create(kode="PG", nama="PG"))
        self.users = {}
        for role in ("Administration", "Finance", "SchoolPrincipal"):
            user = get_user_model().objects.create_user(f"co-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.users[role] = user
        self.client.force_authenticate(self.users["Administration"])


class KomitePerSiswaTests(CutoverBaseTest):
    def test_komite_per_siswa_masuk_biaya_masuk_dan_juli_tidak_menagih_ulang(self):
        res = self.client.post("/api/v1/siswa/", {
            "nama": "Pindahan", "kelompok": self.tka.pk, "spp_nominal": "500000", "status": "aktif",
            "uang_kegiatan": "2000000", "uang_komite": "400000", "diskon_kategori": ["PINDAHAN"], "diskon_nominal": "0",
        }, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["uang_komite"], "400000.00")
        tagihan = Tagihan.objects.get(siswa_id=res.data["id"], jenis="BIAYA_MASUK")
        rincian = {d.komponen: d for d in tagihan.detail.all()}
        self.assertEqual(rincian["KOMITE"].nominal, Decimal("400000"))
        self.assertEqual(rincian["KOMITE"].akun_pendapatan_id, "414")
        siswa = Siswa.objects.get(pk=res.data["id"])
        tahun_juli = tagihan.periode_tahun if tagihan.periode_bulan <= 7 else tagihan.periode_tahun + 1
        lines, _total, _meta = build_tagihan_komponen(siswa, 7, tahun_juli)
        self.assertNotIn("KOMITE", {line["komponen"] for line in lines})

    def test_tanpa_isian_komite_tagihan_juli_tetap_dari_daftar_harga(self):
        siswa = Siswa.objects.create(nama="Biasa", kelompok=self.tka, spp_nominal=500000, status="aktif")
        lines, _total, _meta = build_tagihan_komponen(siswa, 7, 2027)
        self.assertIn("KOMITE", {line["komponen"] for line in lines})

    def test_daftar_harga_tidak_mengisi_komite_dan_portofolio(self):
        res = self.client.get(f"/api/v1/siswa/biaya-masuk-default/?kelompok={self.pg.pk}")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("uang_komite", res.data)
        self.assertNotIn("uang_portofolio", res.data)

    def test_guru_tidak_melihat_isian_komite(self):
        Siswa.objects.create(nama="Rahasia", kelompok=self.tka, spp_nominal=500000, status="aktif", uang_komite=1)
        guru = get_user_model().objects.create_user("co-guru")
        guru.groups.add(Group.objects.get(name="TeacherInCharge"))
        self.client.force_authenticate(guru)
        res = self.client.get("/api/v1/siswa/")
        row = res.data["results"][0] if "results" in res.data else res.data[0]
        self.assertNotIn("uang_komite", row)
        self.assertNotIn("uang_portofolio", row)


class SaldoAwalTests(CutoverBaseTest):
    def setUp(self):
        super().setUp()
        self.siswa = Siswa.objects.create(
            nama="Ayu", kelompok=self.tka, spp_nominal=500000, status="aktif",
            uang_masuk=1000000, uang_kegiatan=2000000,
        )
        from operations.services.biaya_masuk import sinkron_tagihan_biaya_masuk
        self.tagihan = sinkron_tagihan_biaya_masuk(self.siswa, periode=(7, 2026))

    def test_saldo_awal_tanpa_jurnal_mengurangi_sisa_berurutan(self):
        jurnal_awal = TrJurnal.objects.count()
        p = catat_saldo_awal_tagihan(self.tagihan, tanggal=date(2026, 12, 31), nominal=Decimal("1500000"))
        self.assertTrue(p.saldo_awal)
        self.assertIsNone(p.jurnal_id)
        self.assertIsNone(p.akun_kas_id)
        self.assertEqual(TrJurnal.objects.count(), jurnal_awal)
        alokasi = {a.detail.komponen: a.nominal for a in p.alokasi.select_related("detail")}
        self.assertEqual(alokasi, {"UANG_MASUK": Decimal("1000000"), "KEGIATAN": Decimal("500000")})
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, "SEBAGIAN")
        self.assertEqual(self.tagihan.sisa_tagihan, Decimal("1500000"))
        with self.assertRaises(ValueError):
            catat_saldo_awal_tagihan(self.tagihan, tanggal=date(2026, 12, 31), nominal=Decimal("1"))
        with self.assertRaises(ValueError):
            catat_saldo_awal_tagihan(self.tagihan, tanggal=date(2026, 12, 30), nominal=Decimal("9999999"))

    def test_sisa_dibayar_normal_dan_jurnal_hanya_untuk_penerimaan_baru(self):
        catat_saldo_awal_tagihan(self.tagihan, tanggal=date(2026, 12, 31), nominal=Decimal("1500000"))
        kegiatan = self.tagihan.detail.get(komponen="KEGIATAN")
        res = self.client.post(f"/api/v1/tagihan/{self.tagihan.pk}/bayar/", {
            "tanggal": "2027-01-05", "no_bukti": "BM-JAN", "nominal": "1500000", "akun_kas": "1101",
            "request_id": str(uuid.uuid4()), "alokasi": [{"detail": kegiatan.pk, "nominal": "1500000"}],
        }, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["tagihan"]["status"], "LUNAS")
        bayar = {p["no_bukti"]: p for p in res.data["tagihan"]["pembayaran"]}
        self.assertTrue(bayar["SALDO-AWAL-20261231"]["saldo_awal"])
        self.assertIsNone(bayar["SALDO-AWAL-20261231"]["jurnal_status"])
        self.assertEqual(bayar["BM-JAN"]["jurnal_status"], "DRAFT")
        jurnal = TrJurnal.objects.get(pk=res.data["jurnal_id"])
        self.assertEqual(sum(d.debit for d in jurnal.detail.all()), Decimal("1500000"))

    def test_batal_saldo_awal_oleh_tu_dengan_alasan(self):
        p = catat_saldo_awal_tagihan(self.tagihan, tanggal=date(2026, 12, 31), nominal=Decimal("3000000"))
        url = f"/api/v1/tagihan/{self.tagihan.pk}/batal-saldo-awal/"
        self.assertEqual(self.client.post(url, {"pembayaran": p.pk, "alasan": ""}, format="json").status_code, 400)
        self.client.force_authenticate(self.users["Finance"])
        self.assertEqual(self.client.post(url, {"pembayaran": p.pk, "alasan": "salah"}, format="json").status_code, 403)
        self.client.force_authenticate(self.users["Administration"])
        res = self.client.post(url, {"pembayaran": p.pk, "alasan": "Impor salah kolom"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["status"], "BELUM")
        self.assertEqual(self.client.post(url, {"pembayaran": p.pk, "alasan": "lagi"}, format="json").status_code, 400)

    def test_constraint_pembayaran_biasa_wajib_jurnal(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PembayaranTagihan.objects.create(
                tagihan=self.tagihan, tanggal=date(2026, 12, 31), no_bukti="X", nominal=1,
                request_id=uuid.uuid4(), akun_kas_id="1101",
            )


class ImporBiayaMasukTests(CutoverBaseTest):
    def setUp(self):
        super().setUp()
        self.lunas = Siswa.objects.create(nama="Anak Lunas", kelompok=self.tka, spp_nominal=1, status="aktif")
        self.cicil = Siswa.objects.create(nama="Anak Cicil", kelompok=self.pg, spp_nominal=1, status="aktif")
        self.kosong = Siswa.objects.create(nama="Anak Kosong", kelompok=self.tka, spp_nominal=1, status="aktif")
        self.janggal = Siswa.objects.create(nama="Anak Janggal", kelompok=self.tka, spp_nominal=1, status="aktif")
        rows = [JUDUL, SUB,
                _baris(1, "anak  LUNAS", "TK A", "SIB", 500000, (3000000, None, 5000000, 1500000, 700000, 500000), (5000000, 5200000)),
                _baris(2, "Anak Cicil", "PG Lebah 1", "UMUM", 0, (700000, 300000, 2500000, 1000000, 400000, 250000), (2000000,)),
                _baris(3, "Anak Kosong", "TK A", "UMUM", 0, (None,) * 6, ()),
                _baris(4, "Anak Janggal", "TK A", "UMUM", 0, (1000000, None, None, None, None, None), (2000000,)),
                _baris(5, "Anak Tidak Ada", "TK A", "UMUM", 0, (1000000, None, None, None, None, None), ()),
                ["", "", "TOTAL", "", "", "", "", "", "", "9.999"]]
        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        self.csv = buf.getvalue()

    def post(self, simpan=False, tanggal="2026-12-31"):
        berkas = SimpleUploadedFile("master.csv", self.csv.encode(), content_type="text/csv")
        return self.client.post("/api/v1/siswa/impor-biaya-masuk/", {"berkas": berkas, "tanggal": tanggal, "simpan": simpan}, format="multipart")

    def test_pratinjau_tidak_menyimpan(self):
        res = self.post()
        self.assertEqual(res.status_code, 200, res.data)
        r = res.data["ringkasan"]
        self.assertEqual((r["isi"], r["sudah"], r["lewati"], r["cek"], r["galat"]), (2, 0, 1, 1, 1))
        baris = {b["nama"]: b for b in res.data["baris"]}
        self.assertEqual(baris["anak LUNAS"]["ditagih"], 10200000)
        self.assertEqual(baris["anak LUNAS"]["terbayar"], 10200000)
        self.assertEqual(baris["Anak Cicil"]["komponen"]["uang_portofolio"], 300000)
        self.assertIn("melebihi", baris["Anak Janggal"]["alasan"])
        self.assertIn("tidak ditemukan", baris["Anak Tidak Ada"]["alasan"])
        self.assertFalse(Tagihan.objects.filter(jenis="BIAYA_MASUK").exists())
        self.assertFalse(PembayaranTagihan.objects.exists())
        self.lunas.refresh_from_db()
        self.assertIsNone(self.lunas.uang_masuk)

    def test_simpan_membuat_tagihan_awal_tp_dan_saldo_awal_lalu_impor_ulang_sudah(self):
        jurnal_awal = TrJurnal.objects.count()
        res = self.post(simpan=True)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["diisi"], 2)
        lunas = Tagihan.objects.get(siswa=self.lunas, jenis="BIAYA_MASUK")
        self.assertEqual((lunas.periode_bulan, lunas.periode_tahun, lunas.status), (7, 2026, "LUNAS"))
        self.assertEqual(lunas.total, Decimal("10200000"))
        cicil = Tagihan.objects.get(siswa=self.cicil, jenis="BIAYA_MASUK")
        self.assertEqual((cicil.status, cicil.sisa_tagihan), ("SEBAGIAN", Decimal("3150000")))
        self.assertEqual(set(cicil.detail.values_list("komponen", flat=True)),
                         {"UANG_MASUK", "PORTOFOLIO", "KEGIATAN", "PENGEMBANGAN", "KOMITE", "SERAGAM"})
        self.lunas.refresh_from_db()
        self.assertEqual((self.lunas.diskon_kategori, self.lunas.diskon_nominal), (["SIB"], Decimal("500000")))
        self.assertEqual(TrJurnal.objects.count(), jurnal_awal)
        self.assertTrue(all(p.saldo_awal and p.tanggal == date(2026, 12, 31) for p in PembayaranTagihan.objects.all()))
        # Tagihan Juli TP berikutnya tetap menagih Komite untuk tahun kedua, bukan tahun ini.
        lines, _t, _m = build_tagihan_komponen(self.cicil, 7, 2026)
        self.assertNotIn("KOMITE", {line["komponen"] for line in lines})

        ulang = self.post(simpan=True)
        self.assertEqual(ulang.data["diisi"], 0)
        self.assertEqual(ulang.data["ringkasan"]["sudah"], 2)
        self.assertEqual(PembayaranTagihan.objects.count(), 2)

    def test_hanya_tu_yang_bisa_impor(self):
        for role in ("Finance", "SchoolPrincipal"):
            self.client.force_authenticate(self.users[role])
            self.assertEqual(self.post().status_code, 403)

    def test_berkas_tanpa_kolom_biaya_masuk_ditolak(self):
        self.csv = "Nama,Kelas\nA,B\n"
        res = self.post()
        self.assertEqual(res.status_code, 400)
        self.assertIn("berkas", res.data)
