// Tipe domain inti (selaras backend /api/v1).
// Catatan: ke depan bisa di-generate otomatis dari OpenAPI (/api/schema)
// memakai openapi-typescript agar 100% sinkron.

export interface TokenPair {
  access: string
  refresh: string
}

export type Role =
  | "Finance"
  | "SchoolPrincipal"
  | "Administration"
  | "TeacherInCharge"

export interface CurrentUser {
  id: number
  username: string
  nama: string
  is_superuser: boolean
  groups: Role[]
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type SiswaStatus =
  | "aktif" | "lulus" | "cuti" | "pindah" | "mengulang" | "naik"

export interface Siswa {
  id: number
  nis: string | null
  nama: string
  kelompok: number | null
  tanggal_lahir: string | null
  alamat: string | null
  nama_ayah: string | null
  kontak_ayah: string | null
  nama_ibu: string | null
  kontak_ibu: string | null
  spp_nominal: string
  status: SiswaStatus
  periode: number | null
}

export type SiswaInput = Omit<Siswa, "id">

// --- Accounting ---
export interface Coa {
  kode_akun: string
  nama_akun: string
  posisi_normal: "D" | "K"
  is_active: boolean
}

export type JurnalStatus = "DRAFT" | "PENDING" | "POSTED" | "VOID"

export interface JurnalDetail {
  id?: number
  kode_akun: string
  debit: string
  kredit: string
}

export interface Jurnal {
  id: string
  no_bukti: string
  tanggal: string
  keterangan: string | null
  tipe_sumber: string
  status: JurnalStatus
  created_by: number | null
  approved_by: number | null
  posted_at: string | null
  is_deleted: boolean
  detail: JurnalDetail[]
}

export interface JurnalInput {
  no_bukti: string
  tanggal: string
  keterangan?: string
  detail: { kode_akun: string; debit: string; kredit: string }[]
}

export type TagihanStatus = "BELUM" | "SEBAGIAN" | "LUNAS"

export interface TagihanDetail {
  id?: number
  komponen: "SPP" | "KATERING" | "JEMPUTAN" | "LAIN"
  akun_pendapatan: string
  nominal: string
}

export interface Tagihan {
  id: number
  siswa: number
  periode_bulan: number
  periode_tahun: number
  total: string
  status: TagihanStatus
  jurnal: string | null
  detail: TagihanDetail[]
}

export interface StrukTagihan {
  no_tagihan: number
  siswa: string
  nis: string | null
  periode: string
  status: TagihanStatus
  rincian: { komponen: string; nominal: string }[]
  total: string
  no_jurnal: string | null
}

// --- Kepegawaian ---
export interface Pegawai {
  id: number
  nip: string | null
  nama: string
  jabatan: string | null
  nomor_hp: string | null
  alamat: string | null
  status_aktif: boolean
  user: number | null
}
export type PegawaiInput = Omit<Pegawai, "id">

export interface Gaji {
  id: number
  pegawai: number
  periode_bulan: number
  periode_tahun: number
  gaji_pokok: string
  tunjangan_jabatan: string
  tunjangan_pengabdian: string
  transport: string
  bonus_insentif: string
  thr: string
  potongan_pinjaman: string
  potongan_asuransi: string
  total_bruto: string
  total_netto: string
  jurnal: string | null
}

export interface Pinjaman {
  id: number
  pegawai: number
  tanggal_pinjaman: string
  jumlah_pinjaman: string
  tenor_bulan: number
  angsuran_per_bulan: string
  sudah_terbayar: string
  sisa_pinjaman: string
  jurnal: string | null
}

// --- Aset & Kegiatan ---
export interface FixedAsset {
  id: number
  nama: string
  akun_aset: string
  akun_akumulasi: string
  akun_beban_depr: string
  tanggal_perolehan: string
  harga_perolehan: string
  umur_manfaat_bulan: number
  metode: "garis_lurus"
  akumulasi_penyusutan: string
  penyusutan_per_bulan: string
}

export type KegiatanStatus = "RENCANA" | "BERJALAN" | "SELESAI"

export interface Kegiatan {
  id: number
  nama: string
  akun_beban: string
  pagu: string
  penanggung_jawab: number | null
  tanggal_mulai: string | null
  tanggal_selesai: string | null
  status: KegiatanStatus
  realisasi: string
  sisa_pagu: string
  rasio_utilisasi: number
}

export interface LaporanKegiatan {
  kegiatan: string
  pagu: string
  realisasi: string
  sisa_pagu: string
  rasio_utilisasi: number
  rincian: { tanggal: string; deskripsi: string; nominal: string }[]
}

// --- Laporan ---
export interface SaldoRow {
  kode_akun: string
  nama_akun: string
  posisi_normal: "D" | "K"
  total_debit: string
  total_kredit: string
  saldo_akhir: string
}

export interface LabaRugiResult {
  pendapatan: SaldoRow[]
  beban: SaldoRow[]
  total_pendapatan: string
  total_beban: string
  laba_rugi: string
}

export interface PosisiKeuanganResult {
  aset: SaldoRow[]
  liabilitas: SaldoRow[]
  ekuitas: SaldoRow[]
}

export interface RealisasiAnggaranRow {
  kode_akun: string
  nama_akun: string
  tahun_anggaran: number
  pagu: string
  realisasi: string
  sisa_pagu: string
}

export interface BukuBesarRow {
  no_bukti: string
  tanggal: string
  keterangan: string | null
  debit: string
  kredit: string
}

// --- Anggaran & Periode ---
export interface Anggaran {
  id: number
  kode_akun: string
  tahun_anggaran: number
  bulan: number | null
  nominal_anggaran: string
  keterangan: string | null
  carry_over: boolean
  periode: number | null
}

export interface PeriodeAkuntansi {
  id: number
  kode: string
  tgl_mulai: string
  tgl_selesai: string
  status: "OPEN" | "CLOSED"
}

export interface DashboardRingkasan {
  kas: string
  total_pendapatan: string
  total_beban: string
  surplus_defisit: string
  anggaran: { pagu: string | number; realisasi: string | number }
}

export interface LabaRugiBulananRow {
  bulan: number
  pendapatan: number
  beban: number
}
export interface LabaRugiBulananResult {
  tahun: number
  data: LabaRugiBulananRow[]
}

export interface PrediksiKasRow {
  periode: string
  tahun: number
  bulan: number
  arus_kas_masuk: string
  arus_kas_keluar: string
  net_cash_flow_bulanan: string
}
