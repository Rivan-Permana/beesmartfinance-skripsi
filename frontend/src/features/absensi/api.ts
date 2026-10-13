import { api } from "@/core/api"
import type {
  Jenjang,
  KehadiranSiswa,
  KehadiranSiswaInput,
  Kelompok,
  Paginated,
} from "@/types/api"

export const jenjangApi = {
  list: () => api.get<Paginated<Jenjang>>("/jenjang/").then((r) => r.data.results),
  create: (payload: Omit<Jenjang, "id">) =>
    api.post<Jenjang>("/jenjang/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Omit<Jenjang, "id">>) =>
    api.patch<Jenjang>(`/jenjang/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/jenjang/${id}/`),
}

export const kelompokApi = {
  list: (params?: { jenjang?: number }) =>
    api
      .get<Paginated<Kelompok>>("/kelompok/", { params })
      .then((r) => r.data.results),
  create: (payload: Omit<Kelompok, "id" | "jenjang_kode" | "jenjang_nama" | "siswa_aktif">) =>
    api.post<Kelompok>("/kelompok/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<Omit<Kelompok, "id" | "jenjang_kode" | "jenjang_nama" | "siswa_aktif">>) =>
    api.patch<Kelompok>(`/kelompok/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/kelompok/${id}/`),
  pindahSiswa: (kelompokId: number, siswaIds: number[]) =>
    api
      .post<{ detail: string; updated: number }>(`/kelompok/${kelompokId}/pindah-siswa/`, {
        siswa_ids: siswaIds,
      })
      .then((r) => r.data),
}

export const kehadiranApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<KehadiranSiswa>>("/kehadiran-siswa/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<KehadiranSiswa[]> {
    const out: KehadiranSiswa[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await kehadiranApi.list({ ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  create: (payload: KehadiranSiswaInput) =>
    api.post<KehadiranSiswa>("/kehadiran-siswa/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<KehadiranSiswaInput>) =>
    api.patch<KehadiranSiswa>(`/kehadiran-siswa/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/kehadiran-siswa/${id}/`),
}

export interface RekapAbsensiRow {
  siswaId: number
  nis: string | null
  nama: string
  kelompok: string
  hadir: number
  izin: number
  sakit: number
  tidak_hadir: number
  katering: number
  jemput_datang: number
  jemput_pulang: number
}

export function monthDateRange(bulan: number, tahun: number) {
  const pad = (n: number) => String(n).padStart(2, "0")
  const lastDay = new Date(tahun, bulan, 0).getDate()
  return {
    tanggal__gte: `${tahun}-${pad(bulan)}-01`,
    tanggal__lte: `${tahun}-${pad(bulan)}-${pad(lastDay)}`,
  }
}

/** Untuk bulan kalender yang sedang berjalan, batasi rekap sampai hari ini. */
export function rekapAsOfDate(bulan: number, tahun: number, ref = new Date()): string | undefined {
  const cm = ref.getMonth() + 1
  const cy = ref.getFullYear()
  if (bulan !== cm || tahun !== cy) return undefined
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${cy}-${pad(cm)}-${pad(ref.getDate())}`
}

export function buildRekapRows(
  students: { id: number; nis: string | null; nama: string; kelompok: number | null }[],
  kelompokNama: Map<number, string>,
  records: KehadiranSiswa[],
  opts?: { asOfDate?: string; onlyWithData?: boolean },
): RekapAbsensiRow[] {
  const filtered = opts?.asOfDate
    ? records.filter((r) => r.tanggal <= opts.asOfDate!)
    : records

  const agg = new Map<number, RekapAbsensiRow>()
  for (const s of students) {
    agg.set(s.id, {
      siswaId: s.id,
      nis: s.nis,
      nama: s.nama,
      kelompok: s.kelompok ? kelompokNama.get(s.kelompok) ?? "-" : "-",
      hadir: 0,
      izin: 0,
      sakit: 0,
      tidak_hadir: 0,
      katering: 0,
      jemput_datang: 0,
      jemput_pulang: 0,
    })
  }
  for (const r of filtered) {
    const row = agg.get(r.siswa)
    if (!row) continue
    if (r.status === "hadir") row.hadir += 1
    else if (r.status === "izin") row.izin += 1
    else if (r.status === "sakit") row.sakit += 1
    else if (r.status === "tidak_hadir") row.tidak_hadir += 1
    if (r.ikut_katering) row.katering += 1
    if (r.jemput_datang) row.jemput_datang += 1
    if (r.jemput_pulang) row.jemput_pulang += 1
  }

  const hasAny = (r: RekapAbsensiRow) =>
    r.hadir + r.izin + r.sakit + r.tidak_hadir + r.katering + r.jemput_datang + r.jemput_pulang > 0

  let rows = [...agg.values()].sort((a, b) => a.nama.localeCompare(b.nama))
  if (opts?.onlyWithData) rows = rows.filter(hasAny)
  return rows
}

export function countDistinctDays(records: KehadiranSiswa[], asOfDate?: string): number {
  const dates = new Set<string>()
  for (const r of records) {
    if (asOfDate && r.tanggal > asOfDate) continue
    dates.add(r.tanggal)
  }
  return dates.size
}

export function rekapToCsv(rows: RekapAbsensiRow[]): string {
  const header =
    "NIS,Nama,Kelompok,Hadir,Izin,Sakit,Tidak Hadir,Katering,Jemput Datang,Jemput Pulang"
  const lines = rows.map((r) =>
    [
      r.nis ?? "",
      `"${r.nama.replace(/"/g, '""')}"`,
      `"${r.kelompok.replace(/"/g, '""')}"`,
      r.hadir,
      r.izin,
      r.sakit,
      r.tidak_hadir,
      r.katering,
      r.jemput_datang,
      r.jemput_pulang,
    ].join(","),
  )
  return [header, ...lines].join("\n")
}

export function downloadCsv(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
