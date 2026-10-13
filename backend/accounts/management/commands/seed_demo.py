"""Seed demo users, master data, and COA for UAT / skripsi."""

from __future__ import annotations

import csv
import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from operations.models import ArmadaJemputan, Jenjang, Kelompok, Pegawai, PendaftaranJemputan, Siswa

User = get_user_model()

DEFAULT_PASSWORD = "LebahMadu2026!"

DEMO_USERS = [
    {
        "username": "admin.tu",
        "first_name": "Bu",
        "last_name": "Fitri",
        "group": "Administration",
    },
    {
        "username": "keuangan",
        "first_name": "Staff",
        "last_name": "Keuangan",
        "group": "Finance",
    },
    {
        "username": "kepsek",
        "first_name": "Pak",
        "last_name": "Ali",
        "group": "SchoolPrincipal",
    },
    {
        "username": "guru.kegiatan",
        "first_name": "Bu",
        "last_name": "Desi",
        "group": "TeacherInCharge",
    },
]

JENJANG = [
    ("PG", "Playgroup"),
    ("TKA", "TK A"),
    ("TKB", "TK B"),
]

KELOMPOK = [
    ("PG", "PG Merah"),
    ("TKA", "TKA Melati"),
    ("TKB", "TKB Mawar"),
]

SAMPLE_SISWA = [
    ("LM-001", "Aisyah Putri", "PG", "PG Merah", "1350000"),
    ("LM-002", "Bima Sakti", "TKA", "TKA Melati", "1350000"),
    ("LM-003", "Citra Lestari", "TKB", "TKB Mawar", "1350000"),
]

SAMPLE_PEGAWAI = [
    ("PG-001", "Ibu Sari", "Guru PG"),
    ("PG-002", "Pak Rudi", "Supir Jemputan"),
    ("ADM-001", "Bu Dewi", "Staf TU"),
]


def _raw_data_dir() -> Path:
    return Path(settings.BASE_DIR).parent / "database" / "raw_data"


def _posisi_normal(kode_akun: str) -> str:
    return "D" if kode_akun.startswith(("1", "5")) else "K"


class Command(BaseCommand):
    help = "Seed 4 role users, jenjang/kelompok, sample siswa, and COA from CSV (dev/UAT)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users-only",
            action="store_true",
            help="Hanya buat/update user demo (skip COA & siswa).",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help=f"Password dev untuk semua user demo (default: {DEFAULT_PASSWORD}).",
        )
        parser.add_argument(
            "--passwords-env",
            metavar="NAME",
            help="Nama environment variable berisi JSON password unik per username demo.",
        )
        parser.add_argument(
            "--skip-coa",
            action="store_true",
            help="Lewati import COA dari CSV.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password_env: str | None = options["passwords_env"]
        if password_env:
            try:
                passwords = json.loads(os.environ[password_env])
            except (KeyError, json.JSONDecodeError) as exc:
                raise CommandError("Environment password demo tidak tersedia atau JSON tidak valid.") from exc
            usernames = {spec["username"] for spec in DEMO_USERS}
            if (
                not isinstance(passwords, dict)
                or set(passwords) != usernames
                or any(not isinstance(value, str) or len(value) < 20 for value in passwords.values())
                or len(set(passwords.values())) != len(usernames)
            ):
                raise CommandError("Password demo harus unik, minimal 20 karakter, untuk setiap username demo.")
        else:
            passwords = {spec["username"]: options["password"] for spec in DEMO_USERS}
        users_only: bool = options["users_only"]
        skip_coa: bool = options["skip_coa"]

        self._ensure_groups()
        self._seed_users(passwords)

        if users_only:
            self.stdout.write(self.style.SUCCESS("seed_demo: users selesai (--users-only)."))
            return

        self._seed_jenjang_kelompok()
        self._seed_siswa()
        self._seed_pegawai()
        self._seed_jemputan()

        if not skip_coa:
            self._seed_coa_from_csv()

        self._seed_posting_rules()
        from operations.services.tp_templates import ensure_tp_templates

        ensure_tp_templates()
        self.stdout.write("  template komponen TP OK")

        self.stdout.write(self.style.SUCCESS("seed_demo: selesai."))

    def _ensure_groups(self):
        for name in ["Finance", "SchoolPrincipal", "Administration", "TeacherInCharge"]:
            Group.objects.get_or_create(name=name)

    def _seed_users(self, passwords: dict[str, str]):
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "is_staff": True,
                },
            )
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_staff = True
            user.set_password(passwords[spec["username"]])
            user.save()

            group = Group.objects.get(name=spec["group"])
            user.groups.set([group])

            verb = "dibuat" if created else "diperbarui"
            self.stdout.write(f"  user {spec['username']} ({spec['group']}) {verb}")

    def _seed_jenjang_kelompok(self):
        jenjang_map: dict[str, Jenjang] = {}
        for kode, nama in JENJANG:
            j, _ = Jenjang.objects.get_or_create(kode=kode, defaults={"nama": nama})
            j.nama = nama
            j.save(update_fields=["nama"])
            jenjang_map[kode] = j

        for j_kode, k_nama in KELOMPOK:
            Kelompok.objects.get_or_create(
                jenjang=jenjang_map[j_kode],
                nama=k_nama,
            )

        self.stdout.write("  jenjang & kelompok demo OK")

    def _seed_siswa(self):
        kelompok_map = {
            (k.jenjang.kode, k.nama): k
            for k in Kelompok.objects.select_related("jenjang")
        }

        for nis, nama, j_kode, k_nama, spp in SAMPLE_SISWA:
            kel = kelompok_map.get((j_kode, k_nama))
            Siswa.objects.update_or_create(
                nis=nis,
                defaults={
                    "nama": nama,
                    "kelompok": kel,
                    "spp_nominal": Decimal(spp),
                    "status": "aktif",
                    "nama_ibu": "Ibu Wali",
                    "kontak_ibu": "081234567890",
                },
            )

        self.stdout.write(f"  {len(SAMPLE_SISWA)} siswa demo OK")

    def _seed_pegawai(self):
        for nip, nama, jabatan in SAMPLE_PEGAWAI:
            Pegawai.objects.update_or_create(
                nip=nip,
                defaults={
                    "nama": nama,
                    "jabatan": jabatan,
                    "status_aktif": True,
                    "tanggal_mulai_kerja": date(2024, 1, 1),
                },
            )

        self.stdout.write(f"  {len(SAMPLE_PEGAWAI)} pegawai demo OK")

    def _seed_jemputan(self):
        armada, _ = ArmadaJemputan.objects.get_or_create(
            nama_supir="Pak Budi",
            defaults={
                "jenis_mobil": "Avanza",
                "kapasitas": 7,
                "keterangan": "Rute Jakarta Timur",
            },
        )
        siswa = Siswa.objects.filter(nis="LM-002").first()
        if siswa:
            PendaftaranJemputan.objects.update_or_create(
                siswa=siswa,
                armada=armada,
                defaults={"harga": Decimal("350000")},
            )
        self.stdout.write("  jemputan demo OK")

    def _seed_coa_from_csv(self):
        base = Path(settings.BASE_DIR).parent
        final_path = base / "legacy-data" / "Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv"
        if final_path.is_file():
            if MsCoa.objects.exists():
                self.stdout.write("  COA sudah ada — skip (jalankan: import_coa_final --replace)")
                return
            from accounting.coa_final_import import import_coa_final

            stats = import_coa_final(final_path)
            self.stdout.write(
                f"  COA Final: {stats['akun_total']} akun "
                f"(+{stats['golongan']} gol, +{stats['sub']} sub, +{stats['akun']} akun baru)"
            )
            return

        data_dir = _raw_data_dir()
        if not data_dir.is_dir():
            self.stdout.write(self.style.WARNING(f"  COA skip: folder tidak ada ({data_dir})"))
            return

        if MsCoa.objects.exists():
            self.stdout.write("  COA sudah ada — skip import CSV")
            return

        gol_path = data_dir / "T_GOLKUN.csv"
        sub_path = data_dir / "T_SUBGOL.csv"
        akun_path = data_dir / "T_AKUN.csv"

        for path in (gol_path, sub_path, akun_path):
            if not path.is_file():
                self.stdout.write(self.style.WARNING(f"  COA skip: {path.name} tidak ditemukan"))
                return

        with gol_path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                kode = str(row["NOGOL"]).strip()
                MsGolongan.objects.get_or_create(
                    kode_golongan=kode,
                    defaults={"nama_golongan": row["NAMGOL"].strip()},
                )

        with sub_path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                gol = MsGolongan.objects.filter(kode_golongan=str(row["NOGOL"]).strip()).first()
                if not gol:
                    continue
                MsSubGolongan.objects.get_or_create(
                    kode_sub=str(row["NOSUBGOL"]).strip(),
                    defaults={
                        "golongan": gol,
                        "nama_sub": row["NAMSUBGOL"].strip(),
                    },
                )

        count = 0
        with akun_path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                kode = str(row["NOKUN"]).strip()
                sub = MsSubGolongan.objects.filter(kode_sub=str(row["NOSUBGOL"]).strip()).first()
                if not sub:
                    continue
                MsCoa.objects.get_or_create(
                    kode_akun=kode,
                    defaults={
                        "sub_golongan": sub,
                        "nama_akun": row["NAMKUN"].strip(),
                        "posisi_normal": _posisi_normal(kode),
                        "is_active": True,
                    },
                )
                count += 1

        self.stdout.write(f"  COA import: {count} akun dari CSV")

    def _seed_posting_rules(self):
        """MsPostingRule untuk auto-jurnal tagihan, kas, dan payroll."""
        from operations.services.coa_resolve import seed_system_posting_rules

        try:
            mapped = seed_system_posting_rules()
            self.stdout.write(
                "  MsPostingRule OK — "
                + ", ".join(f"{k}={v}" for k, v in mapped.items())
            )
        except ValueError as exc:
            self.stdout.write(self.style.WARNING(f"  posting rules skip: {exc}"))
