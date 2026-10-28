"""Impor biodata siswa dari CSV rekap kelas (format spreadsheet sekolah).

Kolom dikenali dari judulnya: Kelas, No., Nama Siswa, JK, Tempat, Tanggal Lahir, Alamat,
Nama Ayah + No. Tlp, Nama Bunda/Ibu + No. Tlp. Kolom Usia diabaikan (dihitung dari tanggal lahir).
Baris siswa ditandai nomor urut di kolom No.; baris rekap dan judul ulang dilewati.
"""

import csv
import io
import re
from datetime import date

from django.db import transaction
from django.utils import timezone

from .common import audit_user

MAKS_UKURAN = 1024 * 1024
BIODATA_FIELDS = [
    "nama", "jenis_kelamin", "tempat_lahir", "tanggal_lahir", "alamat",
    "nama_ayah", "kontak_ayah", "nama_ibu", "kontak_ibu",
]
CHANGE_REASON = "Impor biodata CSV"

_BULAN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
    "agu": 8, "agt": 8, "ags": 8, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12,
}
# Singkatan yang tetap huruf besar saat alamat dirapikan.
_SINGKATAN = {"RT", "RW", "TNI", "POLRI", "DKI", "KPR", "BTN", "PLN", "PT", "SD", "SMP", "SMA", "UI", "BSD", "II", "III", "IV"}


class ImporBiodataError(ValueError):
    pass


def kunci_nama(nama):
    """Kunci pencocokan nama: tanpa beda huruf besar/kecil dan spasi ganda."""
    return " ".join((nama or "").split()).casefold()


def _bersih(teks):
    return " ".join((teks or "").split())


def parse_tanggal(teks):
    """'24-Nov-21', '4-Agu-21', '24/11/2021', '2021-11-24' -> date. Kosong -> None."""
    teks = _bersih(teks)
    if not teks:
        return None
    m = re.fullmatch(r"(\d{1,2})[-/ .]([A-Za-z]{3,})[-/ .](\d{2}|\d{4})", teks)
    if m:
        bulan = _BULAN.get(m.group(2)[:3].lower())
        if not bulan:
            raise ValueError(f"Bulan '{m.group(2)}' tidak dikenali.")
        hari, tahun = int(m.group(1)), int(m.group(3))
    elif angka := re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", teks):
        hari, bulan, tahun = int(angka.group(1)), int(angka.group(2)), int(angka.group(3))
    elif iso := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", teks):
        tahun, bulan, hari = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
    else:
        raise ValueError(f"Format tanggal lahir '{teks}' tidak dikenali.")
    if tahun < 100:
        tahun += 2000
    try:
        return date(tahun, bulan, hari)
    except ValueError:
        raise ValueError(f"Tanggal lahir '{teks}' tidak valid.") from None


def rapikan_telepon(teks):
    """Sisakan angka; awalan 62/+62 menjadi 0. Kembalikan (nomor, peringatan)."""
    teks = _bersih(teks)
    if not teks:
        return None, None
    angka = re.sub(r"\D", "", teks)
    if angka.startswith("62"):
        angka = "0" + angka[2:]
    elif angka.startswith("8") and 9 <= len(angka) <= 12:
        angka = "0" + angka  # spreadsheet membuang 0 di depan nomor yang tersimpan sebagai angka
    if not angka:
        return None, f"Nomor '{teks}' tidak berisi angka."
    peringatan = None
    if re.search(r"[^\d\s+().-]", teks) or not angka.startswith("0") or not 10 <= len(angka) <= 13:
        peringatan = f"Nomor '{teks}' perlu dicek (hasil {angka})."
    return angka[:20], peringatan


def parse_jenis_kelamin(teks):
    teks = _bersih(teks).casefold()
    if not teks:
        return None
    if teks in ("l", "laki-laki", "laki laki", "lk"):
        return "L"
    if teks in ("p", "perempuan", "pr"):
        return "P"
    raise ValueError(f"Jenis kelamin '{teks}' harus L atau P.")


def _rapikan_kata(kata):
    inti = kata.strip(".,")
    if not inti or not re.search(r"[A-Za-z]", inti):
        return kata
    if inti.upper() in _SINGKATAN:
        return kata.replace(inti, inti.upper())
    if re.fullmatch(r"[A-Za-z]\d+[A-Za-z]?", inti):  # nomor blok: c6 -> C6
        return kata.replace(inti, inti.upper())
    if re.search(r"\d", inti) or (inti != inti.lower() and inti != inti.upper()):
        return kata  # campuran huruf/angka atau sudah huruf campuran: biarkan
    return kata.replace(inti, inti[:1].upper() + inti[1:].lower())


def rapikan_alamat(teks):
    """Seragamkan penulisan alamat: Jl., Gg., No., RT 004/RW 003, Kel., Kec., koma, dan kapitalisasi."""
    s = _bersih(teks)
    if not s:
        return None
    s = re.sub(r"\s*,[\s,]*", ", ", s).strip(" ,")
    s = re.sub(r"\b(?:jalan|jln|jl)\b\.?\s*", "Jl. ", s, flags=re.I)
    s = re.sub(r"\b(?:gang|gg)\b\.?\s*", "Gg. ", s, flags=re.I)
    s = re.sub(r"\b(?:kelurahan|kel)\b\.?\s*", "Kel. ", s, flags=re.I)
    s = re.sub(r"\b(?:kecamatan|kec)\b\.?\s*", "Kec. ", s, flags=re.I)
    s = re.sub(r"\b(?:nomor|no)\b\.?\s*(?=\d)", "No. ", s, flags=re.I)
    s = re.sub(
        r"\brt\.?\s*0*(\d{1,3})\s*[/,.]?\s*rw\.?\s*0*(\d{1,3})\b",
        lambda m: f"RT {int(m.group(1)):03d}/RW {int(m.group(2)):03d}", s, flags=re.I,
    )
    s = re.sub(r"\brt\.?\s*0*(\d{1,3})\b", lambda m: f"RT {int(m.group(1)):03d}", s, flags=re.I)
    s = re.sub(r"\brw\.?\s*0*(\d{1,3})\b", lambda m: f"RW {int(m.group(1)):03d}", s, flags=re.I)
    s = " ".join(_rapikan_kata(k) for k in s.split())
    return s


def _cari_kolom(header, sub):
    """Peta nama kolom -> indeks dari baris judul dan sub-judul (Orang Tua: Ayah/Bunda)."""
    kolom = {}
    for idx, judul in enumerate(header):
        j = _bersih(judul).casefold()
        if j == "kelas":
            kolom["kelas"] = idx
        elif j.rstrip(".") == "no":
            kolom["no"] = idx
        elif j in ("nama siswa", "nama"):
            kolom["nama"] = idx
        elif j in ("jk", "l/p", "jenis kelamin"):
            kolom["jenis_kelamin"] = idx
        elif j in ("tempat", "tempat lahir"):
            kolom["tempat_lahir"] = idx
        elif j == "tanggal lahir":
            kolom["tanggal_lahir"] = idx
        elif j == "alamat":
            kolom["alamat"] = idx
    telepon_untuk = None
    for idx, judul in enumerate(sub):
        j = _bersih(judul).casefold()
        if j == "nama ayah":
            kolom["nama_ayah"], telepon_untuk = idx, "kontak_ayah"
        elif j in ("nama bunda", "nama ibu"):
            kolom["nama_ibu"], telepon_untuk = idx, "kontak_ibu"
        elif j.startswith("no") and ("tlp" in j or "telp" in j or "hp" in j) and telepon_untuk:
            kolom[telepon_untuk], telepon_untuk = idx, None
    return kolom


def parse_csv(berkas):
    """Baca CSV menjadi baris biodata. Tiap baris: dict nilai mentah + nomor baris sumber."""
    data = berkas.read(MAKS_UKURAN + 1)
    if len(data) > MAKS_UKURAN:
        raise ImporBiodataError("Berkas lebih dari 1 MB. Unduh hanya tab biodata sebagai CSV.")
    try:
        teks = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        teks = data.decode("cp1252")
    try:
        delimiter = csv.Sniffer().sniff(teks[:4096], delimiters=",;\t").delimiter
    except csv.Error:
        delimiter = ","
    rows = [[_bersih(c) for c in r] for r in csv.reader(io.StringIO(teks), delimiter=delimiter)]

    hasil, kolom, kelas = [], None, ""
    for i, row in enumerate(rows):
        lower = [c.casefold() for c in row]
        if "nama siswa" in lower:
            sub = rows[i + 1] if i + 1 < len(rows) else []
            kolom = _cari_kolom(row, sub)
            kelas = ""
            continue
        if kolom is None:
            continue
        ambil = lambda key: row[kolom[key]] if key in kolom and kolom[key] < len(row) else ""  # noqa: E731
        if not re.search(r"[^\W\d_]", ambil("nama")):
            continue  # baris rekap (mis. "Laki-laki | 54") atau kosong; jangan ganti kelas
        if ambil("kelas"):
            kelas = ambil("kelas")
        if not ambil("no").isdigit() or not ambil("nama"):
            continue  # baris rekap, sub-judul, atau kosong
        hasil.append({
            "baris": i + 1, "kelas": kelas,
            **{key: ambil(key) for key in ("nama", *BIODATA_FIELDS[1:])},
        })
    if kolom is None:
        raise ImporBiodataError("Judul kolom 'Nama Siswa' tidak ditemukan. Pastikan tab biodata yang diunduh.")
    wajib = {"nama", "kelas", "no"} - set(kolom)
    if wajib:
        raise ImporBiodataError(f"Kolom wajib tidak ditemukan: {', '.join(sorted(wajib))}.")
    if not hasil:
        raise ImporBiodataError("Tidak ada baris siswa bernomor urut di berkas ini.")
    return hasil


def _normalisasi(mentah, today):
    """Baris mentah -> (nilai bersih, peringatan, galat)."""
    nilai: dict[str, object] = {"nama": _bersih(mentah["nama"])}
    peringatan: list[str] = []
    try:
        nilai["jenis_kelamin"] = parse_jenis_kelamin(mentah["jenis_kelamin"])
        nilai["tanggal_lahir"] = parse_tanggal(mentah["tanggal_lahir"])
    except ValueError as exc:
        return nilai, peringatan, str(exc)
    if nilai["tanggal_lahir"] and nilai["tanggal_lahir"] > today:
        return nilai, peringatan, "Tanggal lahir di masa depan."
    nilai["tempat_lahir"] = _bersih(mentah["tempat_lahir"]).title() or None
    nilai["alamat"] = rapikan_alamat(mentah["alamat"])
    nilai["nama_ayah"] = _bersih(mentah["nama_ayah"]) or None
    nilai["nama_ibu"] = _bersih(mentah["nama_ibu"]) or None
    for field, label in (("nama", "Nama siswa"), ("tempat_lahir", "Tempat lahir"), ("nama_ayah", "Nama ayah"), ("nama_ibu", "Nama ibu")):
        if len(str(nilai.get(field) or "")) > 100:
            return nilai, peringatan, f"{label} lebih dari 100 karakter."
    for field in ("kontak_ayah", "kontak_ibu"):
        nilai[field], catatan = rapikan_telepon(mentah[field])
        if catatan:
            peringatan.append(catatan)
    for field in BIODATA_FIELDS:
        if field != "nama" and not nilai.get(field):
            nilai.pop(field, None)  # sel kosong tidak menghapus data lama
    return nilai, peringatan, None


def _tampil(value):
    return value.isoformat() if isinstance(value, date) else value


def susun_impor(baris_mentah, kelas_map, siswa_qs, today=None):
    """Bandingkan baris CSV dengan siswa yang ada. Tidak menyimpan apa pun.

    kelas_map: {nilai Kelas di CSV: id kelompok atau None (kelompok tidak diubah)}.
    """
    today = today or timezone.localdate()
    per_nama = {}
    for siswa in siswa_qs:
        per_nama.setdefault(kunci_nama(siswa.nama), []).append(siswa)
    kembar = {}
    for mentah in baris_mentah:
        kembar[kunci_nama(mentah["nama"])] = kembar.get(kunci_nama(mentah["nama"]), 0) + 1

    hasil = []
    for mentah in baris_mentah:
        nilai, peringatan, galat = _normalisasi(mentah, today)
        kunci = kunci_nama(nilai["nama"])
        cocok = per_nama.get(kunci, [])
        if not galat and kembar[kunci] > 1:
            galat = "Nama ini muncul lebih dari sekali di berkas."
        if not galat and len(cocok) > 1:
            galat = "Ada lebih dari satu siswa bernama sama di sistem. Ubah satu per satu lewat form."
        kelompok = kelas_map.get(mentah["kelas"])
        if kelompok is not None:
            nilai["kelompok"] = kelompok
        item = {
            "baris": mentah["baris"], "kelas": mentah["kelas"], "nama": nilai["nama"],
            "siswa": cocok[0].pk if len(cocok) == 1 else None, "peringatan": peringatan, "galat": galat,
            "perubahan": {}, "nilai": {k: _tampil(v) for k, v in nilai.items()},
        }
        if galat:
            item["aksi"] = "galat"
        elif len(cocok) == 1:
            siswa = cocok[0]
            nilai.pop("nama")  # cocok lewat nama; penulisan nama di sistem dipertahankan
            for field, baru in nilai.items():
                lama = siswa.kelompok_id if field == "kelompok" else getattr(siswa, field)
                if lama != baru:
                    item["perubahan"][field] = [_tampil(lama), _tampil(baru)]
            item["aksi"] = "ubah" if item["perubahan"] else "sama"
        else:
            item["aksi"] = "baru"
        item["_nilai"] = nilai
        hasil.append(item)
    return hasil


def terapkan_impor(hasil, user=None):
    """Simpan baris baru/ubah dalam satu transaksi. Baris galat dan sama dilewati."""
    from operations.models import Siswa

    dibuat, diubah = 0, 0
    with transaction.atomic(), audit_user(user):
        for item in hasil:
            if item["aksi"] == "baru":
                siswa = Siswa(status="aktif", spp_nominal=0)
                dibuat += 1
            elif item["aksi"] == "ubah":
                siswa = Siswa.objects.select_for_update().get(pk=item["siswa"], is_deleted=False)
                diubah += 1
            else:
                continue
            for field, value in item["_nilai"].items():
                setattr(siswa, "kelompok_id" if field == "kelompok" else field, value)
            siswa._change_reason = CHANGE_REASON
            siswa.save()
            item["siswa"] = siswa.pk
    return {"dibuat": dibuat, "diubah": diubah}


def ringkas(hasil):
    hitung = {aksi: 0 for aksi in ("baru", "ubah", "sama", "galat")}
    for item in hasil:
        hitung[item["aksi"]] += 1
    hitung["peringatan"] = sum(1 for item in hasil if item["peringatan"])
    return hitung
