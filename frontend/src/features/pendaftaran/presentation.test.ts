import { describe, expect, it } from 'vitest';
import { cents, components, editable, finalizable, money, receivable } from './presentation';
import type { PendaftaranSiswa } from '@/types/api';
const row: PendaftaranSiswa = { id: 1, nama_calon: 'Alya', jenjang: null, tanggal_daftar: '2026-10-18', status: 'TRIAL', siswa: null, biaya_sitin: '750000.25', biaya_formulir: '100000.10', biaya_pendaftaran: '0.00', total_biaya: '850000.35', total_terbayar: '750000.25', sisa_biaya: '100000.10', perlu_rekonsiliasi: false, sitin_terbayar: true, formulir_terbayar: false, jurnal_sitin: 'journal-1', jurnal_pendaftaran: null, pembayaran: [] };
describe('admission actions and amounts', () => {
    it('distinguishes unknown from explicit zero, keeps cents and rejects unsafe/negative inputs', () => {
        expect(cents(null)).toBeNull();
        expect(cents('')).toBeNull();
        expect(cents('0.00')).toBe(0);
        expect(cents('100000.10')).toBe(10000010);
        expect(cents(-1)).toBeNull();
        expect(cents(Infinity)).toBeNull();
        expect(cents(Number.MAX_SAFE_INTEGER)).toBeNull();
        expect(money(null)).toBe('Belum diketahui');
    });
    it('locks edit/delete when a journal or student exists and never exposes finalization for cancelled/registered', () => {
        expect(editable(row)).toBe(false);
        expect(editable({ ...row, jurnal_sitin: null })).toBe(true);
        expect(editable({ ...row, jurnal_sitin: null, siswa: 2 })).toBe(false);
        expect(finalizable(row)).toBe(true);
        expect(finalizable({ ...row, status: 'BATAL' })).toBe(false);
        expect(finalizable({ ...row, status: 'REGISTERED', siswa: 2 })).toBe(false);
    });
    it('offers only eligible unpaid positive components and blocks ambiguous legacy data', () => {
        expect(components(row)).toEqual([expect.objectContaining({ kode: 'FORMULIR', nominal: 10000010, paid: false }), expect.objectContaining({ kode: 'SITIN', paid: true })]);
        expect(receivable(row)).toBe(true);
        expect(receivable({ ...row, perlu_rekonsiliasi: true, biaya_formulir: null })).toBe(false);
        expect(receivable({ ...row, status: 'BATAL' })).toBe(false);
        expect(receivable({ ...row, sisa_biaya: '0' })).toBe(false);
        expect(receivable({ ...row, formulir_terbayar: true })).toBe(false);
    });
});
