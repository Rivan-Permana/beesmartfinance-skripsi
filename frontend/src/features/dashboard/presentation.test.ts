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
