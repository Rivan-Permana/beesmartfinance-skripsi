import { flushPromises, mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import ConfirmationService from "primevue/confirmationservice"
import ToastService from "primevue/toastservice"
import { describe, expect, it, vi } from "vitest"

vi.mock("vue-router", () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock("@/core/api", () => ({
  api: {
    get: vi.fn(async (path: string) => ({ data: { results: path === "/pendaftaran-siswa/" ? [{
      id: 1, nama_calon: "Calon Uji", jenjang: null, tanggal_daftar: "2026-10-01", status: "TRIAL",
      biaya_sitin: "750000.00", biaya_formulir: "100000.00", biaya_pendaftaran: "0.00", total_biaya: "850000.00",
      total_terbayar: "750000.00", sisa_biaya: "100000.00", perlu_rekonsiliasi: false,
      sitin_terbayar: true, formulir_terbayar: false, jurnal_sitin: "sitin-journal", jurnal_pendaftaran: null,
      pembayaran: [], siswa: null,
    }] : path === "/coa/" ? [{ kode_akun: "111", nama_akun: "Kas", is_active: true }] : [], next: null } })),
    post: vi.fn(async (_path: string, _payload: unknown) => ({ data: {} })),
  },
}))

import { api } from "@/core/api"
import PendaftaranListView from "./PendaftaranListView.vue"

function render() {
  return mount(PendaftaranListView, {
    global: { plugins: [PrimeVue, ToastService, ConfirmationService] }, attachTo: document.body,
  })
}
function clickButton(label: string) {
  const button = Array.from(document.querySelectorAll("button")).find((b) => b.textContent?.trim() === label)!
  button.click()
}

describe("pendaftaran tanpa tarif bawaan", () => {
  it("starts with explicit empty component fees and does not assume a payment on finalization", async () => {
    const wrapper = render()
    try {
      await flushPromises()
      clickButton("Daftar Calon Baru")
      await flushPromises()
      expect(document.querySelector<HTMLInputElement>("#sitin")!.value).toBe("")
      expect(document.querySelector<HTMLInputElement>("#formulir")!.value).toBe("")
      expect(document.body.textContent).toContain("Total biaya pendaftaran: Isi kedua komponen")
      clickButton("Simpan")
      await flushPromises()
      expect(api.post).not.toHaveBeenCalled()
      expect(document.body.textContent).toContain("Isi nama, tanggal daftar, dan kedua komponen")
      clickButton("Batal")
      await flushPromises()
      clickButton("Finalisasi")
      await flushPromises()
      expect(document.querySelector<HTMLInputElement>("#spp")!.value).toBe("")
      expect(document.body.textContent).toContain("Finalisasi tidak mencatat penerimaan uang")
    } finally {
      wrapper.unmount()
      document.body.innerHTML = ""
    }
  })

  it("offers only the unpaid component after sit-in has already been received", async () => {
    const wrapper = render()
    try {
      await flushPromises()
      clickButton("Catat Penerimaan")
      await flushPromises()
      expect(document.querySelector<HTMLInputElement>("#bayar-SITIN")!.disabled).toBe(true)
      expect(document.querySelector<HTMLInputElement>("#bayar-FORMULIR")!.checked).toBe(true)
      expect(document.body.textContent).toContain("Jumlah diterima: Rp 100.000")
      expect(api.post).not.toHaveBeenCalled()
    } finally {
      wrapper.unmount()
      document.body.innerHTML = ""
    }
  })
})
