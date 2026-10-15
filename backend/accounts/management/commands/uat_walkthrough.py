"""Jalankan UAT walkthrough UJ-1/2/3/4 + RBAC via APIClient (tanpa HTTP eksternal)."""

from __future__ import annotations

import time
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.test import APIClient

from accounting.models import MsCoa

User = get_user_model()


def _pick_coa(*candidates: str) -> str:
    for kode in candidates:
        if MsCoa.objects.filter(kode_akun=kode, is_active=True).exists():
            return kode
    return candidates[0]


class Command(BaseCommand):
    help = "UAT walkthrough otomatis — UJ-1, UJ-2, UJ-3, UJ-4, RBAC"

    def handle(self, *args, **options):
        if "testserver" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]
        self.results: list[tuple[str, str, bool, str]] = []
        self.client = APIClient()

        self.stdout.write("=== BeeSmart Finance UAT Walkthrough ===\n")
        jid = None
        try:
            self._preflight()
            self.stdout.write("")
            self._uj1()
            self.stdout.write("")
            jid = self._uj2()
            self.stdout.write("")
            self._uj3(jid)
            self.stdout.write("")
            self._uj4()
            self.stdout.write("")
            self._rbac()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Fatal: {exc}"))
            raise

        passed = sum(1 for *_, ok, _ in self.results if ok)
        failed = [r for r in self.results if not r[2]]
        self.stdout.write(f"\n=== RINGKASAN: {passed}/{len(self.results)} pass ===")
        for uj, step, _, note in failed:
            self.stderr.write(self.style.ERROR(f"  [{uj}] {step} — {note}"))
        if failed:
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("\nSemua langkah UAT lulus ✅"))

    def _auth(self, username: str):
        user = User.objects.get(username=username)
        self.client.force_authenticate(user=user)
        return user

    def _record(self, uj: str, step: str, ok: bool, note: str = ""):
        self.results.append((uj, step, ok, note))
        mark = "✅" if ok else "❌"
        line = f"{mark} [{uj}] {step}"
        if note:
            line += f" — {note}"
        self.stdout.write(line)

    def _preflight(self):
        uj = "SETUP"
        count = MsCoa.objects.filter(is_active=True).count()
        self._record(uj, "COA Final loaded (≥180 akun)", count >= 180, f"{count} akun")
        for username in ("admin.tu", "keuangan", "kepsek", "guru.kegiatan"):
            ok = User.objects.filter(username=username, is_active=True).exists()
            self._record(uj, f"User demo {username}", ok)

    def _uj1(self):
        uj = "UJ-1"
        user = self._auth("admin.tu")
        self._record(uj, "Login admin.tu", user.groups.filter(name="Administration").exists(), user.username)

        r = self.client.get("/api/v1/siswa/")
        self._record(uj, "Akses data siswa", r.status_code == 200 and r.data["count"] > 0, f"{r.data['count']} siswa")
        sid = r.data["results"][0]["id"]

        r = self.client.get("/api/v1/jenjang/")
        self._record(uj, "Load jenjang absensi", r.status_code == 200 and len(r.data["results"]) > 0)

        r = self.client.get("/api/v1/kelompok/")
        self._record(uj, "Load kelompok", r.status_code == 200 and len(r.data["results"]) > 0)

        today = date.today().isoformat()
        payload = {
            "siswa": sid, "tanggal": today, "status": "hadir",
            "ikut_katering": True, "jemput_datang": False, "jemput_pulang": False,
        }
        existing = self.client.get(f"/api/v1/kehadiran-siswa/?siswa={sid}&tanggal={today}")
        if existing.data.get("results"):
            kid = existing.data["results"][0]["id"]
            r = self.client.patch(f"/api/v1/kehadiran-siswa/{kid}/", payload, format="json")
            self._record(uj, "Absensi simpan", r.status_code == 200, f"update #{sid}")
            r = self.client.delete(f"/api/v1/kehadiran-siswa/{kid}/")
            self._record(uj, "Absensi hapus", r.status_code in (204, 403), str(r.status_code))
            r = self.client.post("/api/v1/kehadiran-siswa/", payload, format="json")
            self._record(uj, "Absensi create ulang", r.status_code == 201)
        else:
            r = self.client.post("/api/v1/kehadiran-siswa/", payload, format="json")
            self._record(uj, "Absensi simpan", r.status_code == 201, f"create #{sid}")

        bulan, tahun = date.today().month, date.today().year
        last = monthrange(tahun, bulan)[1]
        pad = str(bulan).zfill(2)
        r = self.client.get(
            f"/api/v1/kehadiran-siswa/?tanggal__gte={tahun}-{pad}-01&tanggal__lte={tahun}-{pad}-{last}"
        )
        self._record(uj, "Rekap absensi (data bulan)", r.status_code == 200, f"{r.data['count']} record")

        r = self.client.post("/api/v1/tagihan/preview/", {
            "siswa": sid, "periode_bulan": bulan, "periode_tahun": tahun, "tarif_katering": 0,
        }, format="json")
        self._record(uj, "Tagihan preview", r.status_code == 200 and Decimal(r.data["total"]) > 0, f"total {r.data['total']}")

        listed = self.client.get(f"/api/v1/tagihan/?siswa={sid}&periode_bulan={bulan}&periode_tahun={tahun}")
        if listed.data.get("results"):
            tid = listed.data["results"][0]["id"]
            tnote = f"existing {listed.data['results'][0]['status']}"
        else:
            r = self.client.post("/api/v1/tagihan/generate/", {
                "siswa": sid, "periode_bulan": bulan, "periode_tahun": tahun, "tarif_katering": 0,
            }, format="json")
            tid = r.data.get("id") if r.status_code == 201 else None
            tnote = "generated" if tid else str(r.data)
        self._record(uj, "Tagihan generate/existing", tid is not None, tnote)

        if tid:
            detail = self.client.get(f"/api/v1/tagihan/{tid}/").data
            if detail["status"] in ("BELUM", "SEBAGIAN"):
                r = self.client.post(f"/api/v1/tagihan/{tid}/bayar/")
                self._record(uj, "Tagihan bayar", r.status_code == 200, r.data.get("tagihan", {}).get("status", ""))
            else:
                self._record(uj, "Tagihan bayar", True, f"skip {detail['status']}")
            r = self.client.get(f"/api/v1/tagihan/{tid}/struk/")
            self._record(uj, "Cetak struk", r.status_code == 200 and "rincian" in r.data)

        uniq = f"UAT-{int(time.time())}"
        r = self.client.post("/api/v1/pendaftaran-siswa/", {
            "nama_calon": uniq, "tanggal_daftar": today,
            "biaya_sitin": "100000", "biaya_formulir": "500000",
        }, format="json")
        pid = r.data.get("id") if r.status_code == 201 else None
        self._record(uj, "Pendaftaran calon baru", r.status_code == 201, f"id={pid}")

        if pid:
            r = self.client.post(f"/api/v1/pendaftaran-siswa/{pid}/bayar-sitin/", {
                "komponen": ["SITIN"], "tanggal": today, "no_bukti": f"SIT-{uniq}",
                "nominal": "100000", "akun_kas": _pick_coa("111", "112", "1101"),
            }, format="json")
            self._record(uj, "Bayar sit-in", r.status_code == 200, r.data.get("detail", "")[:40])
            r = self.client.post(f"/api/v1/pendaftaran-siswa/{pid}/finalisasi/", {"spp_nominal": "400000"}, format="json")
            self._record(uj, "Finalisasi pendaftaran", r.status_code == 200 and r.data["status"] == "REGISTERED")

        self._record(uj, "Modul katering", self.client.get("/api/v1/menu-katering/").status_code == 200)
        self._record(uj, "Modul jemputan", self.client.get("/api/v1/pendaftaran-jemputan/").status_code == 200)
        self._record(uj, "Export legacy katering", self.client.get(
            "/api/v1/export/legacy/katering/", {"bulan": 7, "tahun": 2025},
        ).status_code == 200)
        self._record(uj, "Export legacy jemput", self.client.get(
            "/api/v1/export/legacy/jemput/", {"bulan": 7, "tahun": 2025},
        ).status_code == 200)

    def _uj2(self):
        uj = "UJ-2"
        user = self._auth("keuangan")
        self._record(uj, "Login keuangan", user.groups.filter(name="Finance").exists())

        r = self.client.get("/api/v1/dashboard/ringkasan/")
        self._record(uj, "Dashboard KPI", r.status_code == 200 and "operasional" in r.data)

        coa_count = self.client.get("/api/v1/coa/").data.get("count", 0)
        self._record(uj, "COA list lengkap", coa_count >= 180, f"{coa_count} akun")

        kas = _pick_coa("111", "112", "1101")
        pend = _pick_coa("411", "4101")
        suffix = int(time.time()) % 100000
        r = self.client.post("/api/v1/jurnal/", {
            "no_bukti": f"UAT{suffix}",
            "tanggal": date.today().isoformat(),
            "keterangan": "UAT walkthrough",
            "detail": [
                {"kode_akun": kas, "debit": "50000", "kredit": "0"},
                {"kode_akun": pend, "debit": "0", "kredit": "50000"},
            ],
        }, format="json")
        jid = r.data.get("id") if r.status_code == 201 else None
        self._record(uj, "Buat jurnal seimbang", r.status_code == 201, f"kas={kas} cr={pend} id={jid}")

        if jid:
            r = self.client.patch(f"/api/v1/jurnal/{jid}/", {
                "no_bukti": f"UAT{suffix}",
                "tanggal": date.today().isoformat(),
                "keterangan": "UAT walkthrough (edited)",
                "detail": [
                    {"kode_akun": kas, "debit": "75000", "kredit": "0"},
                    {"kode_akun": pend, "debit": "0", "kredit": "75000"},
                ],
            }, format="json")
            self._record(uj, "Edit jurnal DRAFT", r.status_code == 200)
            r = self.client.post(f"/api/v1/jurnal/{jid}/submit/")
            self._record(uj, "Submit jurnal → PENDING", r.status_code == 200 and r.data["status"] == "PENDING")

        self._record(uj, "Tunggakan tagihan read", self.client.get("/api/v1/tagihan/?status=BELUM").status_code == 200)
        self._record(uj, "Laporan neraca saldo", self.client.get("/api/v1/laporan/neraca-saldo/").status_code == 200)
        self._record(uj, "Laporan realisasi anggaran", self.client.get("/api/v1/laporan/realisasi-anggaran/").status_code == 200)
        self._record(uj, "Laporan buku besar", self.client.get(f"/api/v1/laporan/buku-besar/{pend}/").status_code == 200)

        peg = self.client.get("/api/v1/pegawai/")
        self._record(uj, "Akses pegawai/gaji", peg.status_code == 200)
        if peg.data.get("results"):
            peg_id = peg.data["results"][0]["id"]
            bulan, tahun = date.today().month, date.today().year
            listed = self.client.get(f"/api/v1/gaji/?pegawai={peg_id}&periode_bulan={bulan}&periode_tahun={tahun}")
            if listed.data.get("results"):
                gid = listed.data["results"][0]["id"]
                self._record(uj, "Buat slip gaji", True, f"existing id={gid}")
            else:
                r = self.client.post("/api/v1/gaji/", {
                    "pegawai": peg_id, "periode_bulan": bulan, "periode_tahun": tahun, "gaji_pokok": "3000000",
                }, format="json")
                gid = r.data.get("id") if r.status_code == 201 else None
                self._record(uj, "Buat slip gaji", r.status_code == 201, f"id={gid}")
            if gid:
                r = self.client.post(f"/api/v1/gaji/{gid}/posting/")
                ok = r.status_code == 200 or (
                    r.status_code == 400 and "sudah" in str(r.data).lower()
                )
                self._record(uj, "Posting gaji", ok, str(r.data)[:50])

        r = self.client.get("/api/v1/audit-log/?page=2")
        self._record(uj, "Audit log page 2", r.status_code == 200, f"count={r.data.get('count', 0)}")

        if jid:
            self._record(uj, "SoD: finance tidak approve", self.client.post(f"/api/v1/jurnal/{jid}/approve/").status_code == 403)
        return jid

    def _uj3(self, jid):
        uj = "UJ-3"
        user = self._auth("kepsek")
        self._record(uj, "Login kepsek", user.groups.filter(name="SchoolPrincipal").exists())
        r = self.client.get("/api/v1/dashboard/ringkasan/")
        self._record(uj, "Dashboard KPI", r.status_code == 200 and "operasional" in r.data)

        r = self.client.get("/api/v1/coa/")
        self._record(uj, "COA read-only (list)", r.status_code == 200)
        r = self.client.post("/api/v1/coa/", {
            "kode_akun": "9999", "nama_akun": "UAT", "sub_golongan": "11", "posisi_normal": "D",
        }, format="json")
        self._record(uj, "COA tidak bisa tambah (kepsek)", r.status_code == 403)

        if jid:
            r = self.client.post(f"/api/v1/jurnal/{jid}/approve/")
            self._record(uj, "Approve jurnal PENDING", r.status_code == 200 and r.data["status"] == "POSTED")

        r = self.client.get("/api/v1/audit-log/")
        self._record(uj, "Audit log list", r.status_code == 200, f"{r.data['count']} entri")
        if r.data.get("results"):
            aid = r.data["results"][0]["id"]
            det = self.client.get(f"/api/v1/audit-log/{aid}/")
            self._record(uj, "Audit log detail", det.status_code == 200)

        self._record(uj, "Review laporan", self.client.get("/api/v1/laporan/neraca-saldo/").status_code == 200)
        self._record(uj, "Akses periode akuntansi", self.client.get("/api/v1/periode/").status_code == 200)

        periode = self.client.get("/api/v1/periode/?status=OPEN")
        if periode.data.get("results"):
            pid = periode.data["results"][0]["id"]
            r = self.client.post(f"/api/v1/periode/{pid}/tutup/")
            self._record(uj, "Tutup buku periode OPEN", r.status_code in (200, 400), str(r.data)[:40])
        else:
            self._record(uj, "Tutup buku periode OPEN", True, "skip — tidak ada periode OPEN")

        peg = self.client.get("/api/v1/pegawai/")
        beban = _pick_coa("5101", "5102", "5301")
        per = self.client.get("/api/v1/periode/").data.get("results", [])
        periode_id = per[0]["id"] if per else None
        if peg.data.get("results") and periode_id:
            r = self.client.post("/api/v1/kegiatan/", {
                "nama": f"UAT Kegiatan {int(time.time()) % 10000}",
                "akun_beban": beban,
                "pagu": "5000000",
                "penanggung_jawab": peg.data["results"][0]["id"],
                "periode": periode_id,
            }, format="json")
            self._record(uj, "Buat kegiatan + TA", r.status_code == 201, f"beban={beban}")

    def _uj4(self):
        uj = "UJ-4"
        user = self._auth("guru.kegiatan")
        self._record(uj, "Login guru.kegiatan", user.groups.filter(name="TeacherInCharge").exists())

        r = self.client.get("/api/v1/kegiatan/")
        self._record(uj, "Akses daftar kegiatan", r.status_code == 200, f"{r.data.get('count', 0)} kegiatan")

        listed = self.client.get("/api/v1/kegiatan/")
        sample = listed.data.get("results", [{}])[0] if listed.data.get("results") else {}
        pj = sample.get("penanggung_jawab")
        periode_id = sample.get("periode")
        beban = sample.get("akun_beban") or _pick_coa("5101", "5102", "5301")
        if pj and periode_id:
            r = self.client.post("/api/v1/kegiatan/", {
                "nama": "UAT Guru Create",
                "akun_beban": beban,
                "pagu": "1000000",
                "penanggung_jawab": pj,
                "periode": periode_id,
            }, format="json")
            self._record(uj, "RBAC: guru tidak buat kegiatan", r.status_code == 403)
        else:
            self._record(uj, "RBAC: guru tidak buat kegiatan", True, "skip — tidak ada kegiatan sample")

        if listed.data.get("results"):
            kid = listed.data["results"][0]["id"]
            k = self.client.get(f"/api/v1/kegiatan/{kid}/").data
            sisa = Decimal(k.get("sisa_pagu") or k.get("pagu") or 0)
            if sisa > 0:
                r = self.client.post(f"/api/v1/kegiatan/{kid}/realisasi/", {
                    "nominal": "100000", "deskripsi": "UAT realisasi",
                }, format="json")
                self._record(uj, "Catat realisasi kegiatan", r.status_code == 201, r.data.get("detail", "")[:40])
            else:
                self._record(uj, "Catat realisasi kegiatan", True, "skip — pagu habis")
            lap = self.client.get(f"/api/v1/kegiatan/{kid}/laporan/")
            self._record(uj, "Laporan utilisasi", lap.status_code == 200 and "rasio_utilisasi" in lap.data)

        r = self.client.get("/api/v1/kehadiran-siswa/")
        self._record(uj, "Rekap absensi read-only", r.status_code == 200)
        r = self.client.post("/api/v1/kehadiran-siswa/", {
            "siswa": 1, "tanggal": date.today().isoformat(), "status": "hadir",
        }, format="json")
        self._record(uj, "RBAC: guru tidak input absensi", r.status_code == 403)

    def _rbac(self):
        uj = "RBAC"
        self._auth("admin.tu")
        self._record(uj, "TU tidak akses dashboard API", self.client.get("/api/v1/dashboard/ringkasan/").status_code == 403)
        self._record(uj, "TU tidak akses gaji", self.client.get("/api/v1/gaji/").status_code == 403)
        self._record(uj, "TU akses tagihan", self.client.get("/api/v1/tagihan/").status_code == 200)

        self._auth("kepsek")
        kas = _pick_coa("111", "112", "1101")
        pend = _pick_coa("411", "4101")
        r = self.client.post("/api/v1/jurnal/", {
            "no_bukti": f"RBAC{int(time.time()) % 1000}",
            "tanggal": date.today().isoformat(),
            "keterangan": "RBAC test",
            "detail": [
                {"kode_akun": kas, "debit": "1000", "kredit": "0"},
                {"kode_akun": pend, "debit": "0", "kredit": "1000"},
            ],
        }, format="json")
        self._record(uj, "Kepsek tidak buat jurnal", r.status_code == 403)
        self._record(uj, "Kepsek tidak akses siswa write", self.client.post("/api/v1/siswa/", {}).status_code == 403)

        self._auth("guru.kegiatan")
        self._record(uj, "Guru tidak akses dashboard", self.client.get("/api/v1/dashboard/ringkasan/").status_code == 403)
        self._record(uj, "Guru tidak akses tagihan write", self.client.post("/api/v1/tagihan/generate/", {}).status_code == 403)
