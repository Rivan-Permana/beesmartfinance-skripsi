import type { PaketLSU } from "@/types/api"

export const JUMLAH_SESI_OPTIONS = [
  { label: "8 pertemuan", value: 8 },
  { label: "16 pertemuan", value: 16 },
] as const

export function sisaSesi(paket: Pick<PaketLSU, "jumlah_sesi" | "sesi_terpakai">) {
  return Math.max(paket.jumlah_sesi - paket.sesi_terpakai, 0)
}

export function paketState(paket: Pick<PaketLSU, "jumlah_sesi" | "sesi_terpakai">) {
  return sisaSesi(paket) === 0
    ? { label: "Sesi habis", severity: "secondary" as const }
    : { label: `Sisa ${sisaSesi(paket)} sesi`, severity: "info" as const }
}

export function tagihanState(paket: Pick<PaketLSU, "tagihan_status">) {
  if (paket.tagihan_status === "LUNAS") return { label: "Lunas", severity: "success" as const }
  if (paket.tagihan_status === "SEBAGIAN") return { label: "Dibayar sebagian", severity: "warn" as const }
  return { label: "Belum dibayar", severity: "danger" as const }
}

/** Paket berjalan lebih dulu, lalu yang terbaru. */
export function urutkanPaket(rows: PaketLSU[]) {
  return [...rows].sort((a, b) =>
    Number(sisaSesi(b) > 0) - Number(sisaSesi(a) > 0) || b.tanggal_mulai.localeCompare(a.tanggal_mulai) || b.id - a.id,
  )
}

/** Siswa yang masih punya paket berjalan tidak bisa dibukakan paket baru. */
export function siswaPunyaPaketBerjalan(rows: PaketLSU[], siswa: number | null) {
  return siswa != null && rows.some((p) => p.siswa === siswa && sisaSesi(p) > 0)
}
