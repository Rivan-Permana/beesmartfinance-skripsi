import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { primevueLocale } from '@/core/primevueLocale'
import { payrollLoan, payrollSalary, payrollStaff } from '@/design-system/payroll-fixtures'
import GajiFormDialog from './GajiFormDialog.vue'
import KasbonFormDialog from './KasbonFormDialog.vue'
import EmployeeActionDialog from './EmployeeActionDialog.vue'
const global={plugins:[[PrimeVue,{unstyled:true,locale:primevueLocale}]]}
const base={modelValue:true,optionsLoading:false,optionsError:'',saving:false,uncertain:false,error:'',staff:payrollStaff}
describe('payroll forms',()=>{
  it('keeps every salary component and local metadata, uses server-calculated loan deduction, preserves input on error',async()=>{
    const view=mount(GajiFormDialog,{global,props:{...base,row:payrollSalary,loans:[payrollLoan,{...payrollLoan,id:2,is_legacy:false,ikut_potongan:false}]}})
    try{
      await nextTick()
      await view.get('form').trigger('submit')
      const payload=view.emitted('save')?.[0]?.[0]
      expect(payload).toMatchObject({tunjangan_asuransi:'25000.25',uang_makan:'50000.50',hari_hadir:18,gaji_pokok:'4000000.10',potongan_asuransi:'10000.10'})
      expect(payload).not.toHaveProperty('potongan_pinjaman')
      expect(view.text()).toContain('tidak ikut dipotong pada slip ini')
      await view.setProps({error:'Data ditolak'})
      expect(view.findAllComponents(InputNumber).find(c=>c.props('inputId')==='salary-uang_makan')!.props('modelValue')).toBe(50000.5)
      await view.setProps({saving:true});await view.get('form').trigger('submit');expect(view.emitted('save')).toHaveLength(1)
      expect(view.get('fieldset').attributes('disabled')).toBeDefined()
    }finally{view.unmount()}
  })
  it('blocks unknown deductions and invalid amounts, preserving inactive employee on existing slip',async()=>{
    const view=mount(GajiFormDialog,{global,props:{...base,row:{...payrollSalary,pegawai:3},loans:[]}})
    try{
      await nextTick()
      expect(view.findComponent(Select).props('options')).toContainEqual(payrollStaff[2])
      await view.setProps({optionsError:'Belum dimuat'});await view.get('form').trigger('submit');expect(view.emitted('save')).toBeUndefined()
      await view.setProps({optionsError:''});view.findAllComponents(InputNumber).find(c=>c.props('inputId')==='salary-gaji_pokok')!.vm.$emit('update:modelValue',null);await nextTick();await view.get('form').trigger('submit');expect(view.emitted('save')).toBeUndefined()
    }finally{view.unmount()}
  })
  it('requires explicit loan amount/installment, sends cents and local date including zero installment',async()=>{
    const view=mount(KasbonFormDialog,{global,props:{...base,row:null}})
    try{
      await nextTick()
      await view.get('form').trigger('submit');expect(view.emitted('save')).toBeUndefined()
      view.findComponent(Select).vm.$emit('update:modelValue',1)
      view.findComponent(DatePicker).vm.$emit('update:modelValue',new Date(2026,9,18))
      view.findAllComponents(InputNumber).find(c=>c.props('inputId')==='loan-amount')!.vm.$emit('update:modelValue',1250000.25)
      view.findAllComponents(InputNumber).find(c=>c.props('inputId')==='loan-installment')!.vm.$emit('update:modelValue',0)
      await nextTick();await view.get('form').trigger('submit')
      expect(view.emitted('save')?.[0]?.[0]).toMatchObject({tanggal_pinjaman:'2026-10-18',jumlah_pinjaman:'1250000.25',angsuran_per_bulan:'0.00'})
      const date=view.get('#loan-date');await date.setValue('31/02/2026');await view.get('form').trigger('submit');expect(view.emitted('save')).toHaveLength(1)
    }finally{view.unmount()}
  })
  it('closes loan calendar on lock, retains input and forbids replay while result is uncertain',async()=>{
    const view=mount(KasbonFormDialog,{global,attachTo:document.body,props:{...base,row:payrollLoan}})
    try{
      await nextTick()
      await nextTick();await view.get('#loan-date').trigger('focus');expect(document.querySelector('[data-pc-section="panel"]')).not.toBeNull()
      await view.setProps({saving:true});expect(document.querySelector('[data-pc-section="panel"]')).toBeNull()
      await view.setProps({saving:false,uncertain:true});await view.get('form').trigger('submit');expect(view.emitted('save')).toBeUndefined()
      await view.setProps({uncertain:false,optionsError:'Pegawai belum dimuat'});await view.get('form').trigger('submit');expect(view.emitted('save')).toBeUndefined()
      expect(view.findAllComponents(InputNumber).find(c=>c.props('inputId')==='loan-amount')!.props('modelValue')).toBe(1000000.25)
    }finally{view.unmount()}
  })
  it('locks financial confirmation until fresh status is known and keeps pending non-dismissable',async()=>{
    const view=mount(EmployeeActionDialog,{global,props:{visible:true,title:'Cairkan kasbon?',label:'Contoh',amount:'Rp 1',description:'Contoh',confirmLabel:'Buat jurnal',pending:false,checking:false,error:'',uncertain:true,ready:true}})
    try{
      await nextTick()
      expect(view.findAll('button').find(b=>b.text()==='Buat jurnal')!.attributes('disabled')).toBeDefined()
      await view.setProps({uncertain:false,ready:false});expect(view.findAll('button').find(b=>b.text()==='Buat jurnal')!.attributes('disabled')).toBeDefined()
      await view.setProps({ready:true,pending:true});expect(view.findComponent({name:'Dialog'}).props('closable')).toBe(false)
    }finally{view.unmount()}
  })
})
