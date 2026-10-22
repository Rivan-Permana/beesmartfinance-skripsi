import { api } from "@/core/api"
import type {
  ArmadaJemputan,
  ArmadaJemputanInput,
  Paginated,
  PendaftaranJemputan,
  PendaftaranJemputanInput,
} from "@/types/api"

async function allPages<T>(path: string, params?: Record<string, unknown>): Promise<T[]> {
  const rows: T[] = []
  for (let page = 1; ; page++) {
    const { data } = await api.get<Paginated<T>>(path, { params: { page_size: 200, ...params, page } })
    rows.push(...data.results)
    if (!data.next) return rows
  }
}

export const armadaApi = {
  listAll: () => allPages<ArmadaJemputan>("/armada-jemputan/"),
  list: () =>
    api.get<Paginated<ArmadaJemputan>>("/armada-jemputan/").then((r) => r.data.results),
  create: (payload: ArmadaJemputanInput) =>
    api.post<ArmadaJemputan>("/armada-jemputan/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<ArmadaJemputanInput>) =>
    api.patch<ArmadaJemputan>(`/armada-jemputan/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/armada-jemputan/${id}/`),
}

export const pendaftaranJemputanApi = {
  listAll: (params?: Record<string, unknown>) => allPages<PendaftaranJemputan>("/pendaftaran-jemputan/", params),
  list: (params?: Record<string, unknown>) =>
    api
      .get<Paginated<PendaftaranJemputan>>("/pendaftaran-jemputan/", { params })
      .then((r) => r.data.results),
  create: (payload: PendaftaranJemputanInput) =>
    api.post<PendaftaranJemputan>("/pendaftaran-jemputan/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<PendaftaranJemputanInput>) =>
    api
      .patch<PendaftaranJemputan>(`/pendaftaran-jemputan/${id}/`, payload)
      .then((r) => r.data),
  remove: (id: number) => api.delete(`/pendaftaran-jemputan/${id}/`),
}

export interface JemputanRekapRow {
  siswaId: number
  nis: string | null
  nama: string
  alamat: string
  armada: string
  tarifPerTrip: number
  jemputDatang: number
  jemputPulang: number
  totalNominal: number
}

export function buildJemputanRekap(
  pendaftaran: PendaftaranJemputan[],
  siswaMap: Map<number, { nis: string | null; nama: string; alamat: string | null }>,
  armadaMap: Map<number, string>,
  absensiBySiswa: Map<number, { datang: number; pulang: number }>,
): JemputanRekapRow[] {
  const bySiswa = new Map<number, JemputanRekapRow>()
  // Billing selects the latest registration by ID, including its zero price.
  const latest = new Map<number, PendaftaranJemputan>()
  for (const row of pendaftaran) {
    if (!latest.has(row.siswa) || row.id > latest.get(row.siswa)!.id) latest.set(row.siswa, row)
  }
  for (const p of latest.values()) {
    const s = siswaMap.get(p.siswa)
    if (!s) continue
    const harga = Number(p.harga)
    const abs = absensiBySiswa.get(p.siswa) ?? { datang: 0, pulang: 0 }
    bySiswa.set(p.siswa, {
      siswaId: p.siswa, nis: s.nis, nama: s.nama, alamat: s.alamat ?? "-",
      armada: p.armada ? armadaMap.get(p.armada) ?? `#${p.armada}` : "Belum ditentukan",
      tarifPerTrip: harga, jemputDatang: abs.datang, jemputPulang: abs.pulang,
      totalNominal: Math.round(harga * 100) * (abs.datang + abs.pulang) / 100,
    })
  }

  return [...bySiswa.values()].sort((a, b) => a.nama.localeCompare(b.nama))
}

export function jemputanRekapToCsv(rows: JemputanRekapRow[]): string {
  const header =
    "NIS,Nama,Alamat,Armada,Tarif per Trip,Jemput Datang,Jemput Pulang,Total"
  const lines = rows.map((r) =>
    [
      r.nis ?? "",
      `"${r.nama.replace(/"/g, '""')}"`,
      `"${r.alamat.replace(/"/g, '""')}"`,
      `"${r.armada.replace(/"/g, '""')}"`,
      r.tarifPerTrip,
      r.jemputDatang,
      r.jemputPulang,
      r.totalNominal,
    ].join(","),
  )
  return [header, ...lines].join("\n")
}
