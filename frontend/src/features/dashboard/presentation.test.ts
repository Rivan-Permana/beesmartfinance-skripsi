import { describe, expect, it } from "vitest"
import type { Jurnal } from "@/types/api"
import { canReviewJurnal, dashboardMode } from "./presentation"

describe("dashboard priorities and review eligibility", () => {
  it("keeps Finance priorities when both dashboard roles are present", () => {
    expect(dashboardMode(["SchoolPrincipal"])).toBe("principal")
    expect(dashboardMode(["Finance", "SchoolPrincipal"])).toBe("finance")
  })
  it("excludes drafts, direct Finance posting, reconciliation and own journals", () => {
    const pending = { status: "PENDING", can_finance_post: false, perlu_rekonsiliasi: false, created_by: 2 } as Jurnal
    expect(canReviewJurnal(pending, 1)).toBe(true)
    expect(canReviewJurnal({ ...pending, status: "DRAFT" }, 1)).toBe(false)
    expect(canReviewJurnal({ ...pending, can_finance_post: true }, 1)).toBe(false)
    expect(canReviewJurnal({ ...pending, perlu_rekonsiliasi: true }, 1)).toBe(false)
    expect(canReviewJurnal(pending, 2)).toBe(false)
    expect(canReviewJurnal(pending, undefined)).toBe(false)
  })
})

describe("defaultPeriode", () => {
  const rows = [
    { id: 1, tgl_mulai: "2025-07-01", tgl_selesai: "2026-06-30" },
    { id: 2, tgl_mulai: "2026-07-01", tgl_selesai: "2027-06-30" },
  ]
  it("chooses the school year containing today, else the latest", async () => {
    const { defaultPeriode } = await import("./presentation")
    expect(defaultPeriode(rows, "2026-10-28")?.id).toBe(2)
    expect(defaultPeriode(rows, "2026-06-30")?.id).toBe(1)
    expect(defaultPeriode(rows, "2030-01-01")?.id).toBe(2)
    expect(defaultPeriode([], "2026-10-28")).toBeNull()
  })
})
