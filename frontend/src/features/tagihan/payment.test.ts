import { mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import { describe, expect, it } from "vitest"
import { paymentPayload, paymentTotal, paymentValid, type TagihanPaymentForm } from "./payment"
import { canEditTagihan, canPayTagihan, perluDicocokkan, tagihanState } from "./presentation"
import InvoicePreview from "./InvoicePreview.vue"
import type { StrukTagihan, Tagihan } from "@/types/api"

function form(): TagihanPaymentForm {
  return {tanggal:new Date(2026,9,16,0,5),no_bukti:" BKT-01 ",akun_kas:"111",request_id:"same-request-on-retry",alokasi:[{detail:1,label:"SPP",nominal:.1,sisa:.1},{detail:2,label:"Katering",nominal:.2,sisa:.2},{detail:3,label:"Lainnya",nominal:0,sisa:5}]}
}
describe("tagihan payment contract",()=>{
  it("sums cents and preserves local date, allocation strings and request id",()=>{
    const value=form()
    expect(paymentTotal(value)).toBe(.3)
    expect(paymentValid(value)).toBe(true)
    expect(paymentPayload(value)).toEqual({tanggal:"2026-10-16",no_bukti:"BKT-01",akun_kas:"111",request_id:"same-request-on-retry",nominal:"0.30",alokasi:[{detail:1,nominal:"0.10"},{detail:2,nominal:"0.20"}]})
    expect(paymentPayload(value).request_id).toBe(paymentPayload(value).request_id)
  })
  it("rejects invalid dates, missing proof/account, zero, non-finite, negative and overpaid allocations",()=>{
    expect(paymentValid({...form(),tanggal:new Date('invalid')})).toBe(false)
    expect(paymentValid({...form(),no_bukti:"  "})).toBe(false)
    expect(paymentValid({...form(),akun_kas:""})).toBe(false)
    for (const nominal of [0,NaN,Infinity,-1,10]) expect(paymentValid({...form(),alokasi:[{detail:1,label:"SPP",nominal,sisa:5}]})).toBe(false)
  })
  it("keeps unknown payments distinct from zero even if a reconciliation flag is missing",()=>{
    const row={status:"BELUM",perlu_rekonsiliasi:false,total_terbayar:null,sisa_tagihan:null,pembayaran:[]} as Tagihan
    expect(perluDicocokkan(row)).toBe(true)
    expect(canPayTagihan(row)).toBe(false)
    expect(canEditTagihan(row)).toBe(false)
    expect(tagihanState(row).label).toBe("Perlu dicocokkan")
  })
  it("does not print unknown payments as zero in invoice presentation",()=>{
    const invoice: StrukTagihan={no_tagihan:1,sekolah:"Contoh",siswa:"Siswa Contoh",nis:null,kelompok:null,periode:"Oktober 2026",periode_bulan:10,periode_tahun:2026,status:"SEBAGIAN",sections:[],rincian:[],total:"100000",no_jurnal:null,total_terbayar:null,sisa_tagihan:null,perlu_rekonsiliasi:false}
    const view=mount(InvoicePreview,{props:{invoice},global:{plugins:[[PrimeVue,{unstyled:true}]]}})
    expect(view.text()).toContain("Perlu dicocokkan")
    expect(view.text()).not.toContain("Dibayar: Rp 0")
    view.unmount()
  })
})
