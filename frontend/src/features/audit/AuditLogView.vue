<script setup lang="ts">
import BeePaginator from "@/shared/components/BeePaginator.vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { computed, onMounted, onUnmounted, ref, watch } from "vue"

import {
  AUDIT_ACTION_LABEL,
  AUDIT_TABLE_LABEL,
  AUDIT_TABLE_SHORT,
  buildAuditDiffRows,
  formatRecordId,
  type UserLabelMap,
} from "./auditFormat"
import { auditLogApi } from "./api"
import { friendlyError } from "@/core/errors"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import type { AuditLog } from "@/types/api"

const rows = ref<AuditLog[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref("")
const page = ref(1)
const pageSize = 20
const userLabels = ref<UserLabelMap>({})

const filterTable = ref<string | null>(null)
const filterUser = ref<number | null>(null)
const filterAction = ref<string | null>(null)
const filterSearch = ref("")
const filterDateFrom = ref<Date | null>(null)
const filterDateTo = ref<Date | null>(null)
const filtersOpen = ref(false)
const filterCount = computed(() => [filterTable.value, filterUser.value, filterAction.value, filterSearch.value.trim(), filterDateFrom.value, filterDateTo.value].filter((value) => value !== null && value !== "").length)

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
  for (const [id, user] of Object.entries(userLabels.value)) {
    map.set(Number(id), user.nama || user.username)
  }
  for (const row of rows.value) {
    if (row.changed_by != null) {
      map.set(row.changed_by, row.changed_by_username ?? map.get(row.changed_by) ?? `#${row.changed_by}`)
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
  const request = ++requestId
  loading.value = true
  error.value = ""
  if (filterDateFrom.value && filterDateTo.value && filterDateFrom.value > filterDateTo.value) {
    rows.value = []; total.value = 0; loading.value = false
    error.value = "Tanggal selesai harus sesudah atau sama dengan tanggal mulai."
    return
  }
  try {
    const params: Record<string, string | number> = { page: page.value }
    if (filterTable.value) params.table_name = filterTable.value
    if (filterUser.value) params.changed_by = filterUser.value
    if (filterAction.value) params.action = filterAction.value
    if (filterSearch.value.trim()) params.search = filterSearch.value.trim()
    if (filterDateFrom.value) params.changed_at__gte = toIsoStart(filterDateFrom.value)
    if (filterDateTo.value) params.changed_at__lte = toIsoEnd(filterDateTo.value)

    const data = await auditLogApi.list(params)
    if (request !== requestId) return
    rows.value = data.results
    total.value = data.count
  } catch (cause) {
    if (request !== requestId) return
    const err = cause as { response?: { status?: number } }
    if (err?.response?.status === 404 && page.value > 1) {
      page.value = 1
      await load()
      return
    }
    rows.value = []; total.value = 0
    const message = friendlyError(cause, "Log audit belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally {
    if (request === requestId) loading.value = false
  }
}
let requestId = 0

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
  filtersOpen.value = false
  page.value = 1
}

function openDetail(row: AuditLog) {
  detailRow.value = row
  showAllFields.value = false
  detailOpen.value = true
}

watch(
  [filterTable, filterUser, filterAction, filterDateFrom, filterDateTo, filterSearch],
  () => {
    if (searchTimer) clearTimeout(searchTimer)
    requestId++
    rows.value = []; total.value = 0; loading.value = true
    page.value = 1
    searchTimer = setTimeout(load, filterSearch.value.trim() ? 400 : 0)
  },
)

let searchTimer: ReturnType<typeof setTimeout> | null = null
onUnmounted(() => { if (searchTimer) clearTimeout(searchTimer); requestId++ })

onMounted(async () => {
  await Promise.all([loadUserLabels(), load()])
})
</script>

<template>
  <PageLayout
    title="Log audit"
    subtitle="Jejak perubahan data akuntansi yang dapat diperiksa oleh Keuangan dan Kepala Sekolah."
    :surface="false"
  >
    <template #filters>
      <Button class="audit-filter-toggle" :label="filterCount ? 'Filter log · ' + filterCount + ' aktif' : 'Filter log'" severity="secondary" :aria-expanded="filtersOpen" @click="filtersOpen = !filtersOpen"><template #icon><Icon name="sliders-horizontal" /></template></Button>
      <div class="audit-filter-row" :class="{ 'is-open': filtersOpen }">
        <div class="audit-filter-field"><label for="audit-table">Jenis data</label>
        <Select
          input-id="audit-table"
          v-model="filterTable"
          :options="TABLE_OPTIONS"
          option-label="label"
          option-value="value"
          placeholder="Tabel"
          fluid
        />
        </div>
        <div class="audit-filter-field"><label for="audit-user">Diubah oleh</label>
        <Select
          input-id="audit-user"
          v-model="filterUser"
          :options="userOptions"
          option-label="label"
          option-value="value"
          placeholder="Pengguna"
          fluid
        />
        </div>
        <div class="audit-filter-field"><label for="audit-action">Jenis perubahan</label>
        <Select
          input-id="audit-action"
          v-model="filterAction"
          :options="ACTION_OPTIONS"
          option-label="label"
          option-value="value"
          placeholder="Aksi"
          fluid
        />
        </div>
        <div class="audit-filter-field"><label for="audit-from">Dari tanggal</label>
        <DatePicker
          input-id="audit-from"
          v-model="filterDateFrom"
          date-format="dd/mm/yy"
          placeholder="Dari tanggal"
          show-icon
          fluid
        ><template #inputicon="{ clickCallback }"><button type="button" class="audit-calendar-button" aria-label="Buka kalender tanggal awal" @click="clickCallback"><Icon name="calendar-blank" /></button></template><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker>
        </div>
        <div class="audit-filter-field"><label for="audit-to">Sampai tanggal</label>
        <DatePicker
          input-id="audit-to"
          v-model="filterDateTo"
          date-format="dd/mm/yy"
          placeholder="Sampai tanggal"
          show-icon
          fluid
        ><template #inputicon="{ clickCallback }"><button type="button" class="audit-calendar-button" aria-label="Buka kalender tanggal akhir" @click="clickCallback"><Icon name="calendar-blank" /></button></template><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker>
        </div>
        <div class="audit-filter-field audit-filter-search"><label for="audit-search">Cari kode atau ID</label><SearchField input-id="audit-search" v-model="filterSearch" placeholder="Kode tabel, ID, atau aksi" hint="Pencarian server pada seluruh log audit" /></div>
        <Button label="Hapus filter" severity="secondary" outlined @click="resetFilters" />
      </div>
    </template>

    <div class="audit-scope"><Icon name="info" /><p>Log ini mencatat siapa yang mengubah data, tindakannya, dan waktunya. Buka rincian untuk membandingkan nilai sebelum dan sesudah. Pencarian dijalankan pada kode tabel, ID record, dan aksi.</p></div>
    <section class="audit-panel" aria-label="Daftar log audit" :aria-busy="loading">
      <header class="audit-panel-head"><div><h2>Riwayat perubahan</h2><p role="status">{{ loading ? 'Memuat log…' : error ? 'Riwayat belum tersedia' : total + ' perubahan tercatat' }}</p></div><Button label="Muat ulang" severity="secondary" :disabled="loading" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template></Button></header>
      <div v-if="error" class="audit-notice"><Message severity="error" :closable="false">{{ error }}</Message><Button label="Coba muat ulang log" severity="secondary" @click="load" /></div>
      <div v-if="!loading && !error && !rows.length" class="audit-empty"><Icon name="clock" /><h3>{{ filterTable || filterUser || filterAction || filterSearch || filterDateFrom || filterDateTo ? 'Tidak ada log yang cocok' : 'Belum ada perubahan tercatat' }}</h3><p>{{ filterTable || filterUser || filterAction || filterSearch || filterDateFrom || filterDateTo ? 'Ubah atau hapus filter untuk melihat riwayat lain.' : 'Perubahan pada data akuntansi akan muncul otomatis di sini.' }}</p></div>
      <p v-if="rows.length" class="audit-scroll-hint"><Icon name="caret-right" /> Geser tabel untuk melihat waktu dan rincian.</p>
      <div v-if="!error && (loading || rows.length)" class="audit-table-scroll" role="region" tabindex="0" aria-label="Tabel log audit dapat digulir horizontal">

    <DataTable
      :value="rows"
      :loading="loading"
      lazy
      data-key="id"
      striped-rows
      @page="onPage"
    >
      <Column field="changed_by_username" header="Oleh">
        <template #body="{ data }">
          {{ data.changed_by_username ?? "Sistem / tidak tercatat" }}
        </template>
      </Column>
      <Column field="table_name" header="Data">
        <template #body="{ data }">
          {{ tableShort(data.table_name) }}
        </template>
      </Column>
      <Column field="action" header="Perubahan">
        <template #body="{ data }">
          <Tag
            :value="AUDIT_ACTION_LABEL[data.action] ?? data.action"
            :severity="actionSeverity(data.action)"
          />
        </template>
      </Column>
      <Column field="changed_at" header="Waktu">
        <template #body="{ data }">{{ formatDateTime(data.changed_at) }}</template>
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
      <Column header="Rincian" style="width: 7rem">
        <template #body="{ data }">
          <Button label="Lihat" size="small" text @click="openDetail(data)" />
        </template>
      </Column>
    </DataTable>
      </div>
      <BeePaginator v-if="!error" :first="(page - 1) * pageSize" :rows="pageSize" :total-records="total" @page="onPage" />
    </section>

    <Dialog
      v-model:visible="detailOpen"
      modal
      header="Rincian perubahan"
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
                <td data-label="Sebelum">{{ row.old }}</td>
                <td data-label="Sesudah">{{ row.new }}</td>
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
.audit-filter-row { display: flex; flex-wrap: wrap; align-items: end; gap: var(--bee-space-3); }
.audit-filter-field { display: grid; gap: var(--bee-space-2); flex: 1 1 170px; min-width: 0; }
.audit-filter-field label { font-size: var(--bee-type-caption); font-weight: 600; }
.audit-filter-search { flex: 1.6 1 230px; }
.audit-filter-search :deep(.bee-search-field) { min-width: 0; }
.audit-filter-toggle { display: none; }
.audit-calendar-button { display: grid; place-items: center; width: 32px; height: 32px; padding: 0; border: 0; background: transparent; color: var(--app-text-muted); cursor: pointer; }
.audit-calendar-button .bee-icon { width: 19px; height: 19px; }
.audit-calendar-button:focus-visible { outline: 2px solid var(--bee-color-focus); outline-offset: 2px; }
.audit-scope { display: flex; align-items: start; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); color: var(--app-text-muted); }
.audit-scope .bee-icon { width: 20px; height: 20px; flex: none; color: var(--bee-color-info); }
.audit-scope p { margin: 0; max-width: 95ch; line-height: 1.5; }
.audit-panel { overflow: hidden; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.audit-panel-head { display: flex; align-items: start; justify-content: space-between; flex-wrap: wrap; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.audit-panel-head h2 { margin: 0; font-size: var(--bee-type-section); }
.audit-panel-head p { margin: var(--bee-space-2) 0 0; color: var(--app-text-muted); }
.audit-notice { display: flex; align-items: center; flex-wrap: wrap; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.audit-notice .p-message { flex: 1 1 300px; }
.audit-empty { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-7) var(--bee-space-5); text-align: center; }
.audit-empty .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); }
.audit-empty h3 { margin: 0; font-size: var(--bee-type-section); }
.audit-empty p { margin: 0; color: var(--app-text-muted); }
.audit-table-scroll { overflow-x: auto; }
.audit-table-scroll :deep(.p-datatable) { min-width: 830px; }
.audit-scroll-hint { display: none; align-items: center; gap: var(--bee-space-2); padding: var(--bee-space-3) var(--bee-space-5); margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.audit-scroll-hint .bee-icon { width: 16px; height: 16px; }

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
  background: var(--bee-color-surface-subtle);
  border-radius: var(--bee-radius-control);
  margin-bottom: 1rem;
  border: 1px solid var(--app-border);
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
  font-size: var(--bee-type-ui);
  color: var(--app-text);
}

.audit-diff-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
  border: 1px solid var(--app-border);
}

.audit-diff-table th,
.audit-diff-table td {
  padding: 0.5rem 0.65rem;
  border-bottom: 1px solid var(--app-border);
  text-align: left;
  vertical-align: top;
}

.audit-diff-table th {
  background: var(--bee-color-surface-subtle);
  font-weight: 600;
  color: var(--app-text-muted);
}

.audit-diff-table tr:last-child td {
  border-bottom: none;
}

.audit-diff-table tr.changed td {
  background: var(--bee-color-surface-subtle);
}

.audit-diff-table tr.changed .col-label {
  font-weight: 600;
}

.audit-diff-table tr.changed td:last-child {
  font-weight: 600;
  color: var(--app-text);
}

.audit-diff-table .col-label {
  width: 34%;
  color: var(--app-text);
}

.audit-empty-diff {
  margin: 0;
  font-size: 0.85rem;
  color: var(--app-text-muted);
}
@media (max-width: 900px) { .audit-scroll-hint { display: flex; } }
@media (max-width: 540px) {
  .audit-filter-toggle { display: flex; width: 100%; }
  .audit-filter-row { display: none; margin-top: var(--bee-space-4); }
  .audit-filter-row.is-open { display: flex; }
  .audit-filter-field { flex-basis: 100%; }
  .audit-filter-row > .p-button,.audit-panel-head > .p-button { width: 100%; }
  .audit-meta { grid-template-columns: minmax(0, 1fr); }
  .audit-meta-item.span2 { grid-column: 1; }
  .audit-diff-table,.audit-diff-table tbody,.audit-diff-table tr,.audit-diff-table td { display: block; width: 100%; min-width: 0; }
  .audit-diff-table thead { display: none; }
  .audit-diff-table tr { padding: var(--bee-space-3); border-bottom: 1px solid var(--app-border); }
  .audit-diff-table td { border: 0; padding: var(--bee-space-1) 0; overflow-wrap: anywhere; }
  .audit-diff-table td.col-label { margin-bottom: var(--bee-space-2); }
  .audit-diff-table td[data-label]::before { content: attr(data-label) ': '; display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
}
</style>
