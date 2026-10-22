import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('@/core/api', () => ({ api: { get: vi.fn() } }));
import { api } from '@/core/api';
import { jenjangApi, kelompokApi, kehadiranApi } from './api';
beforeEach(() => vi.clearAllMocks());
describe('complete attendance workspace lists', () => {
    it.each([['levels', '/jenjang/', () => jenjangApi.listAll(), {}, 200], ['groups', '/kelompok/', () => kelompokApi.listAll({ jenjang: 7 }), { jenjang: 7 }, 200], ['attendance', '/kehadiran-siswa/', () => kehadiranApi.listAll({ tanggal: '2026-10-15', kelompok: 3 }), { tanggal: '2026-10-15', kelompok: 3 }, 500]] as const)('loads every page of %s with the same scope', async (_name, path, run, params, page_size) => { vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ id: 1 }], next: '?page=2' } }).mockResolvedValueOnce({ data: { results: [{ id: 2 }], next: null } }); expect(await run()).toEqual([{ id: 1 }, { id: 2 }]); expect(api.get).toHaveBeenNthCalledWith(1, path, { params: { page_size, ...params, page: 1 } }); expect(api.get).toHaveBeenNthCalledWith(2, path, { params: { page_size, ...params, page: 2 } }); });
    it('propagates a later-page failure without returning an incomplete roster', async () => { vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ id: 1 }], next: '?page=2' } }).mockRejectedValueOnce(new Error('Page unavailable')); await expect(kelompokApi.listAll()).rejects.toThrow('Page unavailable'); });
});
