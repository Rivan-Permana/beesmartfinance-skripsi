import { describe, expect, it } from "vitest"
import { journalAccounts, journalSamples } from "@/design-system/journal-fixtures"
import { journalActions, journalFormValid, journalPayload, journalState, journalTotals, petunjukKode, resolveKodePengeluaran, type JournalForm } from "./presentation"
import type { KodePengeluaran } from "@/types/api"

const finance={finance:true,principal:false,userId:1}
const principal={finance:false,principal:true,userId:2}
function form():JournalForm{return {no_bukti:' BKT-001 ',tanggal:new Date(2026,9,16),keterangan:'Desimal',detail:[{kode_akun:'511',debit:0.1,kredit:0},{kode_akun:'512',debit:0.2,kredit:0},{kode_akun:'111',debit:0,kredit:0.3}]}}
describe('journal workflow contracts',()=>{
  it('balances decimal amounts in cents and retains the local calendar date in payloads',()=>{
    const current=form()
    expect(journalTotals(current.detail)).toEqual({debit:0.3,kredit:0.3,balanced:true})
    expect(journalFormValid(current,journalAccounts)).toBe(true)
    expect(journalPayload(current)).toMatchObject({no_bukti:'BKT-001',tanggal:'2026-10-16',detail:[{kode_akun:'511',debit:'0.10',kredit:'0.00'},{kode_akun:'512',debit:'0.20',kredit:'0.00'},{kode_akun:'111',debit:'0.00',kredit:'0.30'}]})
  })
  it('rejects invalid dates, inactive accounts, negatives, double-sided lines and unbalanced journals',()=>{
    const current=form()
    for(const change of [ {tanggal:new Date('invalid')}, {no_bukti:' '}, {detail:[{kode_akun:'599',debit:1,kredit:0},{kode_akun:'111',debit:0,kredit:1}]}, {detail:[{kode_akun:'511',debit:-1,kredit:0},{kode_akun:'111',debit:0,kredit:-1}]}, {detail:[{kode_akun:'511',debit:1,kredit:1},{kode_akun:'111',debit:0,kredit:0}]}, {detail:[{kode_akun:'511',debit:0.1,kredit:0},{kode_akun:'111',debit:0,kredit:0.2}]} ])expect(journalFormValid({...current,...change},journalAccounts)).toBe(false)
  })
  it('does not turn invalid or over-precision amounts into zero',()=>{
    for(const value of ['', 'invalid', Number.NaN, Number.POSITIVE_INFINITY, -1, 0.001])expect(journalTotals([{debit:value,kredit:0}])).toBeNull()
    expect(journalTotals([])?.balanced).toBe(false)
  })
  it('keeps manual editing separate from automatic posting and submission',()=>{
    expect(journalActions(journalSamples[0]!,finance)).toEqual(['edit','remove','catat'])
    expect(journalActions(journalSamples[1]!,finance)).toEqual(['catat','cancel'])
    expect(journalActions(journalSamples[6]!,finance)).toEqual(['submit'])
    expect(journalActions({...journalSamples[6]!,tipe_sumber:'AUTO_PAYROLL',status:'PENDING'},finance)).toEqual(['cancelDraft'])
    expect(journalActions(journalSamples[4]!,finance)).toEqual([])
  })
  it('blocks own approval, reconciliation and direct-post journals for the principal',()=>{
    expect(journalActions(journalSamples[2]!,principal)).toEqual(['approve','reject'])
    expect(journalActions(journalSamples[5]!,principal)).toEqual([])
    expect(journalActions({...journalSamples[2]!,perlu_rekonsiliasi:true},principal)).toEqual([])
    expect(journalActions({...journalSamples[2]!,can_finance_post:true},principal)).toEqual([])
    expect(journalActions(journalSamples[2]!,{...principal,userId:undefined})).toEqual([])
    expect(journalActions(journalSamples[4]!,principal)).toEqual(['void'])
  })
  it('keeps reconciled status visible and prevents actions for deleted or unauthorized records',()=>{
    expect(journalState(journalSamples[3]!)).toMatchObject({label:'Perlu dicocokkan'})
    expect(journalActions(journalSamples[3]!,finance)).toEqual([])
    expect(journalActions({...journalSamples[0]!,is_deleted:true},finance)).toEqual([])
    expect(journalActions(journalSamples[0]!,{finance:false,principal:false,userId:3})).toEqual([])
  })
})

describe("resolveKodePengeluaran", () => {
  const code = (kode: string, unit: KodePengeluaran["unit"], akun: string | null, aktif = true): KodePengeluaran =>
    ({ id: Math.random(), kode, unit, nama: "", akun, akun_nama: akun ? "Akun " + akun : null, aktif })
  const codes = [code("PLN", "UMUM", "5406"), code("AB3", "TK", "5112"), code("AB3", "PG", "5212"), code("DVD", "UMUM", null), code("OLD", "UMUM", "5401", false)]
  it("memilih kode umum, kode per unit, dan menolak kode ambigu", () => {
    expect(resolveKodePengeluaran(" pln ", codes)).toMatchObject({ status: "ok", kode: { akun: "5406" } })
    expect(resolveKodePengeluaran("ab3 pg", codes)).toMatchObject({ status: "ok", kode: { akun: "5212" } })
    expect(resolveKodePengeluaran("PLN TK", codes)).toMatchObject({ status: "ok", kode: { akun: "5406" } })
    expect(resolveKodePengeluaran("AB3", codes)).toEqual({ status: "ambiguous", pilihan: ["AB3 TK", "AB3 PG"] })
  })
  it("membedakan kode belum dipetakan, nonaktif, dan kosong", () => {
    expect(resolveKodePengeluaran("DVD", codes).status).toBe("unmapped")
    expect(resolveKodePengeluaran("OLD", codes).status).toBe("unknown")
    expect(resolveKodePengeluaran("XYZ", codes).status).toBe("unknown")
    expect(resolveKodePengeluaran("  ", codes).status).toBe("empty")
  })
  it("memberi petunjuk netral untuk kode yang akunnya dipilih per transaksi", () => {
    const sentra = { ...code("STR", "TK", null), nama: "Sentra" }
    expect(petunjukKode("str tk", [...codes, sentra])).toEqual({ warn: false, text: "STR TK (Sentra) tidak punya akun tetap. Pilih akun Sentra yang sesuai untuk transaksi ini." })
    expect(petunjukKode("PLN", codes)).toEqual({ warn: false, text: "PLN → 5406 Akun 5406" })
    expect(petunjukKode("AB3", codes)?.warn).toBe(true)
    expect(petunjukKode("XYZ", codes)?.warn).toBe(true)
    expect(petunjukKode("", codes)).toBeNull()
  })
})
