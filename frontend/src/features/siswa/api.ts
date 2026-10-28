import { api } from "@/core/api"
import type { BiayaMasukField, ImporBiodataHasil, ImporSppHasil, Paginated, Siswa, SiswaInput } from "@/types/api"

export const siswaApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Siswa>>("/siswa/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<Siswa[]> {
    const out: Siswa[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      // 200 per request: a whole group or the full roster loads in one round trip.
      const data = await siswaApi.list({ page_size: 200, ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  create: (payload: Partial<SiswaInput>) =>
    api.post<Siswa>("/siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<SiswaInput>) =>
    api.put<Siswa>(`/siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/siswa/${id}/`),
  /** Pratinjau (simpan=false) atau simpan biodata dari CSV rekap kelas. */
  imporBiodata(berkas: File, kelasMap: Record<string, number | null> | null, simpan: boolean) {
    const fd = new FormData()
    fd.append("berkas", berkas)
    fd.append("simpan", simpan ? "true" : "false")
    if (kelasMap) fd.append("kelas_map", JSON.stringify(kelasMap))
    return api.post<ImporBiodataHasil>("/siswa/impor-biodata/", fd).then((r) => r.data)
  },
  /** Pratinjau (simpan=false) atau isi SPP siswa yang masih Rp 0 dari tab master Recap Cash In. */
  imporSpp(berkas: File, simpan: boolean) {
    const fd = new FormData()
    fd.append("berkas", berkas)
    fd.append("simpan", simpan ? "true" : "false")
    return api.post<ImporSppHasil>("/siswa/impor-spp/", fd).then((r) => r.data)
  },
  /** Nominal daftar harga sesuai jenjang kelompok, untuk mengisi awal biaya masuk. */
  biayaMasukDefault: (kelompok: number) =>
    api.get<Record<BiayaMasukField, string | null>>("/siswa/biaya-masuk-default/", { params: { kelompok } }).then((r) => r.data),
}
