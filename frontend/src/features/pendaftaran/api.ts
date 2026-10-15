import { api } from "@/core/api"
import type { BayarPendaftaranInput, Paginated, PendaftaranSiswa, PendaftaranSiswaInput } from "@/types/api"

export const pendaftaranSiswaApi = {
  list: (params?: { status?: string; page?: number }) =>
    api
      .get<Paginated<PendaftaranSiswa>>("/pendaftaran-siswa/", { params })
      .then((r) => r.data),
  async listAll(): Promise<PendaftaranSiswa[]> {
    const results: PendaftaranSiswa[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await pendaftaranSiswaApi.list({ page })
      results.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return results
  },
  create: (payload: PendaftaranSiswaInput) =>
    api.post<PendaftaranSiswa>("/pendaftaran-siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<PendaftaranSiswaInput>) =>
    api.patch<PendaftaranSiswa>(`/pendaftaran-siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/pendaftaran-siswa/${id}/`),
  bayar: (id: number, payload: BayarPendaftaranInput) =>
    api
      .post<{ detail: string; jurnal_id: string; pendaftaran: PendaftaranSiswa }>(`/pendaftaran-siswa/${id}/bayar/`, payload)
      .then((r) => r.data),
  finalisasi: (id: number, spp_nominal: string) =>
    api
      .post<PendaftaranSiswa>(`/pendaftaran-siswa/${id}/finalisasi/`, { spp_nominal })
      .then((r) => r.data),
}
