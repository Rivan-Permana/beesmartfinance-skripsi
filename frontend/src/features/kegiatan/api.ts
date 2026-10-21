import { api } from "@/core/api"
import type { Kegiatan, LaporanKegiatan, Paginated } from "@/types/api"

export const kegiatanApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Kegiatan>>("/kegiatan/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<Kegiatan[]> {
    const rows: Kegiatan[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await kegiatanApi.list({ ...params, page })
      rows.push(...data.results)
      hasNext = Boolean(data.next)
      page += 1
    }
    return rows
  },
  create: (payload: Partial<Kegiatan>) =>
    api.post<Kegiatan>("/kegiatan/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Kegiatan>) =>
    api.put<Kegiatan>(`/kegiatan/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/kegiatan/${id}/`),
  realisasi: (id: number, body: { tanggal: string; deskripsi: string; nominal: number }) =>
    api
      .post<{ detail: string; realisasi_id: number; jurnal_id: string }>(
        `/kegiatan/${id}/realisasi/`,
        body,
      )
      .then((r) => r.data),
  laporan: (id: number) =>
    api.get<LaporanKegiatan>(`/kegiatan/${id}/laporan/`).then((r) => r.data),
}
