/** Format nominal IDR — hindari float di display layer (NFR-9). */
export function formatRp(value: string | number | null | undefined): string {
  const n = Number(value ?? 0)
  if (Number.isNaN(n)) return "Rp 0"
  return "Rp " + n.toLocaleString("id-ID")
}

/** Calendar dates use local fields; converting midnight to UTC can change the day. */
export function formatLocalDate(value: Date): string {
  if (!Number.isFinite(value.getTime())) throw new RangeError("Invalid calendar date")
  return `${value.getFullYear()}-${String(value.getMonth()+1).padStart(2,"0")}-${String(value.getDate()).padStart(2,"0")}`
}

/** PrimeVue restores the old date on parse failure; compare manual text before that happens. */
export function calendarTextMatches(text: string, date: Date | null | undefined): boolean {
  const input = text.trim()
  if (!input) return date == null
  const parts = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(input)
  return Boolean(parts && date && Number.isFinite(date.getTime())
    && Number(parts[1]) === date.getDate() && Number(parts[2]) === date.getMonth()+1 && Number(parts[3]) === date.getFullYear())
}
