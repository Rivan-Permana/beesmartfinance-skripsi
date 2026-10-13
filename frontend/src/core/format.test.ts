import { describe, expect, it } from "vitest"

import { formatRp } from "./format"

describe("formatRp", () => {
  it("formats integer IDR", () => {
    expect(formatRp(1350000)).toBe("Rp 1.350.000")
  })

  it("formats string decimal", () => {
    expect(formatRp("500000.00")).toBe("Rp 500.000")
  })

  it("handles null as zero", () => {
    expect(formatRp(null)).toBe("Rp 0")
  })

  it("handles invalid input", () => {
    expect(formatRp("abc")).toBe("Rp 0")
  })
})
