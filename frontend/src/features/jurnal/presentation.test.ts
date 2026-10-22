import { describe, expect, it } from "vitest"
import { journalAccounts, journalSamples } from "@/design-system/journal-fixtures"
import { journalActions, journalFormValid, journalPayload, journalState, journalTotals, type JournalForm } from "./presentation"

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
