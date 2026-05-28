import { api } from "@/core/api"
import type { Anggaran, Paginated, PeriodeAkuntansi } from "@/types/api"

export const anggaranApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Anggaran>>("/anggaran/", { params }).then((r) => r.data),
  create: (payload: Partial<Anggaran>) =>
    api.post<Anggaran>("/anggaran/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Anggaran>) =>
    api.put<Anggaran>(`/anggaran/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/anggaran/${id}/`),
}

export const periodeApi = {
  list: () =>
    api.get<Paginated<PeriodeAkuntansi>>("/periode/").then((r) => r.data),
  create: (payload: Partial<PeriodeAkuntansi>) =>
    api.post<PeriodeAkuntansi>("/periode/", payload).then((r) => r.data),
  tutup: (id: number) =>
    api
      .post<{ detail: string; periode: PeriodeAkuntansi; jurnal_penutup: string }>(
        `/periode/${id}/tutup/`,
      )
      .then((r) => r.data),
}
