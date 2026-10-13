<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"

import {
  AUDIT_ACTION_LABEL,
  AUDIT_TABLE_LABEL,
  AUDIT_TABLE_SHORT,
  buildAuditDiffRows,
  formatRecordId,
  type UserLabelMap,
} from "./auditFormat"
import { auditLogApi } from "./api"
import { notifyError } from "@/core/errors"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import type { AuditLog } from "@/types/api"

const toast = useToast()

const rows = ref<AuditLog[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const userLabels = ref<UserLabelMap>({})

const filterTable = ref<string | null>(null)
const filterUser = ref<number | null>(null)
const filterAction = ref<string | null>(null)
const filterSearch = ref("")
const filterDateFrom = ref<Date | null>(null)
const filterDateTo = ref<Date | null>(null)

const detailOpen = ref(false)
const detailRow = ref<AuditLog | null>(null)
const showAllFields = ref(false)

const TABLE_OPTIONS = [
  { label: "Semua tabel", value: null },
  { label: "Daftar akun (COA)", value: "ms_coa" },
  { label: "Jurnal", value: "tr_jurnal" },
  { label: "Baris jurnal", value: "tr_jurnal_detail" },
  { label: "Anggaran", value: "tr_anggaran" },
  { label: "Golongan akun", value: "ms_golongan" },
  { label: "Sub-golongan akun", value: "ms_sub_golongan" },
]

const ACTION_OPTIONS = [
  { label: "Semua aksi", value: null },
  { label: "Tambah data", value: "INSERT" },
  { label: "Ubah data", value: "UPDATE" },
  { label: "Hapus data", value: "DELETE" },
]

const userOptions = computed(() => {
  const map = new Map<number, string>()
  for (const row of rows.value) {
    if (row.changed_by != null) {
      map.set(row.changed_by, row.changed_by_username ?? `#${row.changed_by}`)
    }
  }
  return [
    { label: "Semua pengguna", value: null },
    ...[...map.entries()].map(([value, label]) => ({ label, value })),
  ]
})

const detailChangedRows = computed(() => {
  if (!detailRow.value) return []
  return buildAuditDiffRows(
    detailRow.value.old_data,
    detailRow.value.new_data,
    userLabels.value,
    true,
  )
})

const detailAllRows = computed(() => {
  if (!detailRow.value) return []
  return buildAuditDiffRows(
    detailRow.value.old_data,
    detailRow.value.new_data,
    userLabels.value,
    false,
  )
})

const detailRows = computed(() =>
  showAllFields.value ? detailAllRows.value : detailChangedRows.value,
)

function toIsoStart(d: Date) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x.toISOString()
}

function toIsoEnd(d: Date) {
  const x = new Date(d)
  x.setHours(23, 59, 59, 999)
  return x.toISOString()
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
  })
}

function actionSeverity(action: string): "success" | "info" | "warn" | "danger" | "secondary" {
  if (action === "INSERT") return "success"
  if (action === "UPDATE") return "info"
  if (action === "DELETE") return "danger"
  return "secondary"
}

function tableLabel(name: string) {
  return AUDIT_TABLE_LABEL[name] ?? name
}

function tableShort(name: string) {
  return AUDIT_TABLE_SHORT[name] ?? name
}

async function loadUserLabels() {
  try {
    userLabels.value = await auditLogApi.userLabels()
  } catch {
    userLabels.value = {}
  }
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, string | number> = { page: page.value }
    if (filterTable.value) params.table_name = filterTable.value
    if (filterUser.value) params.changed_by = filterUser.value
    if (filterAction.value) params.action = filterAction.value
    if (filterSearch.value.trim()) params.search = filterSearch.value.trim()
    if (filterDateFrom.value) params.changed_at__gte = toIsoStart(filterDateFrom.value)
    if (filterDateTo.value) params.changed_at__lte = toIsoEnd(filterDateTo.value)

    const data = await auditLogApi.list(params)
    rows.value = data.results
    total.value = data.count
  } catch (e) {
    const err = e as { response?: { status?: number } }
    if (err?.response?.status === 404 && page.value > 1) {
      page.value = 1
      loading.value = false
      await load()
      return
    }
    notifyError(toast, e, "Gagal memuat audit log.")
  } finally {
    loading.value = false
  }
}

function onPage(event: { page: number }) {
  page.value = event.page + 1
  load()
}

function resetFilters() {
  filterTable.value = null
  filterUser.value = null
  filterAction.value = null
  filterSearch.value = ""
  filterDateFrom.value = null
  filterDateTo.value = null
  page.value = 1
  load()
}

function openDetail(row: AuditLog) {
  detailRow.value = row
  showAllFields.value = false
  detailOpen.value = true
}

watch(
  [filterTable, filterUser, filterAction, filterDateFrom, filterDateTo],
  () => {
    page.value = 1
    load()
  },
)

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(filterSearch, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    load()
  }, 400)
})

onMounted(async () => {
  await Promise.all([loadUserLabels(), load()])
})
</script>

<template>
  <PageLayout
    title="Log Audit"
    subtitle="Riwayat perubahan data akuntansi — hanya baca (Staff Keuangan & Kepala Sekolah)."
  >
    <template #filters>
      <div class="bee-filter-row">
        <Select
          v-model="filterTable"
          :options="TABLE_OPTIONS"
          option-label="label"
          option-value="value"
          placeholder="Tabel"
          class="bee-filter-field"
        />
        <Select
          v-model="filterUser"
          :options="userOptions"
          option-label="label"
          option-value="value"
          placeholder="Pengguna"
          class="bee-filter-field"
        />
        <Select
          v-model="filterAction"
          :options="ACTION_OPTIONS"
          option-label="label"
          option-value="value"
          placeholder="Aksi"
          class="bee-filter-field"
        />
        <DatePicker
          v-model="filterDateFrom"
          date-format="dd/mm/yy"
          placeholder="Dari tanggal"
          show-icon
          class="bee-filter-field"
        />
        <DatePicker
          v-model="filterDateTo"
          date-format="dd/mm/yy"
          placeholder="Sampai tanggal"
          show-icon
          class="bee-filter-field"
        />
        <InputText
          v-model="filterSearch"
          placeholder="Cari tabel / ID / aksi…"
          class="bee-filter-field bee-filter-field--grow"
        />
        <Button label="Reset" severity="secondary" outlined @click="resetFilters" />
      </div>
    </template>

    <Message severity="info" :closable="false" class="bee-mb">
      <strong>Apa itu audit log?</strong> Setiap kali data akuntansi diubah (daftar akun, jurnal, anggaran),
      sistem menyimpan jejak: <em>siapa</em>, <em>kapan</em>, dan <em>apa yang berubah</em>.
      Halaman ini tidak bisa dipakai untuk mengedit data — hanya untuk melihat riwayat.
    </Message>

    <DataTable
      :value="rows"
      :loading="loading"
      lazy
      paginator
      :rows="pageSize"
      :total-records="total"
      :first="(page - 1) * pageSize"
      data-key="id"
      striped-rows
      @page="onPage"
    >
      <template #empty>
        <EmptyState message="Belum ada perubahan tercatat. Entri muncul otomatis saat COA, jurnal, atau anggaran diubah." />
      </template>

      <Column field="changed_at" header="Waktu" sortable>
        <template #body="{ data }">
          {{ formatDateTime(data.changed_at) }}
        </template>
      </Column>
      <Column field="table_name" header="Tabel">
        <template #body="{ data }">
          {{ tableShort(data.table_name) }}
        </template>
      </Column>
      <Column field="action" header="Aksi">
        <template #body="{ data }">
          <Tag
            :value="AUDIT_ACTION_LABEL[data.action] ?? data.action"
            :severity="actionSeverity(data.action)"
          />
        </template>
      </Column>
      <Column field="row_pk" header="ID record">
        <template #body="{ data }">
          <span
            class="record-id"
            :title="formatRecordId(data.row_pk).hint + (formatRecordId(data.row_pk).full ? `\n${formatRecordId(data.row_pk).full}` : '')"
          >
            {{ formatRecordId(data.row_pk).short }}
          </span>
        </template>
      </Column>
      <Column field="changed_by_username" header="Oleh">
        <template #body="{ data }">
          {{ data.changed_by_username ?? "Sistem / tidak tercatat" }}
        </template>
      </Column>
      <Column header="" style="width: 6rem">
        <template #body="{ data }">
          <Button label="Detail" size="small" text @click="openDetail(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="detailOpen"
      modal
      header="Detail Perubahan"
      :style="{ width: 'min(760px, 96vw)' }"
    >
      <template v-if="detailRow">
        <div class="audit-meta">
          <div class="audit-meta-item">
            <span class="audit-meta-label">Waktu</span>
            <strong>{{ formatDateTime(detailRow.changed_at) }}</strong>
          </div>
          <div class="audit-meta-item">
            <span class="audit-meta-label">Tabel</span>
            <strong>{{ tableLabel(detailRow.table_name) }}</strong>
          </div>
          <div class="audit-meta-item">
            <span class="audit-meta-label">Aksi</span>
            <Tag
              :value="AUDIT_ACTION_LABEL[detailRow.action] ?? detailRow.action"
              :severity="actionSeverity(detailRow.action)"
            />
          </div>
          <div class="audit-meta-item">
            <span class="audit-meta-label">ID record</span>
            <strong :title="formatRecordId(detailRow.row_pk).full">
              {{ formatRecordId(detailRow.row_pk).short }}
            </strong>
            <small class="audit-meta-hint">{{ formatRecordId(detailRow.row_pk).hint }}</small>
          </div>
          <div class="audit-meta-item span2">
            <span class="audit-meta-label">Diubah oleh</span>
            <strong>{{ detailRow.changed_by_username ?? "Sistem / tidak tercatat" }}</strong>
          </div>
        </div>

        <div v-if="detailRows.length" class="audit-diff">
          <div class="audit-diff-head">
            <h4>{{ showAllFields ? "Semua kolom" : "Kolom yang berubah" }}</h4>
            <Button
              :label="showAllFields ? 'Hanya yang berubah' : 'Tampilkan semua kolom'"
              size="small"
              text
              @click="showAllFields = !showAllFields"
            />
          </div>
          <table class="audit-diff-table">
            <thead>
              <tr>
                <th>Kolom</th>
                <th>Sebelum</th>
                <th>Sesudah</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in detailRows"
                :key="row.key"
                :class="{ changed: row.changed }"
              >
                <td class="col-label">{{ row.label }}</td>
                <td>{{ row.old }}</td>
                <td>{{ row.new }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="audit-empty-diff">
          Tidak ada perubahan kolom yang terdeteksi untuk entri ini.
        </p>
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.bee-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.bee-filter-field {
  min-width: 10rem;
}

.bee-filter-field--grow {
  flex: 1;
  min-width: 12rem;
}

.bee-mb {
  margin-bottom: 1rem;
}

.record-id {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  cursor: help;
}

.audit-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
  padding: 1rem 1.1rem;
  background: var(--bee-cream-100, #faf6eb);
  border-radius: var(--bee-radius-md, 12px);
  margin-bottom: 1rem;
  border: 1px solid rgba(46, 42, 110, 0.06);
}

.audit-meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.audit-meta-item.span2 {
  grid-column: 1 / -1;
}

.audit-meta-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--app-text-muted);
}

.audit-meta-hint {
  font-size: 0.78rem;
  color: var(--app-text-muted);
}

.audit-diff-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.audit-diff-head h4 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--bee-secondary);
}

.audit-diff-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
  border: 1px solid var(--app-border, #e8e4dc);
  border-radius: 8px;
  overflow: hidden;
}

.audit-diff-table th,
.audit-diff-table td {
  padding: 0.5rem 0.65rem;
  border-bottom: 1px solid var(--app-border, #e8e4dc);
  text-align: left;
  vertical-align: top;
}

.audit-diff-table th {
  background: var(--bee-cream);
  font-weight: 700;
  color: var(--bee-secondary);
}

.audit-diff-table tr:last-child td {
  border-bottom: none;
}

.audit-diff-table tr.changed td {
  background: rgba(229, 25, 127, 0.05);
}

.audit-diff-table tr.changed .col-label {
  font-weight: 600;
}

.audit-diff-table tr.changed td:last-child {
  font-weight: 600;
  color: var(--bee-secondary);
}

.audit-diff-table .col-label {
  width: 34%;
  color: var(--bee-secondary);
}

.audit-empty-diff {
  margin: 0;
  font-size: 0.85rem;
  color: var(--app-text-muted);
}
</style>
