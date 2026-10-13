/** Format nominal IDR — hindari float di display layer (NFR-9). */
export function formatRp(value: string | number | null | undefined): string {
  const n = Number(value ?? 0)
  if (Number.isNaN(n)) return "Rp 0"
  return "Rp " + n.toLocaleString("id-ID")
}
