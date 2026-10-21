import { mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import { primevueLocale } from "@/core/primevueLocale"
import { describe, expect, it } from "vitest"
import { nextTick } from "vue"
import SiswaDirectory from "./SiswaDirectory.vue"
import SiswaFormDialog from "./SiswaFormDialog.vue"
import type { Siswa } from "@/types/api"

const student: Siswa = {
  id: 1, nama: "Alya", nis: "LM-001", kelompok: 1, status: "aktif", spp_nominal: "750000.25",
  nama_ayah: "Kontak privat", kontak_ayah: "0811111111", nama_ibu: "", kontak_ibu: "",
  alamat: "Alamat privat", tanggal_lahir: "2020-01-01", periode: 1,
}
const global = { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }]] }

describe("student workspace", () => {
  it("clears a selected group without opening the dropdown or changing other fields, and hides clear while saving", async () => {
    const view = mount(SiswaFormDialog, { global, attachTo: document.body, props: { modelValue: true, student, kelompok: [{ id: 1, nama: 'Melati', jenjang: 1 }] } })
    await nextTick()
    const clear = view.get('button[aria-label="Hapus pilihan"]')
    expect(clear.attributes('type')).toBe('button')
    await clear.trigger('click')
    expect(document.activeElement?.id).toBe('siswa-kelompok')
    expect(view.find('[role="listbox"]').exists()).toBe(false)
    await view.get('form').trigger('submit')
    expect(view.emitted('save')?.[0]?.[0]).toMatchObject({ kelompok: null, nama: 'Alya', spp_nominal: '750000.25', kontak_ayah: '0811111111' })
    await view.setProps({ modelValue: false })
    await view.setProps({ modelValue: true, saving: true })
    expect(view.find('button[aria-label="Hapus pilihan"]').exists()).toBe(false)
    view.unmount()
  })
  it("searches displayed group names, excludes private contacts, and distinguishes filtered emptiness", async () => {
    const view = mount(SiswaDirectory, { global, props: { rows: [student], kelompok: [{ id: 1, nama: "Melati", jenjang: 1, jenjang_kode: "TK A" }] } })
    expect(view.get('#siswa-search').attributes('aria-label')).toBeUndefined()
    expect(view.get('#siswa-search').attributes('aria-describedby')).toBe('siswa-search-hint')
    expect(view.get('label[for="siswa-search"]').text()).toBe('Cari siswa')
    await view.get('#siswa-search').setValue("melati")
    expect(view.get('.directory-results').text()).toContain("1–1 dari 1")
    await view.get('#siswa-search').setValue("Kontak privat")
    expect(view.text()).toContain("Tidak ada siswa yang cocok")
    expect(view.text()).not.toContain("Mulai dari data siswa")
    view.unmount()
  })
  it("returns to the first page after a search on the second page", async () => {
    const rows = Array.from({ length: 12 }, (_, i) => ({ ...student, id: i + 1, nama: `Siswa ${i + 1}` }))
    const view = mount(SiswaDirectory, { global, props: { rows, kelompok: [] } })
    await view.get('[aria-label="Halaman berikutnya"]').trigger('click')
    expect(view.get('.directory-results').text()).toContain("11–12")
    await view.get('#siswa-search').setValue("Siswa 1")
    expect(view.get('.directory-results').text()).toContain("1–4 dari 4")
    view.unmount()
  })
  it("rejects blank names, preserves input after server failure, and retains decimal SPP", async () => {
    const view = mount(SiswaFormDialog, { global, props: { modelValue: true, student, kelompok: [] } })
    await nextTick()
    await view.get('#siswa-name').setValue("   ")
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toBeUndefined()
    expect(view.get('#siswa-name').attributes('aria-invalid')).toBe('true')
    await view.get('#siswa-name').setValue("Alya Putri")
    await view.get('form').trigger('submit')
    const payload = view.emitted('save')?.[0]?.[0]
    expect(payload).toMatchObject({ nama: "Alya Putri", spp_nominal: "750000.25", kelompok: 1, kontak_ayah: "0811111111" })
    await view.setProps({ error: "NIS sudah digunakan." })
    expect(view.get('#siswa-name').element).toHaveProperty('value', 'Alya Putri')
    expect(view.text()).toContain("Input tetap tersimpan")
    await view.setProps({ saving: true })
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toHaveLength(1)
    view.unmount()
  })
})
