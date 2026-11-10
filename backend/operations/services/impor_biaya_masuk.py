"""Impor biaya masuk per siswa dari tab master Recap Cash In untuk cut-over.

Tab master memuat satu baris per siswa: kategori dan jumlah diskon, komponen biaya masuk (Uang Masuk,
Portofolio PG, Kegiatan, Pengembangan, Komite, Seragam), jumlah sebelum/sesudah diskon, dan cicilan 1–6.
Untuk tiap siswa, isian biaya masuk diisi, tagihan BIAYA_MASUK dibentuk dengan periode awal tahun
pelajaran, lalu total cicilan dicatat sebagai satu penerimaan saldo awal tanpa jurnal.

Pratinjau menjalankan langkah yang sama di dalam transaksi yang dibatalkan, jadi hasil pratinjau
termasuk galat dari aturan tagihan (mis. komponen sudah ditagih di tagihan Juli).
"""

import re
from collections import Counter
from decimal import Decimal

from django.db import transaction

from .common import audit_user
from .impor_biodata import ImporBiodataError, baca_csv, kunci_nama
from .impor_spp import _rupiah

CHANGE_REASON = "Impor biaya masuk (cut-over)"
# Judul kolom di tab master (baris judul + sub-judul, huruf kecil) -> field Siswa.
KOLOM_KOMPONEN = (
    ("uang masuk", "uang_masuk"),
    ("portofolio", "uang_portofolio"),
    ("kegiatan", "uang_kegiatan"),
    ("pengembangan", "uang_pengembangan"),
    ("komite", "uang_komite"),
    ("seragam", "uang_seragam"),
)
TANPA_DISKON = {"", "-", "UMUM"}


def _cari_kolom(judul, cocok):
    return next((j for j, teks in enumerate(judul) if cocok(teks)), None)


def parse_master(berkas):
    """Baris siswa dari tab master beserta isian biaya masuk dan total cicilan."""
    rows = baca_csv(berkas, "master")
    for i, row in enumerate(rows[:-1]):
        lower = [c.casefold().strip() for c in row]
        if "nama" not in lower or "uang masuk" not in lower:
            continue
        sub = rows[i + 1] + [""] * max(0, len(row) - len(rows[i + 1]))
        judul = [" ".join(f"{a} {b}".split()).casefold() for a, b in zip(row + [""] * (len(sub) - len(row)), sub)]
        kolom = {field: _cari_kolom(judul, lambda t, k=label: t.startswith(k)) for label, field in KOLOM_KOMPONEN}
        kolom_nama = lower.index("nama")
        kolom_kelas = _cari_kolom(judul, lambda t: t == "kelas")
        kolom_kategori = _cari_kolom(judul, lambda t: t == "status diskon")
        kolom_diskon = _cari_kolom(judul, lambda t: t == "jml diskon")
        kolom_netto = _cari_kolom(judul, lambda t: t.startswith("jml stlh"))
        kolom_lunas = _cari_kolom(judul, lambda t: t.startswith("lunas"))
        kolom_cicilan = [j for j, t in enumerate(judul) if re.fullmatch(r"(cicilan )?cil \d+", t)]
        mulai = i + 2
        break
    else:
        raise ImporBiodataError("Judul kolom 'Nama' dan 'Uang Masuk' tidak ditemukan. Pastikan tab master yang diunduh.")
    if any(j is None for j in kolom.values()) or not kolom_cicilan:
        hilang = [label for label, field in KOLOM_KOMPONEN if kolom[field] is None] + ([] if kolom_cicilan else ["cicilan"])
        raise ImporBiodataError(f"Kolom berikut tidak ditemukan di tab master: {', '.join(hilang)}.")

    hasil = []
    for i, row in enumerate(rows[mulai:], start=mulai):
        ambil = lambda j: row[j].strip() if j is not None and j < len(row) else ""  # noqa: E731
        nama = ambil(kolom_nama)
        if not re.search(r"[^\W\d_]", nama) or not ambil(kolom_nama - 1).isdigit():
            continue  # baris rekap atau kosong
        hasil.append({
            "baris": i + 1,
            "nama": " ".join(nama.split()),
            "kelas": ambil(kolom_kelas),
            "kategori": ambil(kolom_kategori).upper(),
            "diskon": _rupiah(ambil(kolom_diskon).lstrip("-")) or 0,
            "komponen": {field: _rupiah(ambil(j)) for field, j in kolom.items()},
            "netto_berkas": _rupiah(ambil(kolom_netto)),
            "lunas_berkas": _rupiah(ambil(kolom_lunas)),
            "terbayar": sum((_rupiah(ambil(j)) or 0) for j in kolom_cicilan),
        })
    if not hasil:
        raise ImporBiodataError("Tidak ada baris siswa bernomor urut di berkas ini.")
    return hasil


def susun(baris_mentah, siswa_qs):
    """Cocokkan baris berkas dengan siswa dan periksa angkanya. Tidak menyimpan apa pun.

    aksi: isi, sudah (saldo awal sudah tercatat), lewati (tanpa biaya masuk), cek, galat.
    """
    from operations.models import PembayaranTagihan, Siswa

    kategori_valid = {kode for kode, _label in Siswa.DISKON_KATEGORI}
    per_nama = {}
    for siswa in siswa_qs:
        per_nama.setdefault(kunci_nama(siswa.nama), []).append(siswa)
    kembar = Counter(kunci_nama(r["nama"]) for r in baris_mentah)
    sudah_dibayar = dict(
        PembayaranTagihan.objects.filter(tagihan__jenis="BIAYA_MASUK", tagihan__is_deleted=False, dibatalkan=False)
        .values_list("tagihan__siswa_id", "saldo_awal")
    )

    hasil = []
    for mentah in baris_mentah:
        kunci = kunci_nama(mentah["nama"])
        cocok = per_nama.get(kunci, [])
        bruto = sum((v or 0) for v in mentah["komponen"].values())
        netto = bruto - mentah["diskon"]
        item = {
            "baris": mentah["baris"], "nama": mentah["nama"], "kelas": mentah["kelas"],
            "siswa": cocok[0].pk if len(cocok) == 1 else None,
            "kategori": mentah["kategori"], "diskon": mentah["diskon"],
            "komponen": mentah["komponen"], "ditagih": netto, "terbayar": mentah["terbayar"],
            "aksi": "isi", "alasan": None,
        }
        siswa_id = item["siswa"]
        if kembar[kunci] > 1:
            item["aksi"], item["alasan"] = "galat", "Nama ini muncul lebih dari sekali di berkas."
        elif not cocok:
            item["aksi"], item["alasan"] = "galat", "Siswa tidak ditemukan di sistem. Impor biodata dulu."
        elif len(cocok) > 1:
            item["aksi"], item["alasan"] = "galat", "Ada lebih dari satu siswa bernama sama di sistem."
        elif siswa_id in sudah_dibayar:
            item["aksi"], item["alasan"] = (
                ("sudah", "Saldo awal biaya masuk sudah tercatat.") if sudah_dibayar[siswa_id]
                else ("cek", "Sudah ada penerimaan biaya masuk di sistem. Cocokkan manual.")
            )
        elif bruto == 0 and not mentah["terbayar"]:
            item["aksi"], item["alasan"] = "lewati", "Tidak ada biaya masuk di berkas."
        elif mentah["kategori"] not in TANPA_DISKON and mentah["kategori"] not in kategori_valid:
            item["aksi"], item["alasan"] = "cek", f"Kategori diskon {mentah['kategori']} tidak dikenal sistem."
        elif netto < 0:
            item["aksi"], item["alasan"] = "cek", "Diskon melebihi total biaya masuk."
        elif mentah["netto_berkas"] is not None and mentah["netto_berkas"] != netto:
            item["aksi"], item["alasan"] = "cek", "Jumlah setelah diskon di berkas tidak sama dengan hitungan komponen."
        elif mentah["terbayar"] > netto:
            item["aksi"], item["alasan"] = "cek", "Total cicilan melebihi biaya masuk setelah diskon."
        elif mentah["lunas_berkas"] is not None and mentah["lunas_berkas"] != mentah["terbayar"]:
            item["aksi"], item["alasan"] = "cek", "Kolom total dibayar tidak sama dengan jumlah cicilan."
        hasil.append(item)
    return hasil


def awal_tp(tanggal):
    """Periode tagihan biaya masuk impor: Juli awal tahun pelajaran tanggal saldo awal."""
    return 7, tanggal.year if tanggal.month >= 7 else tanggal.year - 1


def terapkan(hasil, *, tanggal, user=None, simpan=False):
    """Isi biaya masuk + saldo awal untuk baris 'isi'. Tanpa simpan, transaksi dibatalkan di akhir.

    Baris yang ditolak aturan tagihan diubah menjadi 'cek' dengan alasannya. Mengembalikan jumlah baris diisi.
    """
    from operations.models import Siswa, Tagihan

    from .biaya_masuk import sinkron_tagihan_biaya_masuk
    from .billing import catat_saldo_awal_tagihan

    diisi = 0
    with transaction.atomic(), audit_user(user):
        for item in hasil:
            if item["aksi"] != "isi":
                continue
            try:
                with transaction.atomic():
                    siswa = Siswa.objects.select_for_update().get(pk=item["siswa"])
                    for field, nilai in item["komponen"].items():
                        setattr(siswa, field, Decimal(nilai) if nilai else None)
                    siswa.diskon_nominal = Decimal(item["diskon"])
                    siswa.diskon_kategori = [] if item["kategori"] in TANPA_DISKON else [item["kategori"]]
                    siswa._change_reason = CHANGE_REASON
                    siswa.save()
                    tagihan = sinkron_tagihan_biaya_masuk(siswa, user=user, periode=awal_tp(tanggal))
                    if item["terbayar"] and tagihan:
                        tagihan = Tagihan.objects.get(pk=tagihan.pk)
                        catat_saldo_awal_tagihan(tagihan, tanggal=tanggal, nominal=Decimal(item["terbayar"]), user=user)
            except ValueError as exc:
                item["aksi"], item["alasan"] = "cek", str(exc)
                continue
            diisi += 1
        if not simpan:
            transaction.set_rollback(True)
    return diisi


def ringkas(hasil):
    hitung = {aksi: 0 for aksi in ("isi", "sudah", "lewati", "cek", "galat")}
    for item in hasil:
        hitung[item["aksi"]] += 1
    hitung["total_ditagih"] = sum(i["ditagih"] for i in hasil if i["aksi"] == "isi")
    hitung["total_terbayar"] = sum(i["terbayar"] for i in hasil if i["aksi"] == "isi")
    return hitung
