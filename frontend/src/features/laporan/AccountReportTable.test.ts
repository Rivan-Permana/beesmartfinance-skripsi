import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { SaldoRow } from '@/types/api'
import AccountReportTable from './AccountReportTable.vue'

const account = (kode_akun: string, saldo_akhir: string): SaldoRow => ({
  kode_akun,
  nama_akun: `Akun ${kode_akun}`,
  posisi_normal: 'D',
  total_debit: '0',
  total_kredit: '0',
  saldo_akhir,
})

describe('report print detail', () => {
  it('marks only exact zero balances for print hiding while keeping totals and unknown values', () => {
    const view = mount(AccountReportTable, {
      props: {
        rows: [account('4001', '0.00'), account('4002', '-50.00'), account('4003', 'invalid')],
        caption: 'Rincian pendapatan',
        totalLabel: 'Total pendapatan',
        total: '-50.00',
        compactOnPrint: true,
      },
    })

    const rows = view.findAll('tbody tr')
    expect(rows[0]?.classes()).toContain('report-print-zero')
    expect(rows[1]?.classes()).not.toContain('report-print-zero')
    expect(rows[2]?.classes()).not.toContain('report-print-zero')
    expect(view.text()).toContain('Total pendapatan')
    expect(view.text()).toContain('Rp -50')
  })

  it('adds an empty print message when all accounts have zero balances', () => {
    const view = mount(AccountReportTable, {
      props: { rows: [account('4001', '0')], caption: 'Rincian', compactOnPrint: true },
    })
    expect(view.find('tbody tr.report-print-empty').exists()).toBe(true)
  })
})
