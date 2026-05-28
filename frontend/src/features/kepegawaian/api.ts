import { api } from "@/core/api"
import type {
  Gaji,
  Paginated,
  Pegawai,
  PegawaiInput,
  Pinjaman,
} from "@/types/api"

export const pegawaiApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Pegawai>>("/pegawai/", { params }).then((r) => r.data),
  create: (payload: Partial<PegawaiInput>) =>
    api.post<Pegawai>("/pegawai/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<PegawaiInput>) =>
    api.put<Pegawai>(`/pegawai/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/pegawai/${id}/`),
}

export const gajiApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Gaji>>("/gaji/", { params }).then((r) => r.data),
  create: (payload: Partial<Gaji>) =>
    api.post<Gaji>("/gaji/", payload).then((r) => r.data),
  posting: (id: number) =>
    api.post<{ detail: string; jurnal_id: string }>(`/gaji/${id}/posting/`).then((r) => r.data),
}

export const pinjamanApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Pinjaman>>("/pinjaman/", { params }).then((r) => r.data),
  create: (payload: Partial<Pinjaman>) =>
    api.post<Pinjaman>("/pinjaman/", payload).then((r) => r.data),
  cairkan: (id: number) =>
    api.post<{ detail: string; jurnal_id: string }>(`/pinjaman/${id}/cairkan/`).then((r) => r.data),
}
