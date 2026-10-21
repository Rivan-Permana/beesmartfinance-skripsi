import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { primevueLocale } from '@/core/primevueLocale'
import { journalAccounts, journalSamples } from '@/design-system/journal-fixtures'
import JurnalFormDialog from './JurnalFormDialog.vue'
const global={plugins:[[PrimeVue,{unstyled:true,locale:primevueLocale}]]}
describe('journal form recovery',()=>{
  it('connects labels and preserves draft input after a server error, without resubmitting while pending',async()=>{
    const view=mount(JurnalFormDialog,{global,props:{modelValue:true,journal:journalSamples[0]!,accounts:journalAccounts}})
    await nextTick()
    expect(view.get('label[for="journal-proof"]').text()).toContain('Nomor bukti')
    await view.get('#journal-proof').setValue('BUKTI-UBAH')
    await view.get('form').trigger('submit')
    expect(view.emitted('save')?.[0]?.[0]).toMatchObject({no_bukti:'BUKTI-UBAH',tanggal:'2026-10-16',detail:[{kode_akun:'511',debit:'450000.50',kredit:'0.00'},{kode_akun:'111',debit:'0.00',kredit:'450000.50'}]})
    await view.setProps({error:'Bukti sudah digunakan.'})
    expect(view.get('#journal-proof').element).toHaveProperty('value','BUKTI-UBAH')
    expect(view.text()).toContain('Input tetap ada')
    await view.setProps({saving:true})
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toHaveLength(1)
    expect(view.get('fieldset').attributes('disabled')).toBeDefined()
    view.unmount()
  })
  it('requires a proof and at least two lines before emitting a payload',async()=>{
    const view=mount(JurnalFormDialog,{global,props:{modelValue:true,journal:null,accounts:journalAccounts}})
    await nextTick()
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toBeUndefined()
    expect(view.get('#journal-proof').attributes('aria-invalid')).toBe('true')
    expect(view.text()).toContain('Samakan total debit dan kredit')
    view.unmount()
  })
})
