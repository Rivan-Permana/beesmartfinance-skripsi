import type { AnggaranBulananAkun } from "@/types/api"

export const NAMA_BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

export function bulanLabel(bulan: number, tahun: number) {
  return `${NAMA_BULAN[bulan - 1]} ${tahun}`
}

/** Anggaran dan realisasi satu bulan (indeks dalam tahun pelajaran) untuk satu akun. */
export function pemakaianBulan(akun: AnggaranBulananAkun, index: number) {
  const bulan = akun.bulan[index]
  return {
    anggaranBulan: bulan?.anggaran == null ? null : Number(bulan.anggaran),
    realisasiBulan: Number(bulan?.realisasi ?? 0),
  }
}

/** "lebih" bila realisasi melewati anggaran bulan itu; tanpa anggaran tidak dinilai. */
export function statusRealisasi(anggaran: number | null, realisasi: number): "lebih" | "aman" | "tanpa" {
  if (anggaran == null) return "tanpa"
  return realisasi > anggaran ? "lebih" : "aman"
}
