import type { AbsenPegawai, Pegawai, PegawaiStatus } from '@/types/api'

export const staffStatuses = [
  { label: 'Hadir', value: 'hadir' }, { label: 'Izin', value: 'izin' },
  { label: 'Sakit', value: 'sakit' }, { label: 'Terlambat', value: 'terlambat' },
  { label: 'Tanpa catatan', value: 'none' },
] as const
export type StaffStatus = typeof staffStatuses[number]['value']
export type StaffAttendanceRow = Pick<AbsenPegawai, 'pegawai' | 'hadir' | 'izin' | 'sakit' | 'terlambat'> & { stored: boolean }
export const attendanceFields = ['hadir', 'izin', 'sakit', 'terlambat'] as const
export function staffAttendance(pegawai: number, record?: AbsenPegawai): StaffAttendanceRow {
  return record ? { pegawai, hadir: record.hadir, izin: record.izin, sakit: record.sakit, terlambat: record.terlambat, stored: true }
    : { pegawai, hadir: 1, izin: 0, sakit: 0, terlambat: 0, stored: false }
}
export function staffStatus(row: StaffAttendanceRow): StaffStatus | 'mixed' {
  if (attendanceFields.every(key => row[key] === 0)) return 'none'
  return attendanceFields.find(key => row[key] === 1 && attendanceFields.every(other => other === key || row[other] === 0)) ?? 'mixed'
}
export function setStaffStatus(row: StaffAttendanceRow, status: StaffStatus): StaffAttendanceRow {
  return { ...row, hadir: status === 'hadir' ? 1 : 0, izin: status === 'izin' ? 1 : 0, sakit: status === 'sakit' ? 1 : 0, terlambat: status === 'terlambat' ? 1 : 0 }
}
export function staffChanged(row: StaffAttendanceRow, baseline: StaffAttendanceRow) {
  return attendanceFields.some(key => row[key] !== baseline[key])
}
export function staffNeedsSave(row: StaffAttendanceRow, baseline: StaffAttendanceRow) {
  return baseline.stored ? staffChanged(row, baseline) : staffStatus(row) !== 'none'
}
export function staffPeriod(row: Pegawai) {
  const label = (value: string) => value.split('-').reverse().join('/')
  if (!row.tanggal_mulai_kerja && !row.tanggal_selesai_kerja) return 'Belum dicatat'
  return `${row.tanggal_mulai_kerja ? label(row.tanggal_mulai_kerja) : 'Mulai belum dicatat'} – ${row.tanggal_selesai_kerja ? label(row.tanggal_selesai_kerja) : 'Sekarang'}`
}

export const employeeStatuses: { label: string; value: PegawaiStatus; severity: 'success' | 'warn' | 'secondary' }[] = [
  { label: 'Aktif', value: 'aktif', severity: 'success' },
  { label: 'Cuti', value: 'cuti', severity: 'warn' },
  { label: 'Non-aktif', value: 'nonaktif', severity: 'secondary' },
]
export function employeeStatus(row: Pick<Pegawai, 'status'>) {
  return employeeStatuses.find(item => item.value === row.status) ?? employeeStatuses[0]!
}
/** Pegawai Cuti tetap dapat dibuatkan gaji dan kasbon; Non-aktif tidak. */
export function payrollEligible(row: Pick<Pegawai, 'status'>) { return row.status !== 'nonaktif' }
