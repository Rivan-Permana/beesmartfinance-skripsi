import { flushPromises, mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';
import InputNumber from 'primevue/inputnumber';
import Select from 'primevue/select';
import DatePicker from 'primevue/datepicker';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick } from 'vue';
import { primevueLocale } from '@/core/primevueLocale';
import type { PendaftaranSiswa } from '@/types/api';
vi.mock('vue-router', () => ({ onBeforeRouteLeave: vi.fn(), RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } }));
vi.mock('./api', () => ({ pendaftaranSiswaApi: { listAll: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), bayar: vi.fn(), finalisasi: vi.fn(), remove: vi.fn() } }));
vi.mock('@/features/absensi/api', () => ({ jenjangApi: { listAll: vi.fn() } }));
vi.mock('@/features/jurnal/api', () => ({ coaApi: { list: vi.fn() } }));
import { pendaftaranSiswaApi } from './api';
import { jenjangApi } from '@/features/absensi/api';
import { coaApi } from '@/features/jurnal/api';
import PendaftaranListView from './PendaftaranListView.vue';
import PendaftaranFormDialog from './PendaftaranFormDialog.vue';
const row: PendaftaranSiswa = { id: 1, nama_calon: 'Calon Uji', jenjang: null, tanggal_daftar: '2026-10-01', status: 'TRIAL', biaya_sitin: '750000.25', biaya_formulir: '100000.10', biaya_pendaftaran: '0.00', total_biaya: '850000.35', total_terbayar: '750000.25', sisa_biaya: '100000.10', perlu_rekonsiliasi: false, sitin_terbayar: true, formulir_terbayar: false, jurnal_sitin: 'sitin-journal', jurnal_pendaftaran: null, pembayaran: [], siswa: null };
const global = { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }], ToastService, ConfirmationService] };
beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(pendaftaranSiswaApi.listAll).mockResolvedValue([{ ...row }]);
    vi.mocked(pendaftaranSiswaApi.get).mockResolvedValue({ ...row });
    vi.mocked(jenjangApi.listAll).mockResolvedValue([{ id: 1, kode: 'TK', nama: 'TK' }]);
    vi.mocked(coaApi.list).mockResolvedValue([{ kode_akun: '111', nama_akun: 'Kas', is_active: true, posisi_normal: 'D', sub_golongan: null, saldo_awal: '0', tanggal_saldo_awal: null }]);
});
const button = (view: ReturnType<typeof mount>, label: string) => view.findAll('button').find(b => b.text().trim() === label)!;
const number = (view: ReturnType<typeof mount>, id: string) => view.findAllComponents(InputNumber).find(c => c.props('inputId') === id)!;
async function render() {
    const view = mount(PendaftaranListView, { global });
    await flushPromises();
    return view;
}
async function detail(view: ReturnType<typeof mount>) {
    await view.get('[aria-label="Rincian Calon Uji"]').trigger('click');
    await flushPromises();
}
async function payment(view: ReturnType<typeof mount>) {
    await detail(view);
    await button(view, 'Catat penerimaan').trigger('click');
    await flushPromises();
}
describe('admission local workspace', () => {
    it('starts fees/SPP empty, validates before sending, and preserves zero finalization without payment', async () => {
        const view = await render();
        await button(view, 'Daftar calon baru').trigger('click');
        await flushPromises();
        expect(number(view, 'sitin').props('modelValue')).toBeNull();
        expect(number(view, 'formulir').props('modelValue')).toBeNull();
        await view.get('#admission-form').trigger('submit');
        expect(pendaftaranSiswaApi.create).not.toHaveBeenCalled();
        expect(view.text()).toContain('Isi kedua komponen');
        await button(view, 'Kembali').trigger('click');
        await flushPromises();
        await detail(view);
        await button(view, 'Finalisasi').trigger('click');
        await flushPromises();
        expect(number(view, 'spp').props('modelValue')).toBeNull();
        await view.get('#admission-final').trigger('submit');
        expect(pendaftaranSiswaApi.finalisasi).not.toHaveBeenCalled();
        number(view, 'spp').vm.$emit('update:modelValue', 0);
        await nextTick();
        vi.mocked(pendaftaranSiswaApi.finalisasi).mockResolvedValueOnce({ ...row, status: 'REGISTERED', siswa: 2 });
        vi.mocked(pendaftaranSiswaApi.get).mockResolvedValueOnce({ ...row, status: 'REGISTERED', siswa: 2 });
        await view.get('#admission-final').trigger('submit');
        await flushPromises();
        expect(pendaftaranSiswaApi.finalisasi).toHaveBeenCalledWith(1, '0.00');
        expect(pendaftaranSiswaApi.bayar).not.toHaveBeenCalled();
        view.unmount();
    });
    it('sends decimal fees/local date and keeps the form locked while pending', async () => {
        const view = await render();
        await button(view, 'Daftar calon baru').trigger('click');
        await flushPromises();
        await view.get('#nama-calon').setValue('Alya');
        number(view, 'sitin').vm.$emit('update:modelValue', 0.1);
        number(view, 'formulir').vm.$emit('update:modelValue', 0.2);
        view.findAllComponents(DatePicker).find(c => c.props('inputId') === 'tanggal')!.vm.$emit('update:modelValue', new Date(2026, 9, 18));
        await nextTick();
        let finish!: (value: PendaftaranSiswa) => void;
        vi.mocked(pendaftaranSiswaApi.create).mockReturnValueOnce(new Promise(resolve => finish = resolve));
        await view.get('#admission-form').trigger('submit');
        await view.get('#admission-form').trigger('submit');
        expect(pendaftaranSiswaApi.create).toHaveBeenCalledTimes(1);
        expect(pendaftaranSiswaApi.create).toHaveBeenCalledWith(expect.objectContaining({ biaya_sitin: '0.10', biaya_formulir: '0.20', tanggal_daftar: '2026-10-18' }));
        expect(button(view, 'Kembali').attributes('disabled')).toBeDefined();
        finish({ ...row, id: 2, nama_calon: 'Alya' });
        await flushPromises();
        view.unmount();
    });
    it('offers only unpaid components, preserves input on error, and replays an ambiguous payment unchanged', async () => {
        const view = await render();
        await payment(view);
        expect(view.get('#bayar-SITIN').attributes('disabled')).toBeDefined();
        expect((view.get('#bayar-FORMULIR').element as HTMLInputElement).checked).toBe(true);
        await view.get('#bayar-bukti').setValue('REG-001');
        view.findAllComponents(Select).find(c => c.props('inputId') === 'bayar-kas')!.vm.$emit('update:modelValue', '111');
        await nextTick();
        vi.mocked(pendaftaranSiswaApi.bayar).mockRejectedValueOnce(new Error('Response lost')).mockResolvedValueOnce({ detail: 'ok', jurnal_id: 'new', pendaftaran: { ...row, formulir_terbayar: true, sisa_biaya: '0' } });
        await view.get('#admission-payment').trigger('submit');
        await flushPromises();
        expect(view.text()).toContain('Input tetap ada');
        expect(view.get('#bayar-bukti').attributes('disabled')).toBeDefined();
        const original = vi.mocked(pendaftaranSiswaApi.bayar).mock.calls[0]![1];
        expect(original).toMatchObject({ nominal: '100000.10', komponen: ['FORMULIR'] });
        await button(view, 'Coba ulang penerimaan').trigger('click');
        await flushPromises();
        expect(pendaftaranSiswaApi.bayar).toHaveBeenLastCalledWith(1, original);
        view.unmount();
    });
    it('blocks actions until fresh detail is available, and recovers Kas/Bank separately', async () => {
        const view = await render();
        vi.mocked(pendaftaranSiswaApi.get).mockRejectedValueOnce(new Error('Unavailable'));
        await detail(view);
        expect(view.text()).toContain('Tindakan menunggu rincian terbaru');
        expect(view.findAll('button').some(b => b.text() === 'Catat penerimaan')).toBe(false);
        await button(view, 'Muat ulang rincian').trigger('click');
        await flushPromises();
        vi.mocked(coaApi.list).mockRejectedValueOnce(new Error('Kas unavailable'));
        await button(view, 'Catat penerimaan').trigger('click');
        await flushPromises();
        expect(button(view, 'Simpan penerimaan').attributes('disabled')).toBeDefined();
        await button(view, 'Muat ulang Kas/Bank').trigger('click');
        await flushPromises();
        expect(button(view, 'Simpan penerimaan').attributes('disabled')).toBeUndefined();
        view.unmount();
    });
    it('does not turn legacy unknowns into zero or offer payment/edit with receipt history', async () => {
        vi.mocked(pendaftaranSiswaApi.listAll).mockResolvedValueOnce([{ ...row, perlu_rekonsiliasi: true, biaya_formulir: null, total_biaya: null, total_terbayar: null, sisa_biaya: null }]);
        vi.mocked(pendaftaranSiswaApi.get).mockResolvedValueOnce({ ...row, perlu_rekonsiliasi: true, biaya_formulir: null, total_biaya: null, total_terbayar: null, sisa_biaya: null });
        const view = await render();
        await detail(view);
        expect(view.text()).toContain('Perlu dicocokkan');
        expect(view.findAll('button').some(b => b.text() === 'Catat penerimaan' || b.text() === 'Ubah calon' || b.text() === 'Hapus calon')).toBe(false);
        view.unmount();
    });
    it('clears stale results after list failure and provides a real retry', async () => {
        const view = await render();
        vi.mocked(pendaftaranSiswaApi.listAll).mockRejectedValueOnce(new Error('Unavailable'));
        await button(view, 'Muat ulang daftar').trigger('click');
        await flushPromises();
        expect(view.find('.admission-table').exists()).toBe(false);
        expect(view.text()).toContain('Pendaftaran belum dapat ditampilkan');
        await button(view, 'Muat ulang pendaftaran').trigger('click');
        await flushPromises();
        expect(view.get('.admission-table').text()).toContain('Calon Uji');
        view.unmount();
    });
});

describe('row-level edit and delete actions', () => {
    it('shows Ubah/Hapus on rows still editable and hides them once a receipt exists', async () => {
        const fresh = { ...row, id: 2, nama_calon: 'Calon Baru', jurnal_sitin: null, sitin_terbayar: false, total_terbayar: '0.00' };
        vi.mocked(pendaftaranSiswaApi.listAll).mockResolvedValue([{ ...row }, fresh]);
        vi.mocked(pendaftaranSiswaApi.remove).mockResolvedValue(undefined as never);
        const view = await render();
        expect(view.findAll('[aria-label="Ubah Calon Baru"]').length).toBeGreaterThan(0);
        expect(view.findAll('[aria-label="Ubah Calon Uji"]')).toHaveLength(0);
        await view.get('[aria-label="Ubah Calon Baru"]').trigger('click');
        await flushPromises();
        const form = view.findComponent(PendaftaranFormDialog);
        expect(form.props('modelValue')).toBe(true);
        expect(form.props('row')).toMatchObject({ id: 2 });
        view.unmount();
    });
});
