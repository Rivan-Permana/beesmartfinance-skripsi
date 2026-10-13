import { beforeEach, describe, expect, it, vi } from "vitest"

import { useAuthStore } from "@/stores/auth"

vi.mock("@/core/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
  tokenStore: {
    set: vi.fn(),
    clear: vi.fn(),
    get access() {
      return localStorage.getItem("bee_access")
    },
    get refresh() {
      return localStorage.getItem("bee_refresh")
    },
  },
}))

import { api, tokenStore } from "@/core/api"

describe("auth store", () => {
  beforeEach(() => {
    vi.mocked(api.post).mockReset()
    vi.mocked(api.get).mockReset()
    vi.mocked(tokenStore.set).mockReset()
    vi.mocked(tokenStore.clear).mockReset()
  })

  it("login stores tokens and loads user profile", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { access: "acc", refresh: "ref" },
    })
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        id: 1,
        username: "admin.tu",
        nama: "Bu Fitri",
        is_superuser: false,
        groups: ["Administration"],
      },
    })

    const auth = useAuthStore()
    await auth.login("admin.tu", "LebahMadu2026!")

    expect(tokenStore.set).toHaveBeenCalledWith({
      access: "acc",
      refresh: "ref",
    })
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.roles).toEqual(["Administration"])
  })

  it("hasRole allows superuser bypass", () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: "root",
      nama: "Root",
      is_superuser: true,
      groups: [],
    }
    expect(auth.hasRole(["Finance"])).toBe(true)
  })

  it("logout clears session", () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: "keuangan",
      nama: "Staff",
      is_superuser: false,
      groups: ["Finance"],
    }
    auth.logout()
    expect(tokenStore.clear).toHaveBeenCalled()
    expect(auth.user).toBeNull()
  })
})
