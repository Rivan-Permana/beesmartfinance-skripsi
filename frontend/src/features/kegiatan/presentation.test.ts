import { mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import { nextTick } from "vue"
import { describe, expect, it } from "vitest"
import { budgetUsage, realisasiValid } from "./presentation"
import KegiatanFormDialog from "./KegiatanFormDialog.vue"
import type { Kegiatan } from "@/types/api"
const activity:Kegiatan={id:1,nama:"Kegiatan contoh",akun_beban:"5101",pagu:"7000000.00",realisasi:"1200000.00",sisa_pagu:"5800000.00",rasio_utilisasi:1200000/7000000,penanggung_jawab:null,periode:1,periode_kode:"2026/2027",tanggal_mulai:"2026-10-20",tanggal_selesai:"2026-10-10",status:"BERJALAN"}
describe("kegiatan presentation",()=>{
  it("keeps zero denominators unknown and over-budget percentages honest",()=>{
    expect(budgetUsage("0",0)).toBe(null)
    expect(budgetUsage("100",NaN)).toBe(null)
    expect(budgetUsage("100",.996)?.label).toContain("99,6")
    expect(budgetUsage("100",1.25)?.label).toContain("125")
    expect(budgetUsage("100",1.25)?.value).toBe(100)
  })
  it("requires a valid date and positive realization within the remaining budget",()=>{
    const form={tanggal:new Date(2026,9,16),deskripsi:"",nominal:150000.25}
    expect(realisasiValid(form,activity)).toBe(true)
    expect(realisasiValid(form,null)).toBe(false)
    expect(realisasiValid({...form,tanggal:new Date('invalid')},activity)).toBe(false)
    for(const nominal of [0,-1,NaN,Infinity,5800000.01])expect(realisasiValid({...form,nominal},activity)).toBe(false)
  })
  it("blocks reversed dates and emits local calendar dates without losing form input",async()=>{
    const view=mount(KegiatanFormDialog,{props:{modelValue:true,activity,accounts:[],staff:[],periods:[]},global:{plugins:[[PrimeVue,{unstyled:true}]]}})
    await nextTick()
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toBeUndefined()
    expect(view.text()).toContain("Tanggal selesai tidak boleh sebelum tanggal mulai.")
    await view.get('#activity-end').setValue('31/10/2026')
    await view.get('form').trigger('submit')
    expect(view.emitted('save')?.[0]?.[0]).toMatchObject({nama:"Kegiatan contoh",pagu:"7000000.00",tanggal_mulai:"2026-10-20",tanggal_selesai:"2026-10-31"})
    await view.setProps({error:"Kegiatan belum berhasil disimpan."})
    expect(view.get('#activity-name').element).toHaveProperty('value','Kegiatan contoh')
    view.unmount()
  })
})
