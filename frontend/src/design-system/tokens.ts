import { tokens } from "@/core/designTokens"
export { tokens, cssVariables } from "@/core/designTokens"

export function contrastRatio(foreground: string, background: string) {
  function luminance(hex: string) {
    const rgb = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16) / 255)
      .map((value) => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
    return rgb[0]! * .2126 + rgb[1]! * .7152 + rgb[2]! * .0722
  }
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return (values[0]! + .05) / (values[1]! + .05)
}
export const contrastPairs = [
  { name: "Teks utama", foreground: tokens.color.ink, background: tokens.color.surface },
  { name: "Teks pendukung", foreground: tokens.color.muted, background: tokens.color.surface },
  { name: "Tindakan utama", foreground: tokens.color.surface, background: tokens.color.brand },
  { name: "Navigasi pendukung", foreground: tokens.color["nav-muted"], background: tokens.color.nav },
  { name: "Status tercatat", foreground: tokens.color.positive, background: tokens.color["positive-tint"] },
  { name: "Status menunggu", foreground: tokens.color.warning, background: tokens.color["warning-tint"] },
  { name: "Pesan gagal", foreground: tokens.color.critical, background: tokens.color["critical-tint"] },
]
console.assert(Object.values(tokens.color).every((value) => /^#[0-9a-f]{6}([0-9a-f]{2})?$/i.test(value))
  && contrastPairs.every((pair) => contrastRatio(pair.foreground, pair.background) >= 4.5)
  && contrastRatio(tokens.color["control-border"], tokens.color.surface) >= 3
  && contrastRatio("#000000", "#ffffff") === 21
  && tokens.primary[500] === tokens.color.brand && tokens.primary[600] === tokens.color["brand-hover"],
"Design-system token shape or contrast requirements failed")
