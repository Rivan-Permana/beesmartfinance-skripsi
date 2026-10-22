import { formatRp } from '@/core/format'
import { friendlyError } from '@/core/errors'
import type { Gaji, Pinjaman } from '@/types/api'

export const months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
export const earnings = [
  { key: 'gaji_pokok', label: 'Gaji pokok' },
  { key: 'tunjangan_jabatan', label: 'Tunjangan jabatan' },
  { key: 'tunjangan_pengabdian', label: 'Tunjangan pengabdian' },
  { key: 'tunjangan_asuransi', label: 'Tunjangan asuransi' },
  { key: 'uang_makan', label: 'Uang makan' },
  { key: 'transport', label: 'Transport' },
  { key: 'bonus_insentif', label: 'Bonus / insentif' },
  { key: 'thr', label: 'THR' },
] as const
export type EarningKey = typeof earnings[number]['key']
export function cents(value: string | number | null | undefined): number | null {
  if (value == null || value === '') return null
  const number = Number(value), result = Math.round(number * 100)
  return Number.isFinite(number) && number >= 0 && Number.isSafeInteger(result) ? result : null
}
export function sumMoney(values: (string | number | null | undefined)[]): number | null {
  let total = 0
  for (const value of values) { const amount = cents(value); if (amount == null) return null; total += amount }
  return Number.isSafeInteger(total) ? total / 100 : null
}
export function money(value: string | number | null | undefined) {
  if (value == null || value === '' || !Number.isFinite(Number(value))) return 'Belum diketahui'
  if (typeof value === 'string' && /^-?\d+(\.\d{1,2})?$/.test(value)) {
    const [whole, fraction] = value.replace(/^-/, '').split('.')
    const decimal = fraction?.replace(/0+$/, '')
    return `Rp ${value.startsWith('-')?'-':''}${BigInt(whole!).toLocaleString('id-ID')}${decimal?','+decimal:''}`
  }
  return Number.isSafeInteger(Math.round(Number(value)*100)) ? formatRp(value) : 'Nominal perlu diperiksa'
}
export function salaryPeriod(row: Pick<Gaji, 'periode_bulan' | 'periode_tahun'>) { return `${months[row.periode_bulan-1] ?? 'Bulan belum diketahui'} ${row.periode_tahun}` }
export function dateLabel(iso: string) { return new Intl.DateTimeFormat('id-ID',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${iso}T12:00:00`)) }
export function loanDeduction(rows: Pinjaman[], employee: number | null): number | null {
  const values: number[] = []
  for (const row of rows.filter(row => row.pegawai === employee && row.ikut_potongan)) {
    const rest = cents(row.sisa_pinjaman), monthly = cents(row.angsuran_per_bulan)
    if (rest == null || monthly == null) return null
    values.push(Math.min(rest, monthly > 0 ? monthly : rest) / 100)
  }
  return sumMoney(values)
}
export function loanDisbursed(row: Pick<Pinjaman, 'jurnal' | 'is_legacy'>) { return !!row.jurnal || row.is_legacy }
export function loanStatus(row: Pick<Pinjaman, 'jurnal' | 'is_legacy' | 'ikut_potongan'>): { label: string, severity: 'info' | 'warn' | 'secondary' } {
  if (row.is_legacy) return { label: 'Saldo legacy', severity: 'secondary' }
  if (!row.jurnal) return { label: 'Menunggu pencairan', severity: 'warn' }
  return row.ikut_potongan ? { label: 'Sudah dicairkan', severity: 'info' } : { label: 'Pencairan menunggu persetujuan', severity: 'warn' }
}
export function errorText(value: unknown, fallback: string) { const error = friendlyError(value,fallback); return [error.summary,error.detail].filter(Boolean).join('. ') }
export function ambiguous(value: unknown) { const status = (value as {response?: {status?: number}})?.response?.status; return status == null || status >= 500 }
