import { formatLocalDate } from "@/core/format"
import type { Coa, Jurnal, JurnalInput, JurnalStatus, KodePengeluaran } from "@/types/api"

export const journalStates: Record<JurnalStatus, { label: string; severity: "secondary" | "warn" | "success" | "danger" }> = {
  DRAFT: { label: "Draf", severity: "secondary" },
  PENDING: { label: "Menunggu persetujuan", severity: "warn" },
  POSTED: { label: "Tercatat", severity: "success" },
  VOID: { label: "Dibatalkan", severity: "danger" },
}
export function journalState(row: Jurnal) {
  return row.perlu_rekonsiliasi ? { label: "Perlu dicocokkan", severity: "warn" as const } : journalStates[row.status] ?? { label: "Status belum dikenali", severity: "secondary" as const }
}
export function journalSource(source: string) {
  const labels: Record<string, string> = { MANUAL: "Jurnal manual", AUTO_BILLING: "Pembayaran tagihan", AUTO_PENDAFTARAN: "Pendaftaran", AUTO_SITIN: "Sit-in", AUTO_PAYROLL: "Penggajian", AUTO_DEPRESIASI: "Penyusutan aset", AUTO_KASBON: "Kasbon pegawai", AUTO_KEGIATAN: "Kegiatan", REVERSAL: "Jurnal pembalik", CLOSING: "Tutup buku", AUTO_ANGGARAN_LEGACY: "Anggaran lama" }
  return labels[source] ?? "Transaksi sumber lain"
}
export function journalDate(value: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? value.split("-").reverse().join("/") : value
}

// Integer cents keep decimal journals such as 0.10 + 0.20 balanced.
function cents(value: number | string) {
  if ((typeof value !== "string" && typeof value !== "number") || (typeof value === "string" && !value.trim())) return null
  const number = Number(value)
  const rounded = Math.round(number * 100)
  return Number.isFinite(number) && number >= 0 && Number.isSafeInteger(rounded)
    && Math.abs(number * 100 - rounded) < 0.00001 ? rounded : null
}
export function journalTotals(lines: ReadonlyArray<{ debit: number | string; kredit: number | string }>) {
  let debit = 0, kredit = 0
  for (const line of lines) {
    const d = cents(line.debit), k = cents(line.kredit)
    if (d === null || k === null) return null
    debit += d; kredit += k
    if (!Number.isSafeInteger(debit) || !Number.isSafeInteger(kredit)) return null
  }
  return { debit: debit / 100, kredit: kredit / 100, balanced: debit === kredit && debit > 0 }
}
export interface JournalForm {
  no_bukti: string
  tanggal: Date | null
  keterangan: string
  /** kode_sekolah: kode singkat buku kas yang diketik; akun_dari_kode: akun terisi dari kode itu. Keduanya tidak disimpan. */
  detail: { kode_akun: string | null; debit: number; kredit: number; kode_sekolah?: string; akun_dari_kode?: boolean }[]
}
export function journalLineValid(line: JournalForm["detail"][number], accounts: Coa[]) {
  return accounts.some(account => account.is_active && account.kode_akun === line.kode_akun)
    && cents(line.debit) !== null && cents(line.kredit) !== null && !(line.debit > 0 && line.kredit > 0)
}
export function journalFormValid(form: JournalForm, accounts: Coa[]) {
  return Boolean(form.no_bukti.trim() && form.tanggal && Number.isFinite(form.tanggal.getTime())
    && form.detail.length >= 2 && form.detail.every(line => journalLineValid(line, accounts))
    && journalTotals(form.detail)?.balanced)
}
export function journalPayload(form: JournalForm): JurnalInput {
  return { no_bukti: form.no_bukti.trim(), tanggal: formatLocalDate(form.tanggal!), keterangan: form.keterangan,
    detail: form.detail.map(line => ({ kode_akun: line.kode_akun!, debit: line.debit.toFixed(2), kredit: line.kredit.toFixed(2) })) }
}
export type JournalAction = "edit" | "remove" | "submit" | "approve" | "reject" | "catat" | "cancel" | "cancelDraft" | "void"
/** drafter: Staf TU yang menyiapkan draf untuk dicatat Keuangan. */
export interface JournalAccess { finance: boolean; principal: boolean; drafter?: boolean; userId?: number }
export const journalActionLabels: Record<JournalAction, string> = {
  edit: "Ubah draf", remove: "Hapus draf", submit: "Ajukan persetujuan", approve: "Setujui dan catat", reject: "Tolak pengajuan", catat: "Catat ke buku besar", cancel: "Batalkan penerimaan", cancelDraft: "Batalkan draf", void: "Buat jurnal pembalik",
}
export function journalActions(row: Jurnal, access: JournalAccess): JournalAction[] {
  if (row.is_deleted) return []
  const actions: JournalAction[] = []
  if (row.status === "DRAFT" && row.tipe_sumber === "MANUAL" && (access.finance || access.drafter && access.userId !== undefined && row.created_by === access.userId)) actions.push("edit", "remove")
  if (access.finance && !row.perlu_rekonsiliasi) {
    if (row.status === "DRAFT" && !row.can_finance_post) actions.push("submit")
    if (["DRAFT", "PENDING"].includes(row.status) && row.can_finance_post) actions.push("catat")
    if (["DRAFT", "PENDING"].includes(row.status) && ["AUTO_BILLING", "AUTO_PENDAFTARAN", "AUTO_SITIN"].includes(row.tipe_sumber)) actions.push("cancel")
    if (["DRAFT", "PENDING"].includes(row.status) && ["AUTO_PAYROLL", "AUTO_KASBON"].includes(row.tipe_sumber)) actions.push("cancelDraft")
  }
  if (access.principal) {
    if (row.status === "PENDING" && !row.can_finance_post && !row.perlu_rekonsiliasi && access.userId !== undefined && row.created_by !== access.userId) actions.push("approve", "reject")
    if (row.status === "POSTED") actions.push("void")
  }
  return actions
}

export type KodeResolusi =
  | { status: "ok"; kode: KodePengeluaran }
  | { status: "unmapped"; kode: KodePengeluaran }
  | { status: "ambiguous"; pilihan: string[] }
  | { status: "unknown" }
  | { status: "empty" }
/** "ATK", "STR TK", "ab3 pg" -> kode sekolah aktif. Unit yang tidak terdaftar jatuh ke kode Umum. */
export function resolveKodePengeluaran(input: string, codes: KodePengeluaran[]): KodeResolusi {
  const [kode = "", unit] = input.trim().toUpperCase().split(/\s+/)
  if (!kode) return { status: "empty" }
  const cocok = codes.filter(code => code.aktif && code.kode === kode)
  const pilih = (unit ? cocok.find(code => code.unit === unit) : undefined)
    ?? cocok.find(code => code.unit === "UMUM")
    ?? (cocok.length === 1 ? cocok[0] : undefined)
  if (pilih) return { status: pilih.akun ? "ok" : "unmapped", kode: pilih }
  if (cocok.length) return { status: "ambiguous", pilihan: cocok.map(code => `${code.kode} ${code.unit}`) }
  return { status: "unknown" }
}
export function kodeLabel(code: KodePengeluaran) {
  return code.unit === "UMUM" ? code.kode : `${code.kode} ${code.unit}`
}
/** Petunjuk di bawah kolom kode sekolah. Kode tanpa akun tetap (mis. STR Sentra) bukan kesalahan: akunnya dipilih per transaksi. */
export function petunjukKode(input: string, codes: KodePengeluaran[]): { warn: boolean; text: string } | null {
  const hasil = resolveKodePengeluaran(input, codes)
  if (hasil.status === "ok") return { warn: false, text: `${kodeLabel(hasil.kode)} → ${hasil.kode.akun} ${hasil.kode.akun_nama ?? ""}`.trim() }
  if (hasil.status === "unmapped") return { warn: false, text: `${kodeLabel(hasil.kode)} (${hasil.kode.nama}) tidak punya akun tetap. Pilih akun ${hasil.kode.nama} yang sesuai untuk transaksi ini.` }
  if (hasil.status === "ambiguous") return { warn: true, text: `Tambahkan unit: ${hasil.pilihan.join(" atau ")}.` }
  if (hasil.status === "unknown") return { warn: true, text: "Kode belum terdaftar. Pilih akun manual." }
  return null
}
