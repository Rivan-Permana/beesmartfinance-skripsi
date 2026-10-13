import { api } from "@/core/api"
import type { AuditLog, Paginated } from "@/types/api"

export interface AuditLogListParams {
  page?: number
  table_name?: string
  changed_by?: number
  action?: string
  changed_at__gte?: string
  changed_at__lte?: string
  search?: string
}

export const auditLogApi = {
  list: (params?: AuditLogListParams) =>
    api.get<Paginated<AuditLog>>("/audit-log/", { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<AuditLog>(`/audit-log/${id}/`).then((r) => r.data),
  userLabels: () =>
    api.get<Record<string, { username: string; nama: string }>>("/auth/user-labels/").then((r) => r.data),
}
