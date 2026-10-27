import type { Role } from "@/types/api"
import { journals, approvals } from "./fixtures"

export type JournalState = "DRAFT" | "PENDING" | "POSTED"
export type JournalSource = "MANUAL" | "AUTO_BILLING" | "AUTO_PENDAFTARAN" | "AUTO_KEGIATAN" | "AUTO_PAYROLL"
export interface JournalLine { account: string; debit: number; credit: number }
export interface DemoJournal {
  code: string; title: string; date: string; source: JournalSource; state: JournalState
  creator: Role; needsMatching: boolean; lines: JournalLine[]
}
export const journalStates: Record<JournalState, { label: string; tone: string }> = {
  DRAFT: { label: "Draf", tone: "neutral" },
  PENDING: { label: "Menunggu persetujuan", tone: "warning" },
  POSTED: { label: "Tercatat", tone: "success" },
}
export const journalSources: Record<JournalSource, string> = {
  MANUAL: "Manual", AUTO_BILLING: "Tagihan siswa", AUTO_PENDAFTARAN: "Pendaftaran",
  AUTO_KEGIATAN: "Kegiatan", AUTO_PAYROLL: "Penggajian",
}
// Subset from database/raw_data/coa.csv; these are examples, not live account options.
export const demoAccounts = [
  { code: "1.1.01", name: "Kas di Tangan" }, { code: "1.1.02", name: "Kas di Bank" },
  { code: "4.1.01", name: "Pendapatan SPP" }, { code: "4.1.02", name: "Uang Masuk" },
  { code: "4.1.08", name: "Pendapatan Lain-lain" }, { code: "5.3.01", name: "Beban Administrasi dan Umum" },
  { code: "5.2.01", name: "Beban Gaji Pegawai" }, { code: "5.1.1.01", name: "TK-Beban Operasional-Outing" },
]
export function lineTotals(lines: JournalLine[]) {
  return lines.reduce((sum, line) => ({ debit: sum.debit + Number(line.debit), credit: sum.credit + Number(line.credit) }), { debit: 0, credit: 0 })
}
export function hasValidLines(lines: JournalLine[]) {
  const totals = lineTotals(lines)
  // shortcut: whole-rupiah examples only; use the API decimal contract when integrating.
  return lines.length >= 2 && lines.every((line) => demoAccounts.some((account) => account.code === line.account)
    && Number.isSafeInteger(Number(line.debit)) && Number.isSafeInteger(Number(line.credit))
    && Number(line.debit) >= 0 && Number(line.credit) >= 0
    && ((Number(line.debit) > 0) !== (Number(line.credit) > 0)))
    && Number.isSafeInteger(totals.debit) && totals.debit > 0 && totals.debit === totals.credit
}
export function canFinanceRecord(journal: DemoJournal) {
  return !journal.needsMatching && ["MANUAL", "AUTO_BILLING", "AUTO_PENDAFTARAN"].includes(journal.source)
    && journal.lines.some((line) => line.account.startsWith("4") || line.account.startsWith("5"))
}
// shortcut: one demo user per role; compare actual user IDs when connecting the API.
export function availableAction(journal: DemoJournal, role: Role): "record" | "submit" | "approve" | null {
  if (journal.needsMatching || !hasValidLines(journal.lines)) return null
  if (role === "Finance") {
    if (["DRAFT", "PENDING"].includes(journal.state) && canFinanceRecord(journal)) return "record"
    if (journal.state === "DRAFT" && !canFinanceRecord(journal)) return "submit"
  }
  if (role === "SchoolPrincipal" && journal.state === "PENDING" && !canFinanceRecord(journal) && journal.creator !== role) return "approve"
  return null
}
function entryLines(amount: number, account: string, incoming = false): JournalLine[] {
  return incoming ? [{ account: "1.1.02", debit: amount, credit: 0 }, { account, debit: 0, credit: amount }]
    : [{ account, debit: amount, credit: 0 }, { account: "1.1.02", debit: 0, credit: amount }]
}
export function createDemoJournals(): DemoJournal[] {
  const drafts: DemoJournal[] = journals.map((journal, index) => ({
    code: journal.code, title: journal.title, date: index === 0 ? "2026-10-15" : "2026-10-14",
    source: index === 0 ? "AUTO_BILLING" : "MANUAL", state: "DRAFT", creator: "Finance", needsMatching: false,
    lines: entryLines(journal.amount, index === 0 ? "4.1.01" : index === 1 ? "5.3.01" : "4.1.08", journal.kind === "Penerimaan"),
  }))
  const pending: DemoJournal[] = approvals.map((journal, index) => ({
    code: journal.code, title: journal.title, date: "2026-10-13", source: index === 0 ? "AUTO_KEGIATAN" : "AUTO_PAYROLL",
    state: "PENDING", creator: "Finance", needsMatching: false,
    lines: entryLines(journal.amount, index === 0 ? "5.1.1.01" : "5.2.01"),
  }))
  return [...drafts, ...pending,
    { code: "CONTOH-006", title: "Penerimaan SPP September", date: "2026-09-30", source: "AUTO_BILLING", state: "POSTED", creator: "Finance", needsMatching: false, lines: entryLines(750_000, "4.1.01", true) },
    { code: "CONTOH-007", title: "Biaya operasional September", date: "2026-09-29", source: "MANUAL", state: "POSTED", creator: "Finance", needsMatching: false, lines: entryLines(280_000, "5.3.01") },
  ]
}
const examples = createDemoJournals()
console.assert(examples.every((journal) => hasValidLines(journal.lines))
  && availableAction(examples[0]!, "Finance") === "record"
  && availableAction(examples[3]!, "Finance") === null
  && availableAction({ ...examples[3]!, state: "DRAFT" }, "Finance") === "submit"
  && availableAction(examples[3]!, "SchoolPrincipal") === "approve"
  && availableAction({ ...examples[3]!, creator: "SchoolPrincipal" }, "SchoolPrincipal") === null
  && availableAction({ ...examples[0]!, needsMatching: true }, "Finance") === null
  && availableAction(examples[5]!, "Finance") === null
  && !hasValidLines([{ account: "1.1.02", debit: 10, credit: 10 }, { account: "4.1.01", debit: 0, credit: 0 }]),
"Journal preview fixtures or action boundaries do not match")
