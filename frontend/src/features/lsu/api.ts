import { api } from "@/core/api"
import type { Paginated, PaketLSU, PaketLSUInput } from "@/types/api"

export const lsuApi = {
  async listAll(): Promise<PaketLSU[]> {
    const rows: PaketLSU[] = []
    for (let page = 1; ; page++) {
      const { data } = await api.get<Paginated<PaketLSU>>("/paket-lsu/", { params: { page_size: 200, page } })
      rows.push(...data.results)
      if (!data.next) return rows
    }
  },
  create: (payload: PaketLSUInput) => api.post<PaketLSU>("/paket-lsu/", payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/paket-lsu/${id}/`),
  catatPertemuan: (id: number, payload: { tanggal: string; catatan: string }) =>
    api.post<PaketLSU>(`/paket-lsu/${id}/pertemuan/`, payload).then((r) => r.data),
  hapusPertemuan: (id: number, pertemuanId: number) =>
    api.delete<PaketLSU>(`/paket-lsu/${id}/pertemuan/${pertemuanId}/`).then((r) => r.data),
}
