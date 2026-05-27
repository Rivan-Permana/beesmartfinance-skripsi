import { api } from "@/core/api"
import type { Paginated, StrukTagihan, Tagihan } from "@/types/api"

export interface GenerateInput {
  siswa: number
  periode_bulan: number
  periode_tahun: number
  tarif_katering?: number
}

export const tagihanApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Tagihan>>("/tagihan/", { params }).then((r) => r.data),
  generate: (payload: GenerateInput) =>
    api.post<Tagihan>("/tagihan/generate/", payload).then((r) => r.data),
  bayar: (id: number) =>
    api.post(`/tagihan/${id}/bayar/`).then((r) => r.data),
  struk: (id: number) =>
    api.get<StrukTagihan>(`/tagihan/${id}/struk/`).then((r) => r.data),
}
