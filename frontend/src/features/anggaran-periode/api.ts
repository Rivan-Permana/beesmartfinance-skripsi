import { api } from "@/core/api"
import type { Anggaran, Paginated, PeriodeAkuntansi } from "@/types/api"

async function allPages<T>(path: string): Promise<T[]> {
  const rows: T[] = []
  let page = 1
  let next = true
  while (next) {
    const { data } = await api.get<Paginated<T>>(path, { params: { page } })
    rows.push(...data.results)
    next = !!data.next
    page++
  }
  return rows
}

export const anggaranApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Anggaran>>("/anggaran/", { params }).then((r) => r.data),
  listAll: () => allPages<Anggaran>("/anggaran/"),
  create: (payload: Partial<Anggaran>) =>
    api.post<Anggaran>("/anggaran/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Anggaran>) =>
    api.put<Anggaran>(`/anggaran/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/anggaran/${id}/`),
}

export const periodeApi = {
  list: () =>
    api.get<Paginated<PeriodeAkuntansi>>("/periode/").then((r) => r.data),
  listAll: () => allPages<PeriodeAkuntansi>("/periode/"),
  create: (payload: Partial<PeriodeAkuntansi>) =>
    api.post<PeriodeAkuntansi>("/periode/", payload).then((r) => r.data),
  tutup: (id: number) =>
    api
      .post<{ detail: string; periode: PeriodeAkuntansi; jurnal_penutup: string }>(
        `/periode/${id}/tutup/`,
      )
      .then((r) => r.data),
}
