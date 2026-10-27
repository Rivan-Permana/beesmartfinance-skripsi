import { describe, expect, it } from "vitest"

import { calendarTextMatches, formatLocalDate, formatRp } from "./format"

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

describe("formatLocalDate", () => {
  it("keeps the selected local calendar day at midnight", () => {
    expect(formatLocalDate(new Date(2026,9,16,0,5))).toBe("2026-10-16")
  })
  it("rejects an invalid calendar date", () => {
    expect(()=>formatLocalDate(new Date("invalid"))).toThrow(RangeError)
  })
})


describe("calendarTextMatches",()=>{
  it("rejects text that the calendar silently failed to parse",()=>{
    expect(calendarTextMatches("31/02/2026",new Date(2026,9,16))).toBe(false)
    expect(calendarTextMatches("16/10/2026",new Date(2026,9,16))).toBe(true)
    expect(calendarTextMatches("1/2/2026",new Date(2026,1,1))).toBe(true)
  })
  it("accepts an intentionally cleared optional date and rejects missing/invalid dates with text",()=>{
    expect(calendarTextMatches("",null)).toBe(true)
    expect(calendarTextMatches("16/10/2026",null)).toBe(false)
    expect(calendarTextMatches("16/10/2026",new Date('invalid'))).toBe(false)
  })
})
