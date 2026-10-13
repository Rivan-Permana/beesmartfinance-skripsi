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
}

export const dashboardApi = {
  ringkasan: (filter?: DashboardFilter) =>
    api
      .get<DashboardRingkasan>("/dashboard/ringkasan/", { params: filter })
      .then((r) => r.data),
  prediksiKas: (tahun?: number) =>
    api
      .get<PrediksiKasRow[]>("/dashboard/prediksi-kas/", {
        params: tahun ? { tahun } : {},
      })
      .then((r) => r.data),
  labaRugiBulanan: (tahun?: number) =>
    api
      .get<LabaRugiBulananResult>("/dashboard/laba-rugi-bulanan/", {
        params: tahun ? { tahun } : {},
      })
      .then((r) => r.data),
  menuHariIni: (tanggal?: string) =>
    api
      .get<{ tanggal: string; menu: MenuKatering | null }>("/dashboard/menu-katering/", {
        params: tanggal ? { tanggal } : {},
      })
      .then((r) => r.data),
}
