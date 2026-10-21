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

export type PendaftaranSiswaStatus = "TRIAL" | "REGISTERED" | "BATAL"

export interface PendaftaranSiswa {
  id: number
  nama_calon: string
  jenjang: number | null
  tanggal_daftar: string
  biaya_sitin: string
  biaya_pendaftaran: string
  biaya_formulir: string | null
  total_biaya: string | null
  total_terbayar: string | null
  sisa_biaya: string | null
  perlu_rekonsiliasi: boolean
  sitin_terbayar: boolean | null
  formulir_terbayar: boolean | null
  pembayaran: {
    jurnal_id: string
    tanggal: string
    no_bukti: string
    nominal: string
    status: JurnalStatus
    dibatalkan: boolean
    komponen: ("SITIN" | "FORMULIR")[]
  }[]
  status: PendaftaranSiswaStatus
  siswa: number | null
  jurnal_sitin: string | null
  jurnal_pendaftaran: string | null
}

export type PendaftaranSiswaInput = Pick<
  PendaftaranSiswa,
  "nama_calon" | "jenjang" | "tanggal_daftar" | "biaya_sitin"
> & { biaya_formulir: string }

export interface BayarPendaftaranInput {
  komponen: ("SITIN" | "FORMULIR")[]
  tanggal: string
  no_bukti: string
  akun_kas: string
  nominal: string
}

export interface Jenjang {
  id: number
  kode: string
  nama: string
}

export interface Kelompok {
  id: number
  nama: string
  jenjang: number
  jenjang_kode?: string
  jenjang_nama?: string
  siswa_aktif?: number
}

export type KehadiranStatus = "hadir" | "izin" | "sakit" | "tidak_hadir"

export interface KehadiranSiswa {
  id: number
  siswa: number
  tanggal: string
  status: KehadiranStatus
  ikut_katering: boolean
  jemput_datang: boolean
  jemput_pulang: boolean
}

export type KehadiranSiswaInput = Omit<KehadiranSiswa, "id">

export interface MenuKatering {
  id: number
  tanggal: string
  gambar?: string | null
  gambar_url?: string | null
  keterangan?: string
}

export type MenuKateringInput = Omit<MenuKatering, "id" | "gambar">

export interface ArmadaJemputan {
  id: number
  nama_supir: string
  jenis_mobil?: string
  kapasitas?: number
  keterangan?: string
}

export type ArmadaJemputanInput = Omit<ArmadaJemputan, "id">

export interface PendaftaranJemputan {
  id: number
  siswa: number
  armada: number | null
  harga: string
}

export type PendaftaranJemputanInput = Omit<PendaftaranJemputan, "id">

// --- Accounting ---
export interface Golongan {
  id: number
  kode_golongan: string
  nama_golongan: string
  deskripsi?: string | null
}

export interface SubGolongan {
  id: number
  golongan: number
  kode_sub: string
  nama_sub: string
}

export interface Coa {
  kode_akun: string
  sub_golongan: string | null
  nama_akun: string
  posisi_normal: "D" | "K"
  is_active: boolean
  saldo_awal: string
  tanggal_saldo_awal: string | null
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
  can_finance_post: boolean
  perlu_rekonsiliasi: boolean
}

export interface JurnalInput {
  no_bukti: string
  tanggal: string
  keterangan?: string
  detail: { kode_akun: string; debit: string; kredit: string }[]
}

export type TagihanStatus = "BELUM" | "SEBAGIAN" | "LUNAS"

export type TagihanKategori = "BULANAN" | "TAHUNAN" | "LAIN"

export interface TagihanDetail {
  id?: number
  komponen: "SPP" | "KATERING" | "JEMPUTAN" | "LAIN"
  kategori: TagihanKategori
  keterangan: string
  akun_pendapatan: string
  nominal: string
  total_terbayar?: string
}

export interface Tagihan {
  id: number
  siswa: number
  siswa_nama?: string
  periode_bulan: number
  periode_tahun: number
  total: string
  status: TagihanStatus
  jurnal: string | null
  detail: TagihanDetail[]
  total_terbayar: string | null
  sisa_tagihan: string | null
  perlu_rekonsiliasi: boolean
  pembayaran: PembayaranTagihan[]
}

export interface PembayaranTagihan {
  id: number
  tanggal: string
  no_bukti: string
  nominal: string
  akun_kas: string
  jurnal: string
  jurnal_status: JurnalStatus
  created_by: number | null
  dibatalkan: boolean
  alasan_batal: string
  dibatalkan_pada: string | null
  alokasi: { detail: number; nominal: string }[]
}

export interface TagihanPreview {
  siswa: number
  periode_bulan: number
  periode_tahun: number
  periode_label: string
  detail: TagihanDetail[]
  total: string
  meta: {
    hari_katering: number
    tarif_katering: string
    siswa_nama: string
    nis: string | null
    kelompok: string | null
  }
}

export interface StrukSection {
  kategori: TagihanKategori
  label: string
  lines: { komponen: string; label: string; nominal: string }[]
}

export interface StrukTagihan {
  no_tagihan: number
  sekolah: string
  siswa: string
  nis: string | null
  kelompok: string | null
  periode: string
  periode_bulan: number
  periode_tahun: number
  status: TagihanStatus
  sections: StrukSection[]
  rincian: { komponen: string; label: string; nominal: string }[]
  total: string
  no_jurnal: string | null
  total_terbayar: string | null
  sisa_tagihan: string | null
  perlu_rekonsiliasi: boolean
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
  tanggal_mulai_kerja: string | null
  tanggal_selesai_kerja: string | null
  user: number | null
}
export type PegawaiInput = Omit<Pegawai, "id">

export type AbsenPegawaiStatus = "hadir" | "izin" | "sakit" | "terlambat" | "none"

export interface AbsenPegawai {
  id: number
  pegawai: number
  tanggal: string
  hadir: number
  izin: number
  sakit: number
  terlambat: number
}

export interface AbsenPegawaiRekap {
  pegawai: number
  nama: string
  hadir: number
  izin: number
  sakit: number
  terlambat: number
}

export interface Gaji {
  id: number
  pegawai: number
  periode_bulan: number
  periode_tahun: number
  gaji_pokok: string
  tunjangan_jabatan: string
  tunjangan_pengabdian: string
  tunjangan_asuransi: string
  uang_makan: string
  transport: string
  bonus_insentif: string
  thr: string
  hari_hadir: number
  potongan_pinjaman: string
  potongan_asuransi: string
  total_bruto: string
  total_potongan: string
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
  periode: number | null
  periode_kode?: string | null
  realisasi: string | number
  sisa_pagu: string | number
  rasio_utilisasi: number
}

export interface LaporanKegiatan {
  kegiatan: string
  pagu: string | number
  realisasi: string | number
  sisa_pagu: string | number
  rasio_utilisasi: number
  rincian: { tanggal: string; deskripsi: string; nominal: string | number }[]
}

// --- Laporan ---
export interface AuditLog {
  id: number
  table_name: string
  row_pk: string | null
  action: string
  old_data: unknown
  new_data: unknown
  changed_by: number | null
  changed_by_username?: string | null
  changed_at: string
}

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

export interface DashboardOperasional {
  siswa_aktif: number
  hadir_bulan_ini: number
  katering_bulan_ini: number
  tagihan_belum: number
  tagihan_belum_nominal: string | number
  tagihan_perlu_rekonsiliasi: number
  collection_rate_pct: number
  jurnal_menunggu_approve: number
  absensi_sparkline: { bulan: number; tahun: number; label: string; hadir: number }[]
  periode_ops_label: string
}

export interface DashboardRingkasan {
  kas: string
  total_pendapatan: string
  total_beban: string
  surplus_defisit: string
  anggaran: { pagu: string | number; realisasi: string | number }
  operasional?: DashboardOperasional
  periode_filter?: {
    mode: "day" | "month" | "year"
    tahun: number
    bulan: number | null
    tanggal: string | null
    label: string
  }
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
