import { api } from "@/core/api"
import type { Coa, Jurnal, JurnalInput, Paginated } from "@/types/api"

export const jurnalApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Jurnal>>("/jurnal/", { params }).then((r) => r.data),
  create: (payload: JurnalInput) =>
    api.post<Jurnal>("/jurnal/", payload).then((r) => r.data),
  update: (id: string, payload: JurnalInput) =>
    api.put<Jurnal>(`/jurnal/${id}/`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/jurnal/${id}/`),
  submit: (id: string) =>
    api.post<Jurnal>(`/jurnal/${id}/submit/`).then((r) => r.data),
  approve: (id: string) =>
    api.post<Jurnal>(`/jurnal/${id}/approve/`).then((r) => r.data),
  catat: (id: string) =>
    api.post<Jurnal>(`/jurnal/${id}/catat/`).then((r) => r.data),
  batalPenerimaan: (id: string, alasan: string) =>
    api.post<Jurnal>(`/jurnal/${id}/batal-penerimaan/`, { alasan }).then((r) => r.data),
  void: (id: string) => api.post(`/jurnal/${id}/void/`).then((r) => r.data),
}

export const coaApi = {
  async list(): Promise<Coa[]> {
    const out: Coa[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const { data } = await api.get<Paginated<Coa>>("/coa/", {
        params: { page },
      })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
}
