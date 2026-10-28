import type { BiayaMasukField, DiskonKategori, JenisKelamin, Kelompok, Siswa, SiswaStatus } from "@/types/api"

export const SISWA_STATUS = {
  aktif: { label: "Aktif", severity: "success" },
  lulus: { label: "Lulus", severity: "secondary" },
  cuti: { label: "Cuti", severity: "warn" },
  pindah: { label: "Pindah", severity: "secondary" },
  mengulang: { label: "Mengulang kelas", severity: "info" },
  naik: { label: "Naik kelas", severity: "info" },
} as const satisfies Record<SiswaStatus, { label: string; severity: string }>

export const JENIS_KELAMIN = { L: "Laki-laki", P: "Perempuan" } as const satisfies Record<JenisKelamin, string>
export const jenisKelaminOptions = Object.entries(JENIS_KELAMIN).map(([value, label]) => ({ value, label }))

/** Baris kedua nama siswa: panggilan, jenis kelamin, NIS. */
export function identitasSiswa(row: Pick<Siswa, "nama_panggilan" | "jenis_kelamin" | "nis">) {
  return [
    row.nama_panggilan ? `Panggilan ${row.nama_panggilan}` : null,
    row.jenis_kelamin ? JENIS_KELAMIN[row.jenis_kelamin] : null,
    row.nis ? `NIS ${row.nis}` : "NIS belum diisi",
  ].filter(Boolean).join(" · ")
}

export const statusOptions = Object.entries(SISWA_STATUS).map(([value, state]) => ({ value, label: state.label }))
export function kelompokLabel(kelompok: Kelompok) {
  return [kelompok.jenjang_kode, kelompok.nama].filter(Boolean).join(" · ")
}

export const DISKON_KATEGORI: DiskonKategori[] = ["PG", "SIPG", "SIB", "SIKBR"]
/** Urutan ini juga urutan pemotongan diskon di backend. */
export const BIAYA_MASUK_FIELDS: { field: BiayaMasukField; label: string }[] = [
  { field: "uang_masuk", label: "Uang Masuk" },
  { field: "uang_pengembangan", label: "Uang Pengembangan" },
  { field: "uang_kegiatan", label: "Uang Kegiatan" },
  { field: "uang_seragam", label: "Uang Seragam" },
]
export function biayaMasukBruto(form: Partial<Record<BiayaMasukField, string | null>>) {
  return BIAYA_MASUK_FIELDS.reduce((sum, { field }) => sum + Number(form[field] || 0), 0)
}
export function biayaMasukState(row: Siswa) {
  if (!row.biaya_masuk) return null
  if (row.biaya_masuk.status === "LUNAS") return { label: "Lunas", severity: "success" }
  if (row.biaya_masuk.status === "SEBAGIAN") return { label: "Sebagian", severity: "warn" }
  return { label: "Belum dibayar", severity: "danger" }
}
export function canReceiveBiayaMasuk(row: Siswa) {
  return Boolean(row.biaya_masuk && Number(row.biaya_masuk.sisa) > 0)
}
