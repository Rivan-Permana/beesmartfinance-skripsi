import { flushPromises, mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import Select from 'primevue/select'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { primevueLocale } from '@/core/primevueLocale'
import type { Coa, SaldoRow } from '@/types/api'
vi.mock('./api',()=>({laporanApi:{neracaSaldo:vi.fn(),labaRugi:vi.fn(),posisiKeuangan:vi.fn(),realisasiAnggaran:vi.fn(),bukuBesar:vi.fn()}}))
vi.mock('@/features/jurnal/api',()=>({coaApi:{list:vi.fn()}}))
vi.mock('@/core/export',()=>({downloadCsv:vi.fn()}))
import { coaApi } from '@/features/jurnal/api'
import { downloadCsv } from '@/core/export'
import { laporanApi } from './api'
import LaporanView from './LaporanView.vue'
const row:SaldoRow={kode_akun:'111',nama_akun:'Kas awal contoh',posisi_normal:'D',total_debit:'1000.25',total_kredit:'0.00',saldo_akhir:'1000.25'}
const account:Coa={kode_akun:'411',nama_akun:'Pendapatan contoh',posisi_normal:'K',is_active:false,sub_golongan:null,saldo_awal:'0',tanggal_saldo_awal:null}
const global={plugins:[[PrimeVue,{unstyled:true,locale:primevueLocale}]]}
beforeEach(()=>{
  vi.clearAllMocks()
  vi.mocked(laporanApi.neracaSaldo).mockResolvedValue([row])
  vi.mocked(laporanApi.labaRugi).mockResolvedValue({pendapatan:[{...row,nama_akun:'Pendapatan laporan'}],beban:[],total_pendapatan:'1000.25',total_beban:'0',laba_rugi:'1000.25'})
  vi.mocked(laporanApi.posisiKeuangan).mockResolvedValue({aset:[row],liabilitas:[],ekuitas:[]})
  vi.mocked(laporanApi.realisasiAnggaran).mockResolvedValue([])
  vi.mocked(laporanApi.bukuBesar).mockResolvedValue([{tanggal:'2026-02-01',no_bukti:'SALDO-AWAL',keterangan:'Saldo awal periode',debit:'0.00',kredit:'1000.25'}])
  vi.mocked(coaApi.list).mockResolvedValue([account])
})
function button(view:ReturnType<typeof mount>,text:string){return view.findAll('button').find(item=>item.text().trim()===text)!}
function selection(view:ReturnType<typeof mount>,id:string){return view.findAllComponents(Select).find(item=>item.props('inputId')===id)!}
async function tab(view:ReturnType<typeof mount>,name:string){await view.findAll('[role="tab"]').find(item=>item.text()===name)!.trigger('click');await flushPromises()}
describe('report result scope and recovery',()=>{
  it('keeps titles and CSV on the applied year until the next result succeeds',async()=>{
    const view=mount(LaporanView,{global});await flushPromises()
    const year=new Date().getFullYear()
    selection(view,'report-year').vm.$emit('update:modelValue',year-1);await nextTick()
    expect(view.text()).toContain(`Hingga 31 Desember ${year}`)
    expect(view.text()).toContain('Pilihan belum diterapkan')
    await button(view,'Unduh CSV').trigger('click')
    expect(downloadCsv).toHaveBeenLastCalledWith(`neraca-saldo-${year}.csv`,expect.any(Array),expect.arrayContaining([expect.arrayContaining(['Kas awal contoh'])]))
    await view.get('form').trigger('submit');await flushPromises()
    expect(laporanApi.neracaSaldo).toHaveBeenLastCalledWith({tahun:year-1})
    expect(view.text()).toContain(`Hingga 31 Desember ${year-1}`)
    await button(view,'Unduh CSV').trigger('click')
    expect(downloadCsv).toHaveBeenLastCalledWith(`neraca-saldo-${year-1}.csv`,expect.any(Array),expect.any(Array))
    view.unmount()
  })
  it('hides stale data and disables print/export after failure, then retries the applied scope',async()=>{
    const view=mount(LaporanView,{global});await flushPromises()
    vi.mocked(laporanApi.neracaSaldo).mockRejectedValueOnce(new Error('Laporan uji gagal'))
    selection(view,'report-year').vm.$emit('update:modelValue',new Date().getFullYear()-1);await nextTick()
    await view.get('form').trigger('submit');await flushPromises()
    expect(view.text()).toContain('Laporan belum dapat ditampilkan')
    expect(view.text()).not.toContain('Kas awal contoh')
    expect(button(view,'Cetak laporan').attributes('disabled')).toBeDefined()
    expect(button(view,'Unduh CSV').attributes('disabled')).toBeDefined()
    await button(view,'Muat ulang laporan').trigger('click');await flushPromises()
    expect(view.text()).toContain('Kas awal contoh')
    expect(button(view,'Cetak laporan').attributes('disabled')).toBeUndefined()
    view.unmount()
  })
  it('ignores a late response from a report that is no longer active',async()=>{
    let resolve!:(rows:SaldoRow[])=>void
    vi.mocked(laporanApi.neracaSaldo).mockReturnValueOnce(new Promise(done=>{resolve=done}))
    const view=mount(LaporanView,{global});await nextTick()
    await tab(view,'Laba rugi')
    expect(view.text()).toContain('Pendapatan laporan')
    resolve([{...row,nama_akun:'HASIL LAMA'}]);await flushPromises()
    expect(view.text()).not.toContain('HASIL LAMA')
    expect(view.text()).toContain('Pendapatan laporan')
    view.unmount()
  })
  it('requires an explicit ledger account and keeps monthly/normal position scope in the result',async()=>{
    const view=mount(LaporanView,{global});await flushPromises();await tab(view,'Buku besar')
    expect(laporanApi.bukuBesar).not.toHaveBeenCalled()
    await view.get('form').trigger('submit');await flushPromises()
    expect(view.text()).toContain('Pilih akun buku besar sebelum menerapkan periode.')
    selection(view,'report-account').vm.$emit('update:modelValue','411')
    selection(view,'report-month').vm.$emit('update:modelValue',2);await nextTick()
    await view.get('form').trigger('submit');await flushPromises()
    expect(laporanApi.bukuBesar).toHaveBeenLastCalledWith('411',{tahun:new Date().getFullYear(),bulan:2})
    expect(view.text()).toContain('Februari')
    expect(view.text()).toContain('411 — Pendapatan contoh')
    expect(view.text()).toContain('Rp 1.000,25')
    expect(view.text()).toContain('SALDO-AWAL')
    view.unmount()
  })
  it('shows an account failure separately from an empty account list and can recover',async()=>{
    vi.mocked(coaApi.list).mockRejectedValueOnce(new Error('Accounts unavailable'))
    const view=mount(LaporanView,{global});await flushPromises();await tab(view,'Buku besar')
    expect(view.text()).toContain('Daftar akun belum berhasil dimuat')
    expect(laporanApi.bukuBesar).not.toHaveBeenCalled()
    await button(view,'Muat ulang akun').trigger('click');await flushPromises()
    expect(view.text()).not.toContain('Daftar akun belum berhasil dimuat')
    expect(coaApi.list).toHaveBeenCalledTimes(2)
    view.unmount()
  })
})
