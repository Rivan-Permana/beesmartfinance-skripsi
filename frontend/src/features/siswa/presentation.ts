import { formatRp } from "@/core/format"
import type { BiayaMasukField, DiskonKategori, ImporBiayaMasukBaris, JenisKelamin, KelengkapanKode, Kelompok, Siswa, SiswaStatus } from "@/types/api"

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

/** Usia dari tanggal lahir (YYYY-MM-DD), mis. "4 tahun 11 bulan". Tidak disimpan agar tidak basi. */
export function usiaSiswa(tanggalLahir: string | Date | null | undefined, today = new Date()) {
  if (!tanggalLahir) return null
  const lahir = typeof tanggalLahir === "string" ? new Date(tanggalLahir + "T12:00:00") : tanggalLahir
  if (!Number.isFinite(lahir.getTime()) || lahir > today) return null
  let bulan = (today.getFullYear() - lahir.getFullYear()) * 12 + today.getMonth() - lahir.getMonth()
  if (today.getDate() < lahir.getDate()) bulan -= 1
  const tahun = Math.floor(bulan / 12)
  return tahun ? `${tahun} tahun ${bulan % 12} bulan` : `${bulan} bulan`
}

/** Baris kedua nama siswa: panggilan, jenis kelamin, usia, NIS. */
export function identitasSiswa(row: Pick<Siswa, "nama_panggilan" | "jenis_kelamin" | "nis" | "tanggal_lahir">, today = new Date()) {
  return [
    row.nama_panggilan ? `Panggilan ${row.nama_panggilan}` : null,
    row.jenis_kelamin ? JENIS_KELAMIN[row.jenis_kelamin] : null,
    usiaSiswa(row.tanggal_lahir, today),
    row.nis ? `NIS ${row.nis}` : "NIS belum diisi",
  ].filter(Boolean).join(" · ")
}

export const statusOptions = Object.entries(SISWA_STATUS).map(([value, state]) => ({ value, label: state.label }))
export function kelompokLabel(kelompok: Kelompok) {
  return [kelompok.jenjang_kode, kelompok.nama].filter(Boolean).join(" · ")
}

export const DISKON_KATEGORI: DiskonKategori[] = ["PG", "SIPG", "SIB", "SIKBR", "SBD", "KHUSUS", "PINDAHAN"]
/** Urutan ini juga urutan pemotongan diskon di backend. `perAnak`: kosong = ikut daftar harga di tagihan Juli. */
export const BIAYA_MASUK_FIELDS: { field: BiayaMasukField; label: string; perAnak?: boolean }[] = [
  { field: "uang_masuk", label: "Uang Masuk" },
  { field: "uang_pengembangan", label: "Uang Pengembangan" },
  { field: "uang_kegiatan", label: "Uang Kegiatan" },
  { field: "uang_seragam", label: "Uang Seragam" },
  { field: "uang_komite", label: "Iuran Komite", perAnak: true },
  { field: "uang_portofolio", label: "Portofolio", perAnak: true },
]
/** Komponen yang diisi otomatis oleh tombol "Isi dari daftar harga". */
export const BIAYA_MASUK_PREFILL = BIAYA_MASUK_FIELDS.filter((item) => !item.perAnak)
export function biayaMasukBruto(form: Partial<Record<BiayaMasukField, string | null>>) {
  return BIAYA_MASUK_FIELDS.reduce((sum, { field }) => sum + Number(form[field] || 0), 0)
}
export function biayaMasukState(row: Siswa) {
  if (!row.biaya_masuk) return null
  if (row.biaya_masuk.status === "LUNAS") return { label: "Lunas", severity: "success" }
  if (row.biaya_masuk.status === "SEBAGIAN") return { label: "Sebagian", severity: "warn" }
  return { label: "Belum dibayar", severity: "danger" }
}
/** Siswa aktif dengan SPP 0, mis. hasil impor biodata yang belum diberi tarif. */
export function sppBelumDiisi(row: Pick<Siswa, "status" | "spp_nominal">) {
  return row.status === "aktif" && !(Number(row.spp_nominal) > 0)
}
export function canReceiveBiayaMasuk(row: Siswa) {
  return Boolean(row.biaya_masuk && Number(row.biaya_masuk.sisa) > 0)
}

export const KELENGKAPAN_LABEL = {
  spp_kosong: "SPP belum diisi",
  spp_janggal: "SPP di luar kisaran",
  tanpa_kelompok: "Tanpa kelompok",
  kontak_kosong: "HP orang tua kosong",
  hp_janggal: "HP perlu dicek",
} as const satisfies Record<KelengkapanKode, string>

/** Default tanggal saldo awal impor cut-over: hari terakhir bulan lalu (1 Januari -> 31 Desember). */
export function tanggalSaldoAwalDefault(today = new Date()) {
  return new Date(today.getFullYear(), today.getMonth(), 0)
}
export function imporBiayaMasukDetail(row: ImporBiayaMasukBaris) {
  if (row.aksi === "galat" || row.aksi === "lewati") return row.alasan ?? ""
  const angka = `Ditagihkan ${formatRp(row.ditagih)} · terbayar ${formatRp(row.terbayar)} · sisa ${formatRp(row.ditagih - row.terbayar)}`
  const diskon = row.diskon ? ` · diskon ${row.kategori} ${formatRp(row.diskon)}` : ""
  return row.aksi === "isi" ? angka + diskon : `${row.alasan ?? ""} ${angka}${diskon}`
}
