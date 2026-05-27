import { api } from "@/core/api"
import type { DashboardRingkasan } from "@/types/api"

export const dashboardApi = {
  ringkasan: () =>
    api.get<DashboardRingkasan>("/dashboard/ringkasan/").then((r) => r.data),
}
