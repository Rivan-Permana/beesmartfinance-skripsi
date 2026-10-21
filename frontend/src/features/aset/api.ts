import { api } from "@/core/api"
import type { FixedAsset, Paginated } from "@/types/api"

export const asetApi = {
  list: () =>
    api.get<Paginated<FixedAsset>>("/aset/").then((r) => r.data),
  async listAll(): Promise<FixedAsset[]> {
    const rows: FixedAsset[] = []
    let page = 1
    let next = true
    while (next) {
      const { data } = await api.get<Paginated<FixedAsset>>("/aset/", { params: { page } })
      rows.push(...data.results)
      next = !!data.next
      page += 1
    }
    return rows
  },
  get: (id: number) => api.get<FixedAsset>(`/aset/${id}/`).then((r) => r.data),
  create: (payload: Partial<FixedAsset>) =>
    api.post<FixedAsset>("/aset/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<FixedAsset>) =>
    api.put<FixedAsset>(`/aset/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/aset/${id}/`),
  susutkan: (id: number) =>
    api
      .post<{ detail: string; jurnal_id: string }>(`/aset/${id}/susutkan/`)
      .then((r) => r.data),
}
