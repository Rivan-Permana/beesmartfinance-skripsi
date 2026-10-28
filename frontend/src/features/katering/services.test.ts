import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('@/core/api', () => ({ api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));
import { api } from '@/core/api';
import { buildKateringRekapFromRecords, kateringRekapToCsv, weekdaysOfWeek } from './api';
import { armadaApi, buildJemputanRekap, pendaftaranJemputanApi } from '@/features/jemputan/api';
import type { KehadiranSiswa, PendaftaranJemputan } from '@/types/api';
const record: KehadiranSiswa = { id: 1, siswa: 1, tanggal: '2026-10-15', status: 'hadir', ikut_katering: true, jemput_datang: true, jemput_pulang: true };
beforeEach(() => vi.clearAllMocks());
describe('service calculation contracts', () => {
    it('separates weekday/Friday, ignores weekends and unflagged records, and retains cents', () => {
        const rows = buildKateringRekapFromRecords([{ id: 1, nis: 'LM-1', nama: 'Alya', kelompok: 'Melati' }, { id: 2, nis: null, nama: 'Bima', kelompok: 'Melati' }], [record, { ...record, id: 2, tanggal: '2026-10-16' }, { ...record, id: 3, tanggal: '2026-10-17' }, { ...record, id: 4, tanggal: '2026-10-19', ikut_katering: false }], 0.1, 0.2);
        expect(rows).toHaveLength(1);
        expect(rows[0]).toMatchObject({ hariSenKam: 1, hariJumat: 1, hariKatering: 2, total: 0.3 });
        expect(kateringRekapToCsv(rows).split('\n')[1]).toContain('0.1,0.2,0.3');
    });
    it('takes the newest registration by ID, including zero, matching backend billing rather than highest price', () => {
        const registrations: PendaftaranJemputan[] = [{ id: 9, siswa: 1, armada: 1, harga: '20000.00' }, { id: 12, siswa: 1, armada: 2, harga: '0.00' }, { id: 10, siswa: 1, armada: 1, harga: '30000.00' }];
        const rows = buildJemputanRekap(registrations, new Map([[1, { nama: 'Alya', nis: 'LM-1', alamat: 'Jalan Melati' }]]), new Map([[1, 'Armada lama'], [2, 'Armada terbaru']]), new Map([[1, { datang: 2, pulang: 3 }]]));
        expect(rows).toEqual([expect.objectContaining({ armada: 'Armada terbaru', tarifPerTrip: 0, totalNominal: 0, jemputDatang: 2, jemputPulang: 3 })]);
    });
    it('counts both directions, keeps cents exact and includes registered students without trips', () => {
        const students = new Map([[1, { nama: 'Alya', nis: null, alamat: null }], [2, { nama: 'Bima', nis: null, alamat: null }]]);
        const rows = buildJemputanRekap([{ id: 1, siswa: 1, armada: null, harga: '0.10' }, { id: 2, siswa: 2, armada: null, harga: '25000.25' }], students, new Map(), new Map([[1, { datang: 1, pulang: 2 }]]));
        expect(rows[0]?.totalNominal).toBe(0.3);
        expect(rows[1]?.totalNominal).toBe(0);
    });
    it('uses local Monday-Friday dates across month boundaries even when anchored on Sunday', () => {
        expect(weekdaysOfWeek(new Date(2026, 10, 1))).toEqual(['2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30']);
    });
});
describe('transport pagination', () => {
    it.each([['armada', '/armada-jemputan/', () => armadaApi.listAll(), {}], ['registrations', '/pendaftaran-jemputan/', () => pendaftaranJemputanApi.listAll({ siswa: 1 }), { siswa: 1 }]] as const)('reads every %s page without losing scope', async (_name, path, run, scope) => {
        vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ id: 1 }], next: '?page=2' } }).mockResolvedValueOnce({ data: { results: [{ id: 2 }], next: null } });
        expect(await run()).toEqual([{ id: 1 }, { id: 2 }]);
        expect(api.get).toHaveBeenLastCalledWith(path, { params: { page_size: 200, ...scope, page: 2 } });
    });
    it('rejects a partial list when page two fails', async () => {
        vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ id: 1 }], next: '?page=2' } }).mockRejectedValueOnce(new Error('Unavailable'));
        await expect(armadaApi.listAll()).rejects.toThrow('Unavailable');
    });
});

describe("weekdaysOfMonth", () => {
  it("lists Monday–Friday dates of the month", async () => {
    const { weekdaysOfMonth } = await import("./api")
    const days = weekdaysOfMonth(new Date(2026, 9, 15))
    expect(days[0]).toBe("2026-10-01")
    expect(days.at(-1)).toBe("2026-10-30")
    expect(days).toHaveLength(22)
    expect(days).not.toContain("2026-10-03")
  })
})
