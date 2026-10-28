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
  nama_panggilan: null, jenis_kelamin: null, tempat_lahir: null,
  diskon_kategori: [], diskon_nominal: "0.00", uang_masuk: null, uang_kegiatan: null,
  uang_pengembangan: null, uang_seragam: null, biaya_masuk: null,
}
const global = { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }]] }

describe("student workspace", () => {
  it("keeps personal details and the birth date as a local calendar date", async () => {
    const view = mount(SiswaFormDialog, { global, props: { modelValue: true, student: { ...student, nama_panggilan: "Alya", jenis_kelamin: "P", tempat_lahir: "Bandung" }, kelompok: [] } })
    await nextTick()
    expect(view.get('#siswa-nickname').element).toHaveProperty('value', 'Alya')
    expect(view.get('#siswa-birthplace').element).toHaveProperty('value', 'Bandung')
    await view.get('#siswa-nickname').setValue("  Lya ")
    await view.get('#siswa-birthplace').setValue(" ")
    await view.get('form').trigger('submit')
    expect(view.emitted('save')?.[0]?.[0]).toMatchObject({ nama_panggilan: "Lya", jenis_kelamin: "P", tempat_lahir: null, tanggal_lahir: "2020-01-01" })
    view.unmount()
  })
  it("starts filtered to the group opened from the Kelompok menu and shows nickname and gender", async () => {
    const rows = [{ ...student, nama_panggilan: "Alya", jenis_kelamin: "P" as const }, { ...student, id: 2, nama: "Bima", kelompok: 2 }]
    const view = mount(SiswaDirectory, { global, props: { rows, initialGroup: 2, kelompok: [{ id: 1, nama: "Melati", jenjang: 1 }, { id: 2, nama: "Mawar", jenjang: 1 }] } })
    expect(view.get('.directory-results').text()).toContain("1–1 dari 1 siswa yang cocok")
    expect(view.text()).toContain("Bima")
    expect(view.text()).not.toContain("Alya")
    await view.get('.directory-results button').trigger('click')
    expect(view.text()).toContain("Panggilan Alya · Perempuan · NIS LM-001")
    view.unmount()
  })
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
  it("keeps entry fees and discount in the payload and blocks a discount above the total", async () => {
    const view = mount(SiswaFormDialog, { global, props: { modelValue: true, student: { ...student, uang_masuk: "3200000.00", uang_seragam: "400000.00", diskon_kategori: ["SIB"], diskon_nominal: "500000.00" }, kelompok: [] } })
    await nextTick()
    expect(view.get('.siswa-fee-total').text()).toContain("3.100.000")
    expect((view.get('#diskon-SIB').element as HTMLInputElement).checked).toBe(true)
    await view.get('#diskon-PG').setValue(true)
    await view.get('form').trigger('submit')
    expect(view.emitted('save')?.[0]?.[0]).toMatchObject({ uang_masuk: "3200000.00", uang_seragam: "400000.00", uang_kegiatan: null, diskon_nominal: "500000.00", diskon_kategori: ["SIB", "PG"] })
    await view.setProps({ student: { ...student, uang_masuk: "100000.00", diskon_nominal: "500000.00" }, modelValue: false })
    await view.setProps({ modelValue: true })
    await view.get('form').trigger('submit')
    expect(view.emitted('save')).toHaveLength(1)
    expect(view.get('#siswa-diskon').attributes('aria-invalid')).toBe('true')
    view.unmount()
  })
  it("shows entry-fee status and offers receipt only while a balance remains", async () => {
    const rows: Siswa[] = [
      { ...student, id: 1, nama: "Belum", biaya_masuk: { tagihan: 9, status: "SEBAGIAN", total: "3000000.00", sisa: "1000000.00" } },
      { ...student, id: 2, nama: "Lunas", biaya_masuk: { tagihan: 10, status: "LUNAS", total: "3000000.00", sisa: "0.00" } },
    ]
    const view = mount(SiswaDirectory, { global, props: { rows, kelompok: [] } })
    const buttons = view.findAll('.directory-desktop button[aria-label^="Catat penerimaan"]')
    expect(buttons).toHaveLength(1)
    expect(view.get('.directory-desktop').text()).toContain("Sisa Rp")
    await buttons[0]!.trigger('click')
    expect(view.emitted('receive')?.[0]?.[0]).toMatchObject({ id: 1 })
    const readonly = mount(SiswaDirectory, { global, props: { rows, kelompok: [], readonly: true } })
    expect(readonly.findAll('button[aria-label^="Catat penerimaan"]')).toHaveLength(0)
    expect(readonly.text()).toContain("Sebagian")
    view.unmount(); readonly.unmount()
  })
})
