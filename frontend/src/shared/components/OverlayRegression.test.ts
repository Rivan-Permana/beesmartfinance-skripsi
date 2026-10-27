import { mount } from '@vue/test-utils'
import { nextTick, type Component } from 'vue'
import { describe, expect, it } from 'vitest'
import PrimeVue from 'primevue/config'
import { primevueLocale } from '@/core/primevueLocale'
import { activityAccounts, activityPeriods, activitySamples, activityStaff } from '@/design-system/activity-fixtures'
import { billingAccounts, billingSamples } from '@/design-system/billing-fixtures'
import { journalAccounts, journalSamples } from '@/design-system/journal-fixtures'
import KegiatanFormDialog from '@/features/kegiatan/KegiatanFormDialog.vue'
import KegiatanRealisasiDialog from '@/features/kegiatan/KegiatanRealisasiDialog.vue'
import TagihanPaymentDialog from '@/features/tagihan/TagihanPaymentDialog.vue'
import JurnalFormDialog from '@/features/jurnal/JurnalFormDialog.vue'

const cases: { name: string; component: Component; props: Record<string, unknown>; dates: string[] }[] = [
  { name: 'kegiatan', component: KegiatanFormDialog, props: { activity: activitySamples[0], accounts: activityAccounts, periods: activityPeriods, staff: activityStaff }, dates: ['activity-start', 'activity-end'] },
  { name: 'realisasi', component: KegiatanRealisasiDialog, props: { target: activitySamples[0], form: { tanggal: new Date(2026, 9, 18), nominal: 100, deskripsi: '' } }, dates: ['realisasi-date'] },
  { name: 'pembayaran', component: TagihanPaymentDialog, props: { target: billingSamples[0], studentName: 'Contoh', accounts: billingAccounts, form: { tanggal: new Date(2026, 9, 18), no_bukti: 'CONTOH', akun_kas: '111', alokasi: [] } }, dates: ['tanggal-bayar'] },
  { name: 'jurnal', component: JurnalFormDialog, props: { journal: journalSamples[0], accounts: journalAccounts }, dates: ['journal-date'] },
]

describe.each(cases)('pending overlay: $name', ({ component, props, dates }) => {
  it.each(dates)('closes %s calendar while saving and retains the date after recovery', async id => {
    const view = mount(component, { attachTo: document.body, global: { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }]] }, props: { ...props, modelValue: true } })
    try {
      await nextTick()
      const before = (view.get(`#${id}`).element as HTMLInputElement).value
      await view.get(`#${id}`).trigger('focus')
      expect(document.querySelector('[data-pc-section="panel"]')).not.toBeNull()
      await view.setProps({ saving: true })
      expect(document.querySelector('[data-pc-section="panel"]')).toBeNull()
      expect(view.get(`#${id}`).attributes('disabled')).toBeDefined()
      await view.setProps({ saving: false })
      expect((view.get(`#${id}`).element as HTMLInputElement).value).toBe(before)
    } finally { view.unmount() }
  })
  if (dates[0] !== 'realisasi-date') it('closes choices while saving and restores the selected label after recovery', async () => {
    const view = mount(component, { attachTo: document.body, global: { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }]] }, props: { ...props, modelValue: true } })
    try {
      await nextTick()
      const select = view.get('[data-pc-name="select"] [role="combobox"]')
      const selected = select.text()
      await select.trigger('click')
      expect(document.querySelector('[role="listbox"]')).not.toBeNull()
      await view.setProps({ saving: true })
      expect(document.querySelector('[role="listbox"]')).toBeNull()
      expect(view.emitted('save')).toBeUndefined()
      await view.setProps({ saving: false })
      expect(view.get('[data-pc-name="select"] [role="combobox"]').text()).toBe(selected)
    } finally { view.unmount() }
  })
})
