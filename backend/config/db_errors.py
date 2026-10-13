"""Terjemahkan pesan error database ke bahasa Indonesia yang ramah pegawai sekolah."""

from __future__ import annotations

import re


_FK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"mspostingrule|posting rule|belum diset", re.I),
        "Akun pendapatan untuk komponen tagihan belum dikonfigurasi. Hubungi Staff Keuangan.",
    ),
    (
        re.compile(
            r"insert or update on table \"tr_jurnal_detail\".*kode_akun|"
            r"Key \(kode_akun\)=.*is not present in table \"ms_coa\"",
            re.I,
        ),
        "Akun COA untuk jurnal belum terdaftar atau belum dikonfigurasi. Hubungi Staff Keuangan.",
    ),
    (
        re.compile(r"tr_jurnal_detail.*kode_akun|ms_coa.*tr_jurnal_detail", re.I),
        "Akun ini masih tercatat di jurnal. Nonaktifkan akun, atau hapus/ubah jurnal yang memakainya terlebih dahulu.",
    ),
    (
        re.compile(r"ms_sub_golongan.*ms_coa|ms_coa_sub_golongan", re.I),
        "Sub-golongan ini masih punya akun di dalamnya. Pindahkan atau hapus akun-akun tersebut dulu.",
    ),
    (
        re.compile(r"ms_golongan.*ms_sub_golongan|sub_golongan.*golongan", re.I),
        "Golongan ini masih punya sub-golongan. Hapus sub-golongan di dalamnya terlebih dahulu.",
    ),
    (
        re.compile(r"foreign key constraint|violates foreign key", re.I),
        "Data ini masih dipakai di bagian lain sistem. Periksa kembali sebelum menghapus atau mengubah.",
    ),
    (
        re.compile(r"duplicate key|already exists|unique constraint", re.I),
        "Kode atau data sudah ada. Gunakan kode lain atau edit data yang sudah terdaftar.",
    ),
    (
        re.compile(r"invalid page", re.I),
        "Halaman tidak ditemukan. Kembali ke halaman pertama.",
    ),
]


def humanize_db_error(raw: str) -> str:
    """Map pesan teknis PostgreSQL/DRF ke kalimat yang mudah dipahami."""
    text = (raw or "").strip()
    if not text:
        return "Operasi tidak dapat dilanjutkan. Mohon periksa kembali data Anda."

    for pattern, friendly in _FK_PATTERNS:
        if pattern.search(text):
            return friendly

    if len(text) > 200 or "constraint" in text.lower() or "pg_" in text.lower():
        return "Operasi tidak dapat dilanjutkan. Data mungkin masih dipakai di modul lain."

    return text
