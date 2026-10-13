import { api } from "@/core/api"
import type { Paginated, PendaftaranSiswa, PendaftaranSiswaInput } from "@/types/api"

export const pendaftaranSiswaApi = {
  list: (params?: { status?: string }) =>
    api
      .get<Paginated<PendaftaranSiswa>>("/pendaftaran-siswa/", { params })
      .then((r) => r.data),
  create: (payload: PendaftaranSiswaInput) =>
    api.post<PendaftaranSiswa>("/pendaftaran-siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<PendaftaranSiswaInput>) =>
    api.patch<PendaftaranSiswa>(`/pendaftaran-siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/pendaftaran-siswa/${id}/`),
  bayarSitin: (id: number) =>
    api
      .post<{ detail: string; jurnal_id: string }>(`/pendaftaran-siswa/${id}/bayar-sitin/`)
      .then((r) => r.data),
  finalisasi: (id: number, spp_nominal: string) =>
    api
      .post<PendaftaranSiswa>(`/pendaftaran-siswa/${id}/finalisasi/`, { spp_nominal })
      .then((r) => r.data),
}
