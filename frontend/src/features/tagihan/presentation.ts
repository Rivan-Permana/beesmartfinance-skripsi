import type { PembayaranTagihan, Tagihan } from "@/types/api"

export const TAGIHAN_STATUS = {
  BELUM: { label: "Belum dibayar", severity: "warn" },
  SEBAGIAN: { label: "Dibayar sebagian", severity: "info" },
  LUNAS: { label: "Lunas", severity: "success" },
} as const
export function perluDicocokkan(row: Pick<Tagihan, "perlu_rekonsiliasi" | "total_terbayar" | "sisa_tagihan">) {
  return row.perlu_rekonsiliasi || row.total_terbayar === null || row.sisa_tagihan === null
}
export function tagihanState(row: Tagihan) {
  return perluDicocokkan(row) ? { label: "Perlu dicocokkan", severity: "warn" } : TAGIHAN_STATUS[row.status]
}
export function canEditTagihan(row: Tagihan) {
  // Biaya masuk diubah lewat Data Siswa agar tetap sama dengan isian siswa.
  return row.jenis !== "BIAYA_MASUK" && row.status === "BELUM" && !perluDicocokkan(row) && row.pembayaran.length === 0
}
export function canPayTagihan(row: Tagihan) {
  return !perluDicocokkan(row) && Number(row.sisa_tagihan) > 0
}
export function tagihanPeriod(row: Pick<Tagihan, "periode_bulan" | "periode_tahun"> & Partial<Pick<Tagihan, "jenis">>) {
  const bulan = new Date(row.periode_tahun, row.periode_bulan - 1, 1).toLocaleDateString("id-ID", { month: "long", year: "numeric" })
  return row.jenis === "BIAYA_MASUK" ? `Biaya masuk · ${bulan}` : bulan
}
export function paymentCancelled(payment: Pick<PembayaranTagihan, "dibatalkan" | "jurnal_status">) {
  return payment.dibatalkan || payment.jurnal_status === "VOID"
}
/** Label riwayat pembayaran. Saldo awal = penerimaan sebelum cut-over, tanpa jurnal dan tanpa kwitansi. */
export function paymentState(payment: Pick<PembayaranTagihan, "dibatalkan" | "jurnal_status" | "saldo_awal">) {
  if (paymentCancelled(payment)) return { label: "Dibatalkan", severity: "danger" }
  if (payment.saldo_awal) return { label: "Saldo awal dari spreadsheet", severity: "secondary" }
  if (payment.jurnal_status === "POSTED") return { label: "Sudah dicatat", severity: "success" }
  return { label: "Menunggu pencatatan keuangan", severity: "info" }
}
/** Rincian kwitansi: komponen tagihan yang dilunasi oleh satu pembayaran. */
export function receiptLines(tagihan: Pick<Tagihan, "detail">, payment: Pick<PembayaranTagihan, "alokasi">) {
  return payment.alokasi.map(line => {
    const item = tagihan.detail.find(d => d.id === line.detail)
    return { detail: line.detail, label: item?.keterangan || item?.komponen || "Komponen tagihan", nominal: line.nominal }
  })
}
