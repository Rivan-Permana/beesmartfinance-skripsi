import axios from "axios"
import { afterEach, describe, expect, it, vi } from "vitest"

import { api, tokenStore } from "./api"

const originalAdapter = api.defaults.adapter

afterEach(() => {
  api.defaults.adapter = originalAdapter
  tokenStore.clear()
  vi.restoreAllMocks()
})

describe("API authentication", () => {
  it("invalidates requests when another tab changes the session", () => {
    const version = tokenStore.version
    window.dispatchEvent(new StorageEvent("storage", { key: "bee_access" }))
    expect(tokenStore.version).toBe(version + 1)
  })

  it("refreshes an expired access token when loading the user profile", async () => {
    tokenStore.set({ access: "expired", refresh: "valid-refresh" })
    const refresh = vi.spyOn(axios, "post").mockResolvedValue({ data: { access: "renewed" } })
    const adapter = vi.fn(async (config) => {
      if (adapter.mock.calls.length === 1) throw { config, response: { status: 401 } }
      return { config, data: { username: "keuangan" }, status: 200, statusText: "OK", headers: {} }
    })
    api.defaults.adapter = adapter

    const response = await api.get("/auth/me/")

    expect(response.data.username).toBe("keuangan")
    expect(refresh).toHaveBeenCalledWith(expect.stringContaining("/auth/token/refresh/"), { refresh: "valid-refresh" })
    expect(adapter.mock.calls[1]?.[0]?.headers?.Authorization).toBe("Bearer renewed")
    expect(tokenStore.access).toBe("renewed")
  })

  it("does not refresh a rejected login", async () => {
    tokenStore.set({ access: "expired", refresh: "valid-refresh" })
    const refresh = vi.spyOn(axios, "post")
    api.defaults.adapter = async (config) => { throw { config, response: { status: 401 } } }

    await expect(api.post("/auth/token/", {})).rejects.toBeDefined()
    expect(refresh).not.toHaveBeenCalled()
  })

  it("does not use a new role's refresh token for an old role's 401", async () => {
    tokenStore.set({ access: "old-access", refresh: "old-refresh" })
    const refresh = vi.spyOn(axios, "post").mockResolvedValue({ data: { access: "renewed" } })
    let rejectRequest!: (reason: unknown) => void
    let calls = 0
    api.defaults.adapter = (config) => {
      if (++calls > 1) return Promise.resolve({ config, data: {}, status: 200, statusText: "OK", headers: {} })
      return new Promise((_resolve, reject) => {
        rejectRequest = (reason) => reject({ ...reason, config })
      })
    }

    const pending = api.get("/jurnal/")
    await vi.waitFor(() => expect(rejectRequest).toBeTypeOf("function"))
    tokenStore.clear()
    tokenStore.set({ access: "new-access", refresh: "new-refresh" })
    rejectRequest({ response: { status: 401 } })

    await expect(pending).rejects.toBeDefined()
    expect(refresh).not.toHaveBeenCalled()
    expect(tokenStore.access).toBe("new-access")
  })

  it("does not overwrite a new role when an earlier refresh finishes late", async () => {
    tokenStore.set({ access: "old-access", refresh: "old-refresh" })
    let finishRefresh!: (value: { data: { access: string } }) => void
    const refresh = vi.spyOn(axios, "post").mockReturnValue(new Promise((resolve) => {
      finishRefresh = resolve
    }))
    api.defaults.adapter = async (config) => { throw { config, response: { status: 401 } } }

    const pending = api.get("/jurnal/")
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce())
    tokenStore.clear()
    tokenStore.set({ access: "new-access", refresh: "new-refresh" })
    finishRefresh({ data: { access: "old-renewed" } })

    await expect(pending).rejects.toBeDefined()
    expect(tokenStore.access).toBe("new-access")
  })

  it("retries a second expired request from the same session after refresh completes", async () => {
    tokenStore.set({ access: "expired", refresh: "same-session" })
    const refresh = vi.spyOn(axios, "post").mockResolvedValue({ data: { access: "renewed" } })
    const rejectOld: Array<() => void> = []
    api.defaults.adapter = (config) => {
      if (config.headers.Authorization === "Bearer renewed") {
        return Promise.resolve({ config, data: {}, status: 200, statusText: "OK", headers: {} })
      }
      return new Promise((_resolve, reject) => {
        rejectOld.push(() => reject({ config, response: { status: 401 } }))
      })
    }

    const first = api.get("/dashboard/ringkasan/")
    const second = api.get("/jurnal/")
    await vi.waitFor(() => expect(rejectOld).toHaveLength(2))
    rejectOld[0]!()
    await expect(first).resolves.toBeDefined()
    rejectOld[1]!()
    await expect(second).resolves.toBeDefined()
    expect(refresh).toHaveBeenCalledOnce()
  })
})
