import { describe, expect, it } from "vitest"
import { buildXlsx } from "./export"

describe("buildXlsx", () => {
  it("packs a valid zip with escaped inline strings and numeric cells", () => {
    const bytes = buildXlsx("Rekap Oktober 2026", ["Nama", "Hadir"], [["Ani & <Budi>", 20]])
    const view = new DataView(bytes.buffer)
    expect(view.getUint32(0, true)).toBe(0x04034b50)
    expect(view.getUint32(bytes.length - 22, true)).toBe(0x06054b50)
    expect(view.getUint16(bytes.length - 12, true)).toBe(6)
    const text = new TextDecoder().decode(bytes)
    expect(text).toContain("Ani &amp; &lt;Budi&gt;")
    expect(text).toContain('<c r="B2"><v>20</v></c>')
    expect(text).toContain('<sheet name="Rekap Oktober 2026"')
  })
})
