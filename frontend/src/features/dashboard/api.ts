import { api } from "@/core/api"
import type {
  DashboardRingkasan,
  LabaRugiBulananResult,
  PrediksiKasRow,
} from "@/types/api"

export const dashboardApi = {
  ringkasan: () =>
    api.get<DashboardRingkasan>("/dashboard/ringkasan/").then((r) => r.data),
  prediksiKas: () =>
    api.get<PrediksiKasRow[]>("/dashboard/prediksi-kas/").then((r) => r.data),
  labaRugiBulanan: (tahun?: number) =>
    api
      .get<LabaRugiBulananResult>("/dashboard/laba-rugi-bulanan/", {
        params: tahun ? { tahun } : {},
      })
      .then((r) => r.data),
}
