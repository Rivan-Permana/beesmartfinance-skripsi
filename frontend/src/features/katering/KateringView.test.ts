import { flushPromises, mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import ConfirmationService from "primevue/confirmationservice"
import ToastService from "primevue/toastservice"
import { describe, expect, it, vi } from "vitest"

vi.mock('vue-router',()=>({onBeforeRouteLeave:vi.fn(),RouterLink:{props:['to'],template:'<a :href="to"><slot /></a>'}}))
vi.mock("@/core/api", () => ({
  api: {
    get: vi.fn(async () => ({ data: { results: [], next: null, tarif_harian: "22000", tarif_jumat: "10000", is_default: true } })),
    post: vi.fn(async (_path: string, _payload: FormData) => ({ data: { id: 1, tanggal: "2026-10-15", keterangan: "", gambar_url: "/media/katering/menu.jpg" } })),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from "@/core/api"
import KateringView from "./KateringView.vue"

describe("menu katering", () => {
  it("can save a photo without a description and keeps invalid empty input visible", async () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:menu-preview")
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {})
    const wrapper = mount(KateringView, {
      global: { plugins: [PrimeVue, ToastService, ConfirmationService] },
      attachTo: document.body,
    })
    try {
      await flushPromises()
      await wrapper.findAll("button").find((button) => button.text() === "Menu bulanan")!.trigger("click")
      await flushPromises()
      await wrapper.findAll("button").find((button) => button.text() === "Isi menu")!.trigger("click")
      await flushPromises()
      const buttons = () => Array.from(document.querySelectorAll("button"))
      const save = () => buttons().find((button) => button.textContent?.trim() === "Simpan menu" && button.closest('[role="dialog"]'))!
      expect(save().disabled).toBe(false)
      save().click()
      await flushPromises()
      expect(document.body.textContent).toContain("Isi keterangan atau pilih foto")
      expect(api.post).not.toHaveBeenCalled()
      const input = document.querySelector<HTMLInputElement>("#menu-foto")!
      const file = new File(["image bytes"], "Foto.JPG", { type: "image/jpeg" })
      Object.defineProperty(input, "files", { value: [file] })
      input.dispatchEvent(new Event("change", { bubbles: true }))
      await flushPromises()
      save().click()
      await flushPromises()
      expect(api.post).toHaveBeenCalledOnce()
      const payload = vi.mocked(api.post).mock.calls[0]![1]
      expect(payload.get("keterangan")).toBe("")
      expect(payload.get("gambar")).toMatchObject({ name: "Foto.JPG", type: "image/jpeg", size: file.size })
    } finally {
      wrapper.unmount()
      document.body.innerHTML = ""
    }
  })
})
