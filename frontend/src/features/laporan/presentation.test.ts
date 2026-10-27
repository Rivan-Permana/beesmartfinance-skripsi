import { describe, expect, it } from 'vitest'
import type { SaldoRow } from '@/types/api'
import { budgetPercent, groupBalance, ledgerBalances, reportFiltersChanged, reportMoney, reportPeriod, sumAmounts, type ReportFilters } from './presentation'
const scope:ReportFilters={tahun:2026,bulan:2,account:null}
function account(normal:'D'|'K',amount:string):SaldoRow{return {kode_akun:'111',nama_akun:'Contoh',posisi_normal:normal,total_debit:'0',total_kredit:'0',saldo_akhir:amount}}
describe('report financial presentation',()=>{
  it('separates cumulative year scopes from annual and monthly reports',()=>{
    expect(reportPeriod('neraca',scope)).toBe('Hingga 31 Desember 2026')
    expect(reportPeriod('pk',scope)).toBe('Hingga 31 Desember 2026')
    expect(reportPeriod('lr',scope)).toBe('Januari–Desember 2026')
    expect(reportPeriod('ra',scope)).toBe('Tahun anggaran 2026')
    expect(reportPeriod('bb',scope)).toBe('Februari 2026')
    expect(reportFiltersChanged('neraca',{...scope,bulan:3},scope)).toBe(false)
    expect(reportFiltersChanged('bb',{...scope,bulan:3},scope)).toBe(true)
  })
  it('adds decimal cents, preserves negatives, and distinguishes unknown from zero',()=>{
    expect(sumAmounts(['0.10',0.2,'-0.05'])).toBe(0.25)
    expect(sumAmounts([])).toBe(0)
    for(const value of [null,undefined,'',NaN,Infinity,'unknown','0.001']){
      expect(reportMoney(value)).toBe('Belum diketahui')
      expect(sumAmounts(['10',value])).toBeNull()
    }
    expect(reportMoney('0.00')).toBe('Rp 0')
    expect(reportMoney('-25.50')).toContain('25,5')
  })
  it('subtracts contra accounts when totaling assets and respects negative normal balances',()=>{
    expect(groupBalance([account('D','1000.25'),account('K','100.00')],'D')).toBe(900.25)
    expect(groupBalance([account('K','1000.25'),account('D','100.00')],'K')).toBe(900.25)
    expect(groupBalance([account('K','-25.50')],'K')).toBe(-25.5)
  })
  it('carries server opening rows into debit and credit normal ledger balances',()=>{
    const rows=[{tanggal:'2026-02-01',no_bukti:'SALDO-AWAL',keterangan:'Saldo awal periode',debit:'1000.25',kredit:'0.00'},{tanggal:'2026-02-02',no_bukti:'BKT-001',keterangan:null,debit:'0.10',kredit:'0.00'},{tanggal:'2026-02-02',no_bukti:'BKT-002',keterangan:null,debit:'0.20',kredit:'50.00'}]
    expect(ledgerBalances(rows,'D').map(row=>row.saldo)).toEqual([1000.25,1000.35,950.55])
    expect(ledgerBalances(rows.map(row=>({...row,debit:row.kredit,kredit:row.debit})),'K').map(row=>row.saldo)).toEqual([1000.25,1000.35,950.55])
    expect(ledgerBalances(rows,undefined).map(row=>row.saldo)).toEqual([null,null,null])
  })
  it('does not recover a made-up ledger balance after an unknown amount',()=>{
    const rows=[{tanggal:'2026-02-01',no_bukti:'BKT-1',keterangan:null,debit:'invalid',kredit:'0'},{tanggal:'2026-02-02',no_bukti:'BKT-2',keterangan:null,debit:'10',kredit:'0'}]
    expect(ledgerBalances(rows,'D').map(row=>row.saldo)).toEqual([null,null])
  })
  it('labels budget ratios honestly when zero, almost exhausted or overspent',()=>{
    expect(budgetPercent('0','100')).toBeNull()
    expect(budgetPercent('100',null)).toBeNull()
    expect(budgetPercent('100','99.60')).toEqual({value:99.6,label:'99,6%'})
    expect(budgetPercent('100','150')).toEqual({value:100,label:'150%'})
  })
})
