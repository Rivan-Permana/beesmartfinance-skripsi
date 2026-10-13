import { api } from "@/core/api"
import type { KehadiranSiswa, MenuKatering, MenuKateringInput, Paginated } from "@/types/api"
import { DEFAULT_TARIF_JUMAT, DEFAULT_TARIF_SEN_KAM } from "@/core/config"

export const menuKateringApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<MenuKatering>>("/menu-katering/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<MenuKatering[]> {
    const out: MenuKatering[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await menuKateringApi.list({ ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  create: (payload: MenuKateringInput) =>
    api.post<MenuKatering>("/menu-katering/", payload).then((r) => r.data),
  createWithForm: (payload: { tanggal: string; keterangan: string; gambar?: File }) => {
    const fd = new FormData()
    fd.append("tanggal", payload.tanggal)
    fd.append("keterangan", payload.keterangan)
    if (payload.gambar) fd.append("gambar", payload.gambar)
    return api.post<MenuKatering>("/menu-katering/", fd).then((r) => r.data)
  },
  update: (id: number, payload: Partial<MenuKateringInput>) =>
    api.patch<MenuKatering>(`/menu-katering/${id}/`, payload).then((r) => r.data),
  updateWithForm: (id: number, payload: { keterangan?: string; gambar?: File | null }) => {
    const fd = new FormData()
    if (payload.keterangan !== undefined) fd.append("keterangan", payload.keterangan)
    if (payload.gambar) fd.append("gambar", payload.gambar)
    return api.patch<MenuKatering>(`/menu-katering/${id}/`, fd).then((r) => r.data)
  },
  remove: (id: number) => api.delete(`/menu-katering/${id}/`),
}

export interface TarifKateringResponse {
  periode_bulan: number
  periode_tahun: number
  tarif_harian: string
  tarif_jumat: string
  is_default: boolean
}

export const tarifKateringApi = {
  get: (bulan: number, tahun: number) =>
    api
      .get<TarifKateringResponse>("/tarif-katering/", { params: { bulan, tahun } })
      .then((r) => r.data),
  set: (payload: {
    periode_bulan: number
    periode_tahun: number
    tarif_harian: number
    tarif_jumat?: number
  }) => api.put<TarifKateringResponse>("/tarif-katering/", payload).then((r) => r.data),
}

export interface KateringRekapRow {
  siswaId: number
  nis: string | null
  nama: string
  kelompok: string
  hariSenKam: number
  hariJumat: number
  hariKatering: number
  tarifSenKam: number
  tarifJumat: number
  total: number
}

function weekdayBucket(isoDate: string): "sen_kam" | "jumat" | null {
  const d = new Date(isoDate + "T12:00:00")
  const day = d.getDay()
  if (day >= 1 && day <= 4) return "sen_kam"
  if (day === 5) return "jumat"
  return null
}

export function buildKateringRekapFromRecords(
  students: { id: number; nis: string | null; nama: string; kelompok: string }[],
  records: KehadiranSiswa[],
  tarifSenKam: number,
  tarifJumat: number,
): KateringRekapRow[] {
  const agg = new Map<number, KateringRekapRow>()
  for (const s of students) {
    agg.set(s.id, {
      siswaId: s.id,
      nis: s.nis,
      nama: s.nama,
      kelompok: s.kelompok,
      hariSenKam: 0,
      hariJumat: 0,
      hariKatering: 0,
      tarifSenKam,
      tarifJumat,
      total: 0,
    })
  }
  for (const r of records) {
    if (!r.ikut_katering) continue
    const row = agg.get(r.siswa)
    if (!row) continue
    const bucket = weekdayBucket(r.tanggal)
    if (bucket === "sen_kam") row.hariSenKam += 1
    else if (bucket === "jumat") row.hariJumat += 1
    else continue
    row.hariKatering += 1
  }
  return [...agg.values()]
    .map((r) => ({
      ...r,
      total: r.hariSenKam * tarifSenKam + r.hariJumat * tarifJumat,
    }))
    .filter((r) => r.hariKatering > 0)
    .sort((a, b) => a.nama.localeCompare(b.nama))
}

/** @deprecated gunakan buildKateringRekapFromRecords */
export function buildKateringRekap(
  absensiRows: { siswaId: number; nis: string | null; nama: string; kelompok: string; katering: number }[],
  tarif: number,
): KateringRekapRow[] {
  return absensiRows
    .filter((r) => r.katering > 0)
    .map((r) => ({
      siswaId: r.siswaId,
      nis: r.nis,
      nama: r.nama,
      kelompok: r.kelompok,
      hariSenKam: r.katering,
      hariJumat: 0,
      hariKatering: r.katering,
      tarifSenKam: tarif,
      tarifJumat: DEFAULT_TARIF_JUMAT,
      total: r.katering * tarif,
    }))
}

export function kateringRekapToCsv(rows: KateringRekapRow[]): string {
  const header = "NIS,Nama,Kelompok,Hari Sen-Kam,Hari Jumat,Total Hari,Tarif Sen-Kam,Tarif Jumat,Total"
  const lines = rows.map((r) =>
    [
      r.nis ?? "",
      `"${r.nama.replace(/"/g, '""')}"`,
      `"${r.kelompok.replace(/"/g, '""')}"`,
      r.hariSenKam,
      r.hariJumat,
      r.hariKatering,
      r.tarifSenKam,
      r.tarifJumat,
      r.total,
    ].join(","),
  )
  return [header, ...lines].join("\n")
}

const HARI = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]

export function formatTanggalId(iso: string): string {
  const d = new Date(iso + "T12:00:00")
  return `${HARI[d.getDay()]}, ${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`
}

/** Senin–Jumat dari minggu yang berisi `anchor` */
export function weekdaysOfWeek(anchor: Date): string[] {
  const d = new Date(anchor)
  const day = d.getDay()
  const mondayOffset = day === 0 ? -6 : 1 - day
  const monday = new Date(d)
  monday.setDate(d.getDate() + mondayOffset)
  return Array.from({ length: 5 }, (_, i) => {
    const x = new Date(monday)
    x.setDate(monday.getDate() + i)
    const y = x.getFullYear()
    const m = String(x.getMonth() + 1).padStart(2, "0")
    const dd = String(x.getDate()).padStart(2, "0")
    return `${y}-${m}-${dd}`
  })
}

export function weekRange(dates: string[]) {
  return { tanggal__gte: dates[0], tanggal__lte: dates[dates.length - 1] }
}

export { DEFAULT_TARIF_SEN_KAM, DEFAULT_TARIF_JUMAT }
