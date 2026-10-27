import { describe, expect, it } from 'vitest';
import { attendanceChanged, attendanceFromRecord, attendanceNeedsSave, attendancePayload, emptyAttendance } from './presentation';
import { buildRekapRows, monthDateRange, rekapAsOfDate } from './api';
import type { KehadiranSiswa } from '@/types/api';
const record: KehadiranSiswa = { id: 71, siswa: 1, tanggal: '2026-10-15', status: 'hadir', ikut_katering: true, jemput_datang: true, jemput_pulang: true };
describe('daily attendance state', () => {
    it('treats default Hadir as an unsaved record without inventing a manual change', () => { const row = emptyAttendance(1); expect(attendanceChanged(row, { ...row })).toBe(false); expect(attendanceNeedsSave(row, { ...row })).toBe(true); });
    it('ignores identity hydration but saves actual status and service changes', () => { const base = emptyAttendance(1), row = { ...base, existingId: 71 }; expect(attendanceChanged(row, base)).toBe(false); expect(attendanceNeedsSave(row, base)).toBe(false); expect(attendanceNeedsSave({ ...row, jemput_pulang: true }, base)).toBe(true); });
    it('clears services on every non-attending payload and preserves the applied day', () => { for (const status of ['izin', 'sakit', 'tidak_hadir'] as const) {
        expect(attendancePayload({ ...attendanceFromRecord(record), status }, '2026-10-15')).toEqual({ siswa: 1, tanggal: '2026-10-15', status, ikut_katering: false, jemput_datang: false, jemput_pulang: false });
    } });
    it('marks inconsistent saved services for correction and keeps present services', () => { const base = attendanceFromRecord({ ...record, status: 'izin' }); expect(attendanceNeedsSave(base, { ...base })).toBe(true); expect(attendancePayload(attendanceFromRecord(record), '2026-10-15').ikut_katering).toBe(true); });
});
describe('recap scope', () => {
    it('uses leap-month boundaries and local current-day cutoff only for the current month', () => { expect(monthDateRange(2, 2024)).toEqual({ tanggal__gte: '2024-02-01', tanggal__lte: '2024-02-29' }); expect(rekapAsOfDate(10, 2026, new Date(2026, 9, 16))).toBe('2026-10-16'); expect(rekapAsOfDate(9, 2026, new Date(2026, 9, 16))).toBeUndefined(); });
    it('keeps students without records at zero, ignores other students and clips future records', () => { const rows = buildRekapRows([{ id: 1, nis: 'LM-01', nama: 'Alya', kelompok: 1 }, { id: 2, nis: null, nama: 'Bima', kelompok: 1 }], new Map([[1, 'Melati']]), [record, { ...record, id: 72, tanggal: '2026-10-17' }, { ...record, id: 73, siswa: 3 }], { asOfDate: '2026-10-16' }); expect(rows[0]).toMatchObject({ nama: 'Alya', hadir: 1, katering: 1 }); expect(rows[1]).toMatchObject({ nama: 'Bima', hadir: 0, tidak_hadir: 0 }); expect(buildRekapRows([{ id: 2, nis: null, nama: 'Bima', kelompok: 1 }], new Map(), [], { onlyWithData: true })).toEqual([]); });
});
