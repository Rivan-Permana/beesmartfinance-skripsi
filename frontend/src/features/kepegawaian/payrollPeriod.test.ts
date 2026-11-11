import { flushPromises, mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import { describe, expect, it, vi } from 'vitest'
import { payrollSalary } from '@/design-system/payroll-fixtures'
import type { Gaji, GajiPeriodeHasil } from '@/types/api'
import GajiPeriodePanel from './GajiPeriodePanel.vue'
import { gajiApi } from './api'
import { payrollPeriods, slipState } from './payroll'

vi.mock('./api', () => ({ gajiApi: { postingPeriode: vi.fn(), setujuiPeriode: vi.fn() } }))

const slip = (extra: Partial<Gaji>): Gaji => ({ ...payrollSalary, ...extra })
const hasil = (extra: Partial<GajiPeriodeHasil>): GajiPeriodeHasil => ({
  disimpan: false, jumlah: 2, berhasil: 0, gagal: 0, total_netto: '2000.00',
  hasil: [{ gaji: 1, pegawai: 1, nama: 'Pegawai A', netto: '1000.00', status: 'siap', pesan: null },
          { gaji: 2, pegawai: 2, nama: 'Pegawai B', netto: '1000.00', status: 'siap', pesan: null }], ...extra,
})

describe('status dan periode slip gaji', () => {
  it('membedakan belum dijurnal, menunggu persetujuan, dan tercatat', () => {
    expect(slipState({ jurnal: null, jurnal_status: null }).label).toBe('Belum dijurnal')
    expect(slipState({ jurnal: 'j', jurnal_status: 'PENDING' }).label).toBe('Menunggu persetujuan')
    expect(slipState({ jurnal: 'j', jurnal_status: 'POSTED' }).label).toBe('Tercatat')
  })
  it('mengelompokkan slip per periode, terbaru dulu', () => {
    const rows = [slip({ id: 1, periode_bulan: 12, periode_tahun: 2026, jurnal: 'j', jurnal_status: 'POSTED' }),
                  slip({ id: 2, periode_bulan: 1, periode_tahun: 2027 }),
                  slip({ id: 3, periode_bulan: 1, periode_tahun: 2027, jurnal: 'j', jurnal_status: 'PENDING' })]
    expect(payrollPeriods(rows).map(p => [p.label, p.belum, p.menunggu])).toEqual([['Januari 2027', 1, 1], ['Desember 2026', 0, 0]])
  })
})

describe('panel jurnal gaji per periode', () => {
  const pasang = (mode: 'finance' | 'principal') => mount(GajiPeriodePanel, {
    props: { mode, rows: [slip({ id: 1, periode_bulan: 1, periode_tahun: 2027 }), slip({ id: 2, periode_bulan: 1, periode_tahun: 2027, pegawai: 2 })] },
    global: { plugins: [[PrimeVue, { unstyled: true }], ToastService], stubs: { Dialog: { props: ['visible'], template: "<div v-if='visible'><slot /><slot name='footer' /></div>" } } },
  })

  it('Keuangan memeriksa pratinjau dulu, lalu memproses dan menampilkan slip yang gagal', async () => {
    vi.mocked(gajiApi.postingPeriode).mockReset()
      .mockResolvedValueOnce(hasil({}))
      .mockResolvedValueOnce(hasil({ disimpan: true, berhasil: 1, gagal: 1, total_netto: '1000.00',
        hasil: [{ gaji: 1, pegawai: 1, nama: 'Pegawai A', netto: '1000.00', status: 'berhasil', pesan: null },
                { gaji: 2, pegawai: 2, nama: 'Pegawai B', netto: '1000.00', status: 'gagal', pesan: 'Periode sudah ditutup.' }] }))
    const view = pasang('finance')
    const tombol = view.findAll('button').find(b => b.text().includes('Posting dan ajukan 2 slip'))!
    await tombol.trigger('click'); await flushPromises()
    expect(gajiApi.postingPeriode).toHaveBeenLastCalledWith(1, 2027, false)
    expect(view.text()).toContain('Pegawai B')
    await view.findAll('button').find(b => b.text() === 'Buat dan ajukan jurnal')!.trigger('click'); await flushPromises()
    expect(gajiApi.postingPeriode).toHaveBeenLastCalledWith(1, 2027, true)
    expect(view.text()).toContain('1 berhasil')
    expect(view.text()).toContain('Periode sudah ditutup.')
    expect(view.emitted('done')).toHaveLength(1)
    view.unmount()
  })

  it('Kepsek tidak punya tombol bila tidak ada jurnal yang menunggu', () => {
    const view = pasang('principal')
    const tombol = view.findAll('button').find(b => b.text().includes('Periksa dan setujui 0 jurnal'))!
    expect(tombol.attributes('disabled')).toBeDefined()
    view.unmount()
  })
})
