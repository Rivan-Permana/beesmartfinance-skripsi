import { flushPromises, mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import ConfirmationService from "primevue/confirmationservice"
import ToastService from "primevue/toastservice"
import { describe, expect, it, vi } from "vitest"

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({ hasRole: (roles: string[]) => roles.includes("Finance") }),
}))
vi.mock("@/core/api", () => ({
  api: {
    get: vi.fn(async (path: string) => ({ data: {
      results: path === "/coa/" ? [{ kode_akun: "111", nama_akun: "Kas", sub_golongan: null,
        posisi_normal: "D", is_active: true, saldo_awal: "1000.25", tanggal_saldo_awal: "2026-01-01" }] : [],
      next: null,
    } })),
    patch: vi.fn(async (_path: string, _payload: unknown) => ({ data: {} })),
  },
}))

import { api } from "@/core/api"
import CoaListView from "./CoaListView.vue"

describe("saldo awal pada daftar akun", () => {
  it("places the balance after active, loads it for editing, and requires an explicit date", async () => {
    const wrapper = mount(CoaListView, {
      global: { plugins: [PrimeVue, ToastService, ConfirmationService] },
      attachTo: document.body,
    })
    try {
      await flushPromises()
      const headers = wrapper.findAll("th").map((header) => header.text())
      expect(headers.indexOf("Saldo Awal")).toBe(headers.indexOf("Aktif") + 1)
      await wrapper.find('[aria-label="Edit akun"]').trigger("click")
      await flushPromises()
      const date = document.querySelector<HTMLInputElement>("#akun-tanggal-saldo-awal")!
      expect(document.querySelector<HTMLInputElement>("#akun-saldo-awal")!.value).toContain("1.000,25")
      date.value = ""
      date.dispatchEvent(new Event("input", { bubbles: true }))
      const save = () => Array.from(document.querySelectorAll("button")).find((button) => button.textContent?.trim() === "Simpan")!
      save().click()
      await flushPromises()
      expect(api.patch).not.toHaveBeenCalled()
      expect(document.body.textContent).toContain("Isi tanggal acuan")
      date.value = "2026-01-01"
      date.dispatchEvent(new Event("input", { bubbles: true }))
      await flushPromises()
      save().click()
      await flushPromises()
      expect(api.patch).toHaveBeenCalledWith("/coa/111/", expect.objectContaining({ saldo_awal: "1000.25", tanggal_saldo_awal: "2026-01-01" }))
    } finally {
      wrapper.unmount()
      document.body.innerHTML = ""
    }
  })
})
