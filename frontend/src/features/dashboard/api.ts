import { api } from "@/core/api"
import type {
  DashboardRingkasan,
  LabaRugiBulananResult,
  MenuKatering,
  PrediksiKasRow,
} from "@/types/api"

export type DashboardFilter = {
  tahun?: number
  bulan?: number
  tanggal?: string
  /** ID periode akuntansi (tahun ajaran) */
  periode?: number
}

export const dashboardApi = {
  ringkasan: (filter?: DashboardFilter) =>
    api
      .get<DashboardRingkasan>("/dashboard/ringkasan/", { params: filter })
      .then((r) => r.data),
  prediksiKas: (scope?: number | { periode: number }) =>
    api
      .get<PrediksiKasRow[]>("/dashboard/prediksi-kas/", {
        params: typeof scope === "number" ? { tahun: scope } : scope ?? {},
      })
      .then((r) => r.data),
  labaRugiBulanan: (scope?: number | { periode: number }) =>
    api
      .get<LabaRugiBulananResult>("/dashboard/laba-rugi-bulanan/", {
        params: typeof scope === "number" ? { tahun: scope } : scope ?? {},
      })
      .then((r) => r.data),
  menuHariIni: (tanggal?: string) =>
    api
      .get<{ tanggal: string; menu: MenuKatering | null }>("/dashboard/menu-katering/", {
        params: tanggal ? { tanggal } : {},
      })
      .then((r) => r.data),
}
