import { api } from "@/core/api"
import type { Coa, Golongan, KodePengeluaran, KodePengeluaranInput, Paginated, SubGolongan } from "@/types/api"

async function fetchAll<T>(path: string): Promise<T[]> {
  const out: T[] = []
  let page = 1
  let hasNext = true
  while (hasNext) {
    const { data } = await api.get<Paginated<T>>(path, { params: { page_size: 200, page } })
    out.push(...data.results)
    hasNext = !!data.next
    page += 1
  }
  return out
}

export type CoaInput = Omit<Coa, "is_active" | "saldo_awal" | "tanggal_saldo_awal"> & {
  is_active?: boolean
  saldo_awal?: string
  tanggal_saldo_awal?: string | null
}

export const coaManageApi = {
  listGolongan: () => fetchAll<Golongan>("/golongan/"),
  createGolongan: (payload: Omit<Golongan, "id">) =>
    api.post<Golongan>("/golongan/", payload).then((r) => r.data),
  updateGolongan: (id: number, payload: Partial<Golongan>) =>
    api.patch<Golongan>(`/golongan/${id}/`, payload).then((r) => r.data),
  removeGolongan: (id: number) => api.delete(`/golongan/${id}/`),

  listSubGolongan: () => fetchAll<SubGolongan>("/sub-golongan/"),
  createSubGolongan: (payload: Omit<SubGolongan, "id">) =>
    api.post<SubGolongan>("/sub-golongan/", payload).then((r) => r.data),
  updateSubGolongan: (id: number, payload: Partial<SubGolongan>) =>
    api.patch<SubGolongan>(`/sub-golongan/${id}/`, payload).then((r) => r.data),
  removeSubGolongan: (id: number) => api.delete(`/sub-golongan/${id}/`),

  listCoa: () => fetchAll<Coa>("/coa/"),
  createCoa: (payload: CoaInput) =>
    api.post<Coa>("/coa/", payload).then((r) => r.data),
  updateCoa: (kode: string, payload: Partial<CoaInput>) =>
    api.patch<Coa>(`/coa/${kode}/`, payload).then((r) => r.data),
  removeCoa: (kode: string) => api.delete(`/coa/${kode}/`),
}

/** Kode buku kas sekolah (ATK, PLN, AB3 TK, ...) -> akun beban. Ditulis Keuangan, dibaca semua peran. */
export const kodePengeluaranApi = {
  list: () => api.get<KodePengeluaran[]>("/kode-pengeluaran/").then((r) => r.data),
  create: (payload: KodePengeluaranInput) =>
    api.post<KodePengeluaran>("/kode-pengeluaran/", payload).then((r) => r.data),
  update: (id: number, payload: KodePengeluaranInput) =>
    api.put<KodePengeluaran>(`/kode-pengeluaran/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/kode-pengeluaran/${id}/`),
}
