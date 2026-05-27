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

export interface DashboardRingkasan {
  kas: string
  total_pendapatan: string
  total_beban: string
  surplus_defisit: string
  anggaran: { pagu: string | number; realisasi: string | number }
}
