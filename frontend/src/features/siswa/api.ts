import { api } from "@/core/api"
import type { Paginated, Siswa, SiswaInput } from "@/types/api"

export const siswaApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Siswa>>("/siswa/", { params }).then((r) => r.data),
  create: (payload: Partial<SiswaInput>) =>
    api.post<Siswa>("/siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<SiswaInput>) =>
    api.put<Siswa>(`/siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/siswa/${id}/`),
}
