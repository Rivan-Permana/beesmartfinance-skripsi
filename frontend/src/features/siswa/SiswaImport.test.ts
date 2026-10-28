import { flushPromises, mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import { primevueLocale } from "@/core/primevueLocale"
import { describe, expect, it, vi } from "vitest"
import type { ImporBiodataHasil, ImporSppHasil } from "@/types/api"
import SiswaImportDialog from "./SiswaImportDialog.vue"
import SppImportDialog from "./SppImportDialog.vue"
import { identitasSiswa, sppBelumDiisi, usiaSiswa } from "./presentation"

const preview: ImporBiodataHasil = {
  disimpan: false,
  ringkasan: { baru: 1, ubah: 1, sama: 0, galat: 1, peringatan: 0 },
  kelas: [{ kelas: "BU MAWAR", jumlah: 3, kelompok: 2 }],
  baris: [
    { baris: 6, kelas: "BU MAWAR", nama: "Anak Satu", aksi: "baru", siswa: null, peringatan: [], galat: null, perubahan: {}, nilai: { jenis_kelamin: "P", tanggal_lahir: "2021-11-24", alamat: "Jl. Melati No. 5 RT 004/RW 003" } },
    { baris: 7, kelas: "BU MAWAR", nama: "Anak Dua", aksi: "ubah", siswa: 9, peringatan: [], galat: null, perubahan: { kelompok: [1, 2], kontak_ayah: [null, "081255556666"] }, nilai: {} },
    { baris: 8, kelas: "BU MAWAR", nama: "Anak Tiga", aksi: "galat", siswa: null, peringatan: [], galat: "Jenis kelamin 'x' harus L atau P.", perubahan: {}, nilai: {} },
  ],
}
const imporBiodata = vi.fn(async (_file: File, _map: Record<string, number | null> | null, simpan: boolean) => ({ ...preview, disimpan: simpan }))
const sppPreview: ImporSppHasil = {
  disimpan: false, diisi: 0,
  ringkasan: { isi: 1, sama: 0, beda: 1, cek: 1, galat: 0 },
  baris: [
    { baris: 4, nama: "Anak Baru", kelas: "TK A", aksi: "isi", siswa: 1, spp_lama: "0.00", spp_baru: "1350000.00", nilai: [1350000], alasan: null },
    { baris: 5, nama: "Anak Beda", kelas: "TK B", aksi: "beda", siswa: 2, spp_lama: "1300000.00", spp_baru: "1350000.00", nilai: [1350000], alasan: null },
    { baris: 6, nama: "Anak Variasi", kelas: "TK B", aksi: "cek", siswa: 3, spp_lama: "0.00", spp_baru: "1300000.00", nilai: [650000, 1300000], alasan: "Nominal SPP berbeda antar bulan." },
  ],
}
const imporSpp = vi.fn(async (_file: File, simpan: boolean) => ({ ...sppPreview, disimpan: simpan, diisi: simpan ? 1 : 0 }))
vi.mock("./api", () => ({ siswaApi: {
  imporBiodata: (...args: Parameters<typeof imporBiodata>) => imporBiodata(...args),
  imporSpp: (...args: Parameters<typeof imporSpp>) => imporSpp(...args),
} }))
const global = { plugins: [[PrimeVue, { unstyled: true, locale: primevueLocale }]] }

describe("student biodata import", () => {
  it("computes age from the birth date and flags active students without SPP", () => {
    const today = new Date(2026, 9, 28)
    expect(usiaSiswa("2021-11-24", today)).toBe("4 tahun 11 bulan")
    expect(usiaSiswa("2026-05-30", today)).toBe("4 bulan")
    expect(usiaSiswa("2027-01-01", today)).toBeNull()
    expect(identitasSiswa({ nama_panggilan: null, jenis_kelamin: "L", nis: null, tanggal_lahir: "2021-10-28" }, today)).toBe("Laki-laki · 5 tahun 0 bulan · NIS belum diisi")
    expect(sppBelumDiisi({ status: "aktif", spp_nominal: "0.00" })).toBe(true)
    expect(sppBelumDiisi({ status: "lulus", spp_nominal: "0.00" })).toBe(false)
    expect(sppBelumDiisi({ status: "aktif", spp_nominal: "850000.00" })).toBe(false)
  })
  it("previews a CSV, shows changes and problems, then saves with the chosen group mapping", async () => {
    const view = mount(SiswaImportDialog, { global, attachTo: document.body, props: { modelValue: true, kelompok: [{ id: 1, nama: "Lama", jenjang: 1 }, { id: 2, nama: "Bu Mawar 26/27", jenjang: 1, jenjang_kode: "TKA" }] } })
    await flushPromises()
    const input = document.querySelector<HTMLInputElement>("#impor-berkas")!
    const file = new File(["Kelas,No.,Nama Siswa"], "biodata.csv", { type: "text/csv" })
    Object.defineProperty(input, "files", { value: [file] })
    input.dispatchEvent(new Event("change"))
    await flushPromises()
    expect(imporBiodata).toHaveBeenLastCalledWith(file, null, false)
    const text = document.body.textContent ?? ""
    expect(text).toContain("Jl. Melati No. 5 RT 004/RW 003")
    expect(text).toContain("Lama → TKA · Bu Mawar 26/27")
    expect(text).toContain("kosong → 081255556666")
    expect(text).toContain("harus L atau P")
    const save = [...document.querySelectorAll("button")].find((b) => b.textContent?.includes("Simpan 2 siswa"))!
    save.click()
    await flushPromises()
    expect(imporBiodata).toHaveBeenLastCalledWith(file, { "BU MAWAR": 2 }, true)
    expect(view.emitted("saved")?.[0]?.[0]).toMatchObject({ disimpan: true })
    view.unmount()
  })
  it("previews SPP from the master tab, keeps flagged and different rows unchanged, then fills only new SPP", async () => {
    const view = mount(SppImportDialog, { global, attachTo: document.body, props: { modelValue: true } })
    await flushPromises()
    const input = document.querySelector<HTMLInputElement>("#impor-spp-berkas")!
    const file = new File(["Nama,Juli"], "master.csv", { type: "text/csv" })
    Object.defineProperty(input, "files", { value: [file] })
    input.dispatchEvent(new Event("change"))
    await flushPromises()
    expect(imporSpp).toHaveBeenLastCalledWith(file, false)
    const text = document.body.textContent ?? ""
    expect(text).toContain("Rp 1.350.000 per bulan")
    expect(text).toContain("Sistem Rp 1.300.000 · berkas Rp 1.350.000")
    expect(text).toContain("Nominal di berkas: Rp 650.000, Rp 1.300.000")
    const save = [...document.querySelectorAll("button")].find((b) => b.textContent?.includes("Isi SPP 1 siswa"))!
    save.click()
    await flushPromises()
    expect(imporSpp).toHaveBeenLastCalledWith(file, true)
    expect(view.emitted("saved")?.[0]?.[0]).toMatchObject({ disimpan: true, diisi: 1 })
    view.unmount()
  })
})
