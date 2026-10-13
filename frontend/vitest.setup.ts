import { config } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { beforeEach, vi } from "vitest"

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  sessionStorage.clear()
  vi.restoreAllMocks()
})

config.global.stubs = {
  teleport: true,
}
