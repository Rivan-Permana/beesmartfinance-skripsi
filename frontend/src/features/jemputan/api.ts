import { api } from "@/core/api"
import type {
  ArmadaJemputan,
  ArmadaJemputanInput,
  Paginated,
  PendaftaranJemputan,
  PendaftaranJemputanInput,
} from "@/types/api"

export const armadaApi = {
  list: () =>
    api.get<Paginated<ArmadaJemputan>>("/armada-jemputan/").then((r) => r.data.results),
  create: (payload: ArmadaJemputanInput) =>
    api.post<ArmadaJemputan>("/armada-jemputan/", payload).then((r) => r.data),
  update: (id: number, payload: Partial<ArmadaJemputanInput>) =>
    api.patch<ArmadaJemputan>(`/armada-jemputan/${id}/`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/armada-jemputan/${id}/`),
}

export const pendaftaranJemputanApi = {
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

  for (const p of pendaftaran) {
    const s = siswaMap.get(p.siswa)
    if (!s) continue
    const harga = Number(p.harga) || 0
    const armadaLabel = p.armada ? armadaMap.get(p.armada) ?? `#${p.armada}` : "-"
    const abs = absensiBySiswa.get(p.siswa) ?? { datang: 0, pulang: 0 }
    const trips = abs.datang + abs.pulang

    const existing = bySiswa.get(p.siswa)
    if (existing) {
      existing.tarifPerTrip = Math.max(existing.tarifPerTrip, harga)
      existing.armada = existing.armada.includes(armadaLabel)
        ? existing.armada
        : `${existing.armada}, ${armadaLabel}`
      existing.totalNominal = existing.tarifPerTrip * trips
    } else {
      bySiswa.set(p.siswa, {
        siswaId: p.siswa,
        nis: s.nis,
        nama: s.nama,
        alamat: s.alamat ?? "-",
        armada: armadaLabel,
        tarifPerTrip: harga,
        jemputDatang: abs.datang,
        jemputPulang: abs.pulang,
        totalNominal: harga * trips,
      })
    }
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
