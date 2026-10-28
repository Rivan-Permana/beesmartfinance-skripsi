"""Impor tarif SPP per siswa dari tab master Recap Cash In.

Tab master memuat satu baris per siswa dengan kolom per bulan (Juli–Juni); sub-judul tiap bulan
berisi Tgl | SPP | Tgl | Cat | Jem | Tgl | LSU. Tarif SPP = nominal SPP yang paling sering dibayar.
Hanya `spp_nominal` yang diubah; tagihan, jurnal, biodata, dan biaya masuk tidak disentuh.
"""

import re
from collections import Counter
from decimal import Decimal

from django.db import transaction

from .common import audit_user
from .impor_biodata import ImporBiodataError, baca_csv, kunci_nama

CHANGE_REASON = "Impor SPP CSV"
SPP_MIN = 500_000
SPP_MAKS = 2_000_000
_BULAN = ("juli", "agustus", "september", "oktober", "november", "desember",
          "januari", "februari", "maret", "april", "mei", "juni")


def _rupiah(teks):
    """'1.350.000' / 'Rp1.350.000' / '1350000' -> 1350000; selain angka -> None."""
    teks = (teks or "").strip()
    if not re.fullmatch(r"(Rp\s?)?[\d.,]+", teks) or not re.search(r"\d", teks):
        return None
    return int(re.sub(r"\D", "", teks))


def parse_master(berkas):
    """Baris siswa dari tab master: nomor baris, nama, kelas, dan daftar nominal SPP yang dibayar."""
    rows = baca_csv(berkas, "master")
    for i, row in enumerate(rows[:-1]):
        lower = [c.casefold() for c in row]
        if "nama" not in lower or not any(b in lower for b in _BULAN):
            continue
        sub = [c.casefold() for c in rows[i + 1]]
        kolom_spp = [j for j, c in enumerate(sub) if c == "spp"]
        if not kolom_spp:
            continue
        kolom_nama = lower.index("nama")
        kolom_kelas = lower.index("kelas") if "kelas" in lower else None
        mulai = i + 2
        break
    else:
        raise ImporBiodataError("Judul kolom 'Nama' dan kolom SPP per bulan tidak ditemukan. Pastikan tab master yang diunduh.")

    hasil = []
    for i, row in enumerate(rows[mulai:], start=mulai):
        ambil = lambda j: row[j] if j is not None and j < len(row) else ""  # noqa: E731
        nama = ambil(kolom_nama)
        if not re.search(r"[^\W\d_]", nama) or not ambil(kolom_nama - 1).isdigit():
            continue  # baris rekap atau kosong
        nilai = [v for v in (_rupiah(ambil(j)) for j in kolom_spp) if v]
        hasil.append({"baris": i + 1, "nama": " ".join(nama.split()), "kelas": ambil(kolom_kelas), "nilai": nilai})
    if not hasil:
        raise ImporBiodataError("Tidak ada baris siswa bernomor urut di berkas ini.")
    return hasil


def susun_spp(baris_mentah, siswa_qs):
    """Bandingkan tarif dari berkas dengan SPP siswa. Tidak menyimpan apa pun.

    aksi: isi (SPP sistem masih 0), sama, beda (SPP sistem sudah terisi dan berbeda; tidak diubah),
    cek (perlu dicek manual), galat (tidak cocok dengan siswa sistem).
    """
    per_nama = {}
    for siswa in siswa_qs:
        per_nama.setdefault(kunci_nama(siswa.nama), []).append(siswa)
    kembar = Counter(kunci_nama(r["nama"]) for r in baris_mentah)

    hasil = []
    for mentah in baris_mentah:
        kunci = kunci_nama(mentah["nama"])
        cocok = per_nama.get(kunci, [])
        hitung = Counter(mentah["nilai"])
        tarif = hitung.most_common(1)[0][0] if hitung else None
        item = {
            "baris": mentah["baris"], "nama": mentah["nama"], "kelas": mentah["kelas"],
            "siswa": cocok[0].pk if len(cocok) == 1 else None,
            "spp_lama": str(cocok[0].spp_nominal) if len(cocok) == 1 else None,
            "spp_baru": str(Decimal(tarif)) if tarif else None,
            "nilai": sorted(hitung), "alasan": None,
        }
        if kembar[kunci] > 1:
            item["aksi"], item["alasan"] = "galat", "Nama ini muncul lebih dari sekali di berkas."
        elif not cocok:
            item["aksi"], item["alasan"] = "galat", "Siswa tidak ditemukan di sistem. Impor biodata dulu."
        elif len(cocok) > 1:
            item["aksi"], item["alasan"] = "galat", "Ada lebih dari satu siswa bernama sama di sistem."
        elif not tarif:
            item["aksi"], item["alasan"] = "cek", "Belum ada pembayaran SPP di berkas."
        elif len(hitung) > 1:
            item["aksi"], item["alasan"] = "cek", "Nominal SPP berbeda antar bulan."
        elif not SPP_MIN <= tarif <= SPP_MAKS:
            item["aksi"], item["alasan"] = "cek", "Nominal di luar Rp 500.000–2.000.000; mungkin bayar beberapa bulan sekaligus."
        elif Decimal(tarif) == cocok[0].spp_nominal:
            item["aksi"] = "sama"
        elif cocok[0].spp_nominal > 0:
            item["aksi"] = "beda"
        else:
            item["aksi"] = "isi"
        hasil.append(item)
    return hasil


def terapkan_spp(hasil, user=None):
    """Isi SPP untuk baris aksi 'isi' dalam satu transaksi."""
    from operations.models import Siswa

    diisi = 0
    with transaction.atomic(), audit_user(user):
        for item in hasil:
            if item["aksi"] != "isi":
                continue
            siswa = Siswa.objects.select_for_update().get(pk=item["siswa"])
            if siswa.spp_nominal > 0:
                continue  # sudah diisi orang lain sejak pratinjau
            siswa.spp_nominal = Decimal(item["spp_baru"])
            siswa._change_reason = CHANGE_REASON
            siswa.save()
            diisi += 1
    return diisi


def ringkas_spp(hasil):
    hitung = {aksi: 0 for aksi in ("isi", "sama", "beda", "cek", "galat")}
    for item in hasil:
        hitung[item["aksi"]] += 1
    return hitung
