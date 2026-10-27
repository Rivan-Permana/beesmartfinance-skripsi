import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import DatePicker from 'primevue/datepicker'
import { nextTick } from 'vue'
import { primevueLocale } from '@/core/primevueLocale'
import PegawaiFormDialog from './PegawaiFormDialog.vue'
import { staffAttendance, staffChanged, staffNeedsSave, staffStatus, setStaffStatus, staffPeriod } from './staff'
vi.mock('@/core/api',()=>({api:{get:vi.fn()}}))
import { api } from '@/core/api'
import { absenPegawaiApi, pegawaiApi } from './api'
describe('pegawai and attendance contract',()=>{
  it('loads all date-filtered attendance pages and offers fresh employee detail',async()=>{
    vi.mocked(api.get).mockReset().mockResolvedValueOnce({data:{results:[{id:1}],next:'next'}}).mockResolvedValueOnce({data:{results:[{id:2}],next:null}})
    expect(await absenPegawaiApi.listAll({tanggal:'2026-10-18'})).toEqual([{id:1},{id:2}])
    expect(api.get).toHaveBeenNthCalledWith(2,'/absen-pegawai/',{params:{page_size:200,tanggal:'2026-10-18',page:2}})
    vi.mocked(api.get).mockResolvedValueOnce({data:{id:3,nama:'Contoh'}})
    expect(await pegawaiApi.get(3)).toMatchObject({id:3,nama:'Contoh'})
  })
  it('preserves historical mixed flags until explicitly changed and allows deleting a stored record',()=>{
    const mixed=staffAttendance(1,{id:7,pegawai:1,tanggal:'2026-10-18',hadir:1,izin:1,sakit:0,terlambat:0})
    expect(staffStatus(mixed)).toBe('mixed')
    expect(staffNeedsSave(mixed,mixed)).toBe(false)
    const none=setStaffStatus(mixed,'none')
    expect(staffStatus(none)).toBe('none')
    expect(staffChanged(none,mixed)).toBe(true)
    expect(staffNeedsSave(none,mixed)).toBe(true)
    expect(mixed.izin).toBe(1)
  })
  it('rejects inverted work dates and saves local dates without changing the linked user',async()=>{
    const row={id:1,nama:'Pegawai Contoh',nip:'X-1',jabatan:'Guru',nomor_hp:null,alamat:null,status_aktif:false,tanggal_mulai_kerja:'2026-10-18',tanggal_selesai_kerja:null,user:4}
    const view=mount(PegawaiFormDialog,{global:{plugins:[[PrimeVue,{unstyled:true,locale:primevueLocale}],ConfirmationService]},props:{row,saving:false,error:'',uncertain:false,modelValue:true}})
    try{
      await nextTick()
      const dates=view.findAllComponents(DatePicker)
      dates[1]!.vm.$emit('update:modelValue',new Date(2026,8,1))
      await nextTick();await view.get('form').trigger('submit')
      expect(view.emitted('save')).toBeUndefined()
      dates[1]!.vm.$emit('update:modelValue',new Date(2026,10,3))
      await nextTick();await view.get('form').trigger('submit')
      expect(view.emitted('save')?.[0]?.[0]).toMatchObject({nama:'Pegawai Contoh',status_aktif:false,tanggal_mulai_kerja:'2026-10-18',tanggal_selesai_kerja:'2026-11-03'})
      expect(view.emitted('save')?.[0]?.[0]).not.toHaveProperty('user')
    }finally{view.unmount()}
  })
  it('distinguishes unsaved default Hadir from a confirmed record',()=>{
    const initial=staffAttendance(2)
    expect(staffNeedsSave(initial,initial)).toBe(true)
    const cleared=setStaffStatus(initial,'none')
    expect(staffNeedsSave(cleared,initial)).toBe(false)
    expect(staffPeriod({tanggal_mulai_kerja:'2026-10-18',tanggal_selesai_kerja:'2026-11-03'} as never)).toBe('18/10/2026 – 03/11/2026')
  })
})
