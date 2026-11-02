"""Daftar siswa aktif yang datanya perlu dilengkapi Staf TU. Hanya membaca."""

from collections import defaultdict
from decimal import Decimal
from statistics import median

from operations.models import Siswa

from .impor_biodata import rapikan_telepon

# SPP dianggap di luar kisaran bila kurang dari separuh atau lebih dari 1,5x median jenjangnya.
BATAS_BAWAH = Decimal("0.5")
BATAS_ATAS = Decimal("1.5")
MIN_SAMPEL_MEDIAN = 3

MASALAH = {
    "spp_kosong": "SPP belum diisi",
    "spp_janggal": "SPP di luar kisaran jenjang",
    "tanpa_kelompok": "Belum punya kelompok",
    "kontak_kosong": "Nomor HP orang tua kosong",
    "hp_janggal": "Nomor HP perlu dicek",
}


def siswa_perlu_dilengkapi():
    siswa_list = list(Siswa.objects.filter(status="aktif").select_related("kelompok__jenjang").order_by("nama"))
    spp_per_jenjang = defaultdict(list)
    for s in siswa_list:
        if s.kelompok_id and s.spp_nominal > 0:
            spp_per_jenjang[s.kelompok.jenjang_id].append(s.spp_nominal)
    median_jenjang = {
        jenjang: median(nilai) for jenjang, nilai in spp_per_jenjang.items() if len(nilai) >= MIN_SAMPEL_MEDIAN
    }

    baris = []
    ringkasan = dict.fromkeys(MASALAH, 0)
    for s in siswa_list:
        masalah = []
        acuan = median_jenjang.get(s.kelompok.jenjang_id) if s.kelompok_id else None
        if s.spp_nominal <= 0:
            masalah.append(("spp_kosong", MASALAH["spp_kosong"]))
        elif acuan and not acuan * BATAS_BAWAH <= s.spp_nominal <= acuan * BATAS_ATAS:
            masalah.append(("spp_janggal", MASALAH["spp_janggal"]))
        if not s.kelompok_id:
            masalah.append(("tanpa_kelompok", MASALAH["tanpa_kelompok"]))
        if not (s.kontak_ayah or "").strip() and not (s.kontak_ibu or "").strip():
            masalah.append(("kontak_kosong", MASALAH["kontak_kosong"]))
        for label, nomor in (("ayah", s.kontak_ayah), ("ibu", s.kontak_ibu)):
            if nomor and rapikan_telepon(nomor)[1]:
                masalah.append(("hp_janggal", f"Nomor HP {label} perlu dicek"))
        if not masalah:
            continue
        for kode in {kode for kode, _ in masalah}:
            ringkasan[kode] += 1
        baris.append({
            "id": s.id,
            "nama": s.nama,
            "nis": s.nis,
            "kelompok": str(s.kelompok) if s.kelompok_id else None,
            "spp_nominal": s.spp_nominal,
            "spp_acuan": acuan,
            "masalah": [{"kode": kode, "pesan": pesan} for kode, pesan in masalah],
        })
    return {"total_siswa": len(siswa_list), "ringkasan": ringkasan, "baris": baris}
