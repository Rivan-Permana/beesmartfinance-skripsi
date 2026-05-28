import { api } from "@/core/api"
import type { Kegiatan, LaporanKegiatan, Paginated } from "@/types/api"

export const kegiatanApi = {
  list: () =>
    api.get<Paginated<Kegiatan>>("/kegiatan/").then((r) => r.data),
  create: (payload: Partial<Kegiatan>) =>
    api.post<Kegiatan>("/kegiatan/", payload).then((r) => r.data),
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
