import type { Jurnal, Role } from "@/types/api"

export function dashboardMode(roles: Role[]) {
  return roles.includes("SchoolPrincipal") && !roles.includes("Finance") ? "principal" : "finance"
}

export function canReviewJurnal(journal: Jurnal, userId: number | undefined) {
  return userId !== undefined && journal.status === "PENDING" && !journal.can_finance_post
    && !journal.perlu_rekonsiliasi && journal.created_by !== userId
}

/** Periode yang memuat `today`; bila tidak ada, periode terbaru. */
export function defaultPeriode<T extends { tgl_mulai: string; tgl_selesai: string }>(rows: T[], today: string): T | null {
  return rows.find((row) => row.tgl_mulai <= today && today <= row.tgl_selesai)
    ?? [...rows].sort((a, b) => b.tgl_mulai.localeCompare(a.tgl_mulai))[0] ?? null
}
