import { formatRp } from '@/core/format';
import type { PendaftaranSiswa, PendaftaranSiswaStatus } from '@/types/api';
export const statusOptions = [{ label: 'Semua status', value: null }, { label: 'Sit-in / observasi', value: 'TRIAL' }, { label: 'Terdaftar', value: 'REGISTERED' }, { label: 'Batal', value: 'BATAL' }];
export const statusLabels: Record<PendaftaranSiswaStatus, string> = { TRIAL: 'Sit-in / observasi', REGISTERED: 'Terdaftar', BATAL: 'Batal' };
export const statusSeverity = { TRIAL: 'warn', REGISTERED: 'success', BATAL: 'danger' } as const;
export function cents(value: string | number | null | undefined): number | null {
    if (value == null || value === '')
        return null;
    const number = Number(value), result = Math.round(number * 100);
    return Number.isFinite(number) && number >= 0 && Number.isSafeInteger(result) ? result : null;
}
export function money(value: string | number | null | undefined) {
    return cents(value) == null ? 'Belum diketahui' : formatRp(value);
}
export function dateLabel(iso: string) {
    return new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(iso + 'T12:00:00'));
}
export function editable(row: PendaftaranSiswa) {
    return row.status === 'TRIAL' && !row.siswa && !row.jurnal_sitin && !row.jurnal_pendaftaran;
}
export function finalizable(row: PendaftaranSiswa) {
    return row.status === 'TRIAL' && !row.siswa;
}
export function components(row: PendaftaranSiswa) {
    return [
        { kode: 'FORMULIR' as const, label: 'Formulir', nominal: cents(row.biaya_formulir), paid: row.formulir_terbayar },
        { kode: 'SITIN' as const, label: 'Sit-in / observasi', nominal: cents(row.biaya_sitin), paid: row.sitin_terbayar },
    ];
}
export function receivable(row: PendaftaranSiswa) {
    return row.status !== 'BATAL' && !row.perlu_rekonsiliasi && (cents(row.sisa_biaya) ?? 0) > 0 && components(row).some(item => item.paid === false && (item.nominal ?? 0) > 0);
}
export const journalLabels: Record<string, string> = { DRAFT: 'Menunggu pencatatan Finance', PENDING: 'Menunggu persetujuan', POSTED: 'Tercatat di buku besar', VOID: 'Dibatalkan' };
