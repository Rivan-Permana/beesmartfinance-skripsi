import type { Jurnal, Role } from "@/types/api"

export function dashboardMode(roles: Role[]) {
  return roles.includes("SchoolPrincipal") && !roles.includes("Finance") ? "principal" : "finance"
}

export function canReviewJurnal(journal: Jurnal, userId: number | undefined) {
  return userId !== undefined && journal.status === "PENDING" && !journal.can_finance_post
    && !journal.perlu_rekonsiliasi && journal.created_by !== userId
}
