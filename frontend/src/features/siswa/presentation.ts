import type { Kelompok, SiswaStatus } from "@/types/api"

export const SISWA_STATUS = {
  aktif: { label: "Aktif", severity: "success" },
  lulus: { label: "Lulus", severity: "secondary" },
  cuti: { label: "Cuti", severity: "warn" },
  pindah: { label: "Pindah", severity: "secondary" },
  mengulang: { label: "Mengulang kelas", severity: "info" },
  naik: { label: "Naik kelas", severity: "info" },
} as const satisfies Record<SiswaStatus, { label: string; severity: string }>

export const statusOptions = Object.entries(SISWA_STATUS).map(([value, state]) => ({ value, label: state.label }))
export function kelompokLabel(kelompok: Kelompok) {
  return [kelompok.jenjang_kode, kelompok.nama].filter(Boolean).join(" · ")
}
