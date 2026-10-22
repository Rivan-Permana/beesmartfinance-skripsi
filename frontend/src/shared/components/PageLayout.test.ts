import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import PageLayout from "./PageLayout.vue"

describe("PageLayout surface compatibility", () => {
  it("keeps the surface for existing callers that omit the new prop", () => {
    const view = mount(PageLayout, { props: { title: "Siswa" }, slots: { default: "Isi" } })
    expect(view.find(".bee-page__card--plain").exists()).toBe(false)
    expect(view.find(".bee-page__card").text()).toBe("Isi")
  })
  it("allows dashboard to opt out without removing content", () => {
    const view = mount(PageLayout, { props: { title: "Ringkasan", surface: false }, slots: { default: "Angka" } })
    expect(view.find(".bee-page__card--plain").text()).toBe("Angka")
  })
})
