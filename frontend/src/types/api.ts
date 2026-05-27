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
