import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/core/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  tokenStore: {
    access: null,
    refresh: null,
    set: vi.fn(),
    clear: vi.fn(),
  },
}))

import { api } from "@/core/api"
import { tagihanApi } from "./api"

describe("tagihanApi.generate", () => {
  beforeEach(() => {
    vi.mocked(api.post).mockReset()
  })

  it("posts generate payload and returns tagihan", async () => {
    const mockTagihan = {
      id: 42,
      siswa: 1,
      periode_bulan: 2,
      periode_tahun: 2026,
      total: "1350000.00",
      status: "BELUM",
      jurnal: null,
      detail: [],
    }
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockTagihan })

    const result = await tagihanApi.generate({
      siswa: 1,
      periode_bulan: 2,
      periode_tahun: 2026,
      tarif_katering: 22000,
    })

    expect(api.post).toHaveBeenCalledWith("/tagihan/generate/", {
      siswa: 1,
      periode_bulan: 2,
      periode_tahun: 2026,
      tarif_katering: 22000,
    })
    expect(result.id).toBe(42)
    expect(result.total).toBe("1350000.00")
  })
})

describe("tagihanApi.preview", () => {
  it("posts preview without persisting", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { total: "500000.00", detail: [{ komponen: "SPP", nominal: "500000" }] },
    })

    const preview = await tagihanApi.preview({
      siswa: 3,
      periode_bulan: 3,
      periode_tahun: 2026,
    })

    expect(api.post).toHaveBeenCalledWith("/tagihan/preview/", {
      siswa: 3,
      periode_bulan: 3,
      periode_tahun: 2026,
    })
    expect(preview.total).toBe("500000.00")
  })
})
