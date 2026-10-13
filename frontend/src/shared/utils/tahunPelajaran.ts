/** Utilitas tahun pelajaran (Juli–Juni). */

export interface TahunPelajaran {
  kode: string
  startYear: number
  endYear: number
  isActive: boolean
}

export function currentTahunPelajaran(ref = new Date()): TahunPelajaran {
  const y = ref.getFullYear()
  const m = ref.getMonth() + 1
  if (m >= 7) {
    return { kode: `${y}/${y + 1}`, startYear: y, endYear: y + 1, isActive: true }
  }
  return { kode: `${y - 1}/${y}`, startYear: y - 1, endYear: y, isActive: true }
}

export function listTahunPelajaran(minStart = 2023, ref = new Date()): TahunPelajaran[] {
  const active = currentTahunPelajaran(ref)
  const out: TahunPelajaran[] = []
  for (let s = active.startYear; s >= minStart; s -= 1) {
    out.push({
      kode: `${s}/${s + 1}`,
      startYear: s,
      endYear: s + 1,
      isActive: s === active.startYear,
    })
  }
  return out
}

/** Apakah pasangan bulan/tahun kalender ada di dalam TA. */
export function isMonthInTa(ta: TahunPelajaran, bulan: number, tahun: number): boolean {
  if (tahun === ta.startYear && bulan >= 7) return true
  if (tahun === ta.endYear && bulan <= 6) return true
  return false
}

/** Default bulan/tahun untuk TA: bulan berjalan jika masuk TA, else Juli awal TA. */
export function defaultMonthForTa(ta: TahunPelajaran, ref = new Date()): { bulan: number; tahun: number } {
  const m = ref.getMonth() + 1
  const y = ref.getFullYear()
  if (isMonthInTa(ta, m, y)) return { bulan: m, tahun: y }
  return { bulan: 7, tahun: ta.startYear }
}
