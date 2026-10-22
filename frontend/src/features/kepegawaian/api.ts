import { api } from "@/core/api"
import type {
  AbsenPegawai,
  AbsenPegawaiRekap,
  Gaji,
  Paginated,
  Pegawai,
  PegawaiInput,
  Pinjaman,
} from "@/types/api"

export const pegawaiApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Pegawai>>("/pegawai/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<Pegawai[]> {
    const out: Pegawai[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await pegawaiApi.list({ page_size: 200, ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  get: (id: number) => api.get<Pegawai>(`/pegawai/${id}/`).then((r) => r.data),
  create: (payload: Partial<PegawaiInput>) =>
    api.post<Pegawai>("/pegawai/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<PegawaiInput>) =>
    api.put<Pegawai>(`/pegawai/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/pegawai/${id}/`),
}

export const absenPegawaiApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<AbsenPegawai>>("/absen-pegawai/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<AbsenPegawai[]> {
    const rows: AbsenPegawai[] = []
    let page = 1, next = true
    while (next) { const data = await absenPegawaiApi.list({ page_size: 200, ...params, page }); rows.push(...data.results); next = !!data.next; page++ }
    return rows
  },
  bulkSave: (tanggal: string, items: Omit<AbsenPegawai, "id" | "tanggal">[]) =>
    api.post("/absen-pegawai/bulk-save/", { tanggal, items }).then((r) => r.data),
  rekapBulanan: (bulan: number, tahun: number) =>
    api
      .get<AbsenPegawaiRekap[]>("/absen-pegawai/rekap-bulanan/", { params: { bulan, tahun } })
      .then((r) => r.data),
}

export const gajiApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Gaji>>("/gaji/", { params }).then((r) => r.data),
  async listAll(): Promise<Gaji[]> {
    const rows: Gaji[] = []
    let page = 1, next = true
    while (next) { const data = await gajiApi.list({ page_size: 200, page }); rows.push(...data.results); next = !!data.next; page++ }
    return rows
  },
  get: (id: number) => api.get<Gaji>(`/gaji/${id}/`).then((r) => r.data),
  create: (payload: Partial<Gaji>) =>
    api.post<Gaji>("/gaji/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Gaji>) =>
    api.put<Gaji>(`/gaji/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/gaji/${id}/`),
  posting: (id: number) =>
    api.post<{ detail: string; jurnal_id: string }>(`/gaji/${id}/posting/`).then((r) => r.data),
}

export const pinjamanApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Pinjaman>>("/pinjaman/", { params }).then((r) => r.data),
  get: (id: number) => api.get<Pinjaman>(`/pinjaman/${id}/`).then((r) => r.data),
  async listAll(): Promise<Pinjaman[]> {
    const rows: Pinjaman[] = []
    let page = 1, next = true
    while (next) { const data = await pinjamanApi.list({ page_size: 200, page }); rows.push(...data.results); next = !!data.next; page++ }
    return rows
  },
  create: (payload: Partial<Pinjaman>) =>
    api.post<Pinjaman>("/pinjaman/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Pinjaman>) =>
    api.put<Pinjaman>(`/pinjaman/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/pinjaman/${id}/`),
  cairkan: (id: number) =>
    api.post<{ detail: string; jurnal_id: string }>(`/pinjaman/${id}/cairkan/`).then((r) => r.data),
}
