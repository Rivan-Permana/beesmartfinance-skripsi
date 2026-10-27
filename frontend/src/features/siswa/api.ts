import { api } from "@/core/api"
import type { Paginated, Siswa, SiswaInput } from "@/types/api"

export const siswaApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Siswa>>("/siswa/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<Siswa[]> {
    const out: Siswa[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      // 200 per request: a whole group or the full roster loads in one round trip.
      const data = await siswaApi.list({ page_size: 200, ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  create: (payload: Partial<SiswaInput>) =>
    api.post<Siswa>("/siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<SiswaInput>) =>
    api.put<Siswa>(`/siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/siswa/${id}/`),
}
