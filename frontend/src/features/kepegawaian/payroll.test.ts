import { describe, expect, it } from 'vitest'
import { cents, loanDeduction, loanStatus, money, sumMoney } from './payroll'
import { payrollLoan } from '@/design-system/payroll-fixtures'
describe('payroll values',()=>{
  it('distinguishes missing/unsafe amounts from explicit zero and sums cents',()=>{
    expect(cents(null)).toBeNull();expect(cents('')).toBeNull();expect(cents(-1)).toBeNull();expect(cents(Infinity)).toBeNull();expect(cents('9999999999999999')).toBeNull()
    expect(cents(0)).toBe(0);expect(sumMoney([0.1,0.2])).toBe(0.3);expect(sumMoney([0,null])).toBeNull()
    expect(money(null)).toBe('Belum diketahui');expect(money('9999999999999999.25')).toBe('Rp 9.999.999.999.999.999,25');expect(money('-0.10')).toBe('Rp -0,1')
  })
  it('mirrors server deduction: cap at remaining balance, zero installment uses full balance, skip loans not yet disbursed',()=>{
    expect(loanDeduction([payrollLoan],1)).toBe(100000)
    expect(loanDeduction([{...payrollLoan,angsuran_per_bulan:'0.00'}],1)).toBe(100000)
    expect(loanDeduction([{...payrollLoan,angsuran_per_bulan:'0.10',sisa_pinjaman:'0.20'},{...payrollLoan,id:2,angsuran_per_bulan:'0.20',sisa_pinjaman:'0.30'}],1)).toBe(0.3)
    expect(loanDeduction([{...payrollLoan,sisa_pinjaman:'bad'}],1)).toBeNull();expect(loanDeduction([payrollLoan],2)).toBe(0)
    expect(loanDeduction([payrollLoan,{...payrollLoan,id:2,is_legacy:false,ikut_potongan:false}],1)).toBe(100000)
    expect(loanStatus({jurnal:null,is_legacy:true,ikut_potongan:true}).label).toBe('Saldo legacy')
    expect(loanStatus({jurnal:'j1',is_legacy:false,ikut_potongan:false}).label).toBe('Pencairan menunggu persetujuan')
  })
})
