import type { KehadiranSiswa, KehadiranSiswaInput, KehadiranStatus } from '@/types/api';
export interface AttendanceRow {
    siswaId: number;
    existingId?: number;
    status: KehadiranStatus;
    ikut_katering: boolean;
    jemput_datang: boolean;
    jemput_pulang: boolean;
}
export const attendanceStatuses = [
    { value: 'hadir', label: 'Hadir' }, { value: 'izin', label: 'Izin' }, { value: 'sakit', label: 'Sakit' }, { value: 'tidak_hadir', label: 'Tidak hadir' },
] as const;
export const serviceFlags = [
    { key: 'ikut_katering', label: 'Katering' }, { key: 'jemput_datang', label: 'Jemput datang' }, { key: 'jemput_pulang', label: 'Jemput pulang' },
] as const;
export function emptyAttendance(siswaId: number): AttendanceRow { return { siswaId, status: 'hadir', ikut_katering: false, jemput_datang: false, jemput_pulang: false }; }
export function attendanceFromRecord(record: KehadiranSiswa): AttendanceRow { return { siswaId: record.siswa, existingId: record.id, status: record.status, ikut_katering: record.ikut_katering, jemput_datang: record.jemput_datang, jemput_pulang: record.jemput_pulang }; }
export function attendanceChanged(row: AttendanceRow, base: AttendanceRow | undefined) { return !base || row.status !== base.status || serviceFlags.some(flag => row[flag.key] !== base[flag.key]); }
export function invalidServices(row: AttendanceRow) { return row.status !== 'hadir' && serviceFlags.some(flag => row[flag.key]); }
export function attendanceNeedsSave(row: AttendanceRow, base: AttendanceRow | undefined) { return !row.existingId || attendanceChanged(row, base) || invalidServices(row); }
export function attendancePayload(row: AttendanceRow, tanggal: string): KehadiranSiswaInput {
    return { siswa: row.siswaId, tanggal, status: row.status, ikut_katering: row.status === 'hadir' && row.ikut_katering, jemput_datang: row.status === 'hadir' && row.jemput_datang, jemput_pulang: row.status === 'hadir' && row.jemput_pulang };
}
export function attendanceDays(row: {
    hadir: number;
    izin: number;
    sakit: number;
    tidak_hadir: number;
}) { return row.hadir + row.izin + row.sakit + row.tidak_hadir; }
