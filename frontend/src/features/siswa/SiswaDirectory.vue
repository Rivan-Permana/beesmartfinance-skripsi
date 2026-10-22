<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import Paginator from "primevue/paginator"
import Select from "primevue/select"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import { formatRp } from "@/core/format"
import type { Kelompok, Siswa, SiswaStatus } from "@/types/api"
import { kelompokLabel, SISWA_STATUS, statusOptions } from "./presentation"

const props = defineProps<{
  rows: Siswa[]
  kelompok: Kelompok[]
  loading?: boolean
  error?: string
  groupError?: boolean
}>()
const emit = defineEmits<{ create: []; edit: [row: Siswa]; remove: [row: Siswa]; retry: []; manageGroups: [] }>()
const status = ref<SiswaStatus | null>(null)
const group = ref<number | "unassigned" | null>(null)
const first = ref(0)
const groupMap = computed(() => new Map(props.kelompok.map((item) => [item.id, kelompokLabel(item)])))
const groupOptions = computed(() => [
  { label: "Belum dikelompokkan", value: "unassigned" },
  ...props.kelompok.map((item) => ({ label: kelompokLabel(item), value: item.id })),
])
function groupName(row: Siswa) {
  return row.kelompok == null ? "Belum dikelompokkan" : groupMap.value.get(row.kelompok) ?? "Nama kelompok belum dimuat"
}
const { query, filtered: searched } = useTableSearch(() => props.rows, (row) => [
  row.nis, row.nama, SISWA_STATUS[row.status].label, groupName(row), formatRp(row.spp_nominal),
])
const filtered = computed(() => searched.value.filter((row) =>
  (!status.value || row.status === status.value)
  && (group.value === null || (group.value === "unassigned" ? row.kelompok == null : row.kelompok === group.value)),
))
const hasFilter = computed(() => Boolean(query.value.trim() || status.value || group.value !== null))
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 10))
watch([query, status, group, () => props.rows], () => { first.value = 0 })
function reset() { query.value = ""; status.value = null; group.value = null }
</script>

<template>
  <section class="siswa-directory" aria-label="Direktori siswa" :aria-busy="loading">
    <div class="directory-heading">
      <div><h2>Daftar siswa <span v-if="!loading && !error">{{ rows.length }}</span></h2><p>Profil, kelompok belajar, dan SPP bulanan.</p></div>
      <Button label="Kelola kelompok" severity="secondary" text @click="emit('manageGroups')"><template #icon><Icon name="squares-four" /></template></Button>
    </div>
    <div class="directory-toolbar">
      <div class="directory-field directory-search"><label for="siswa-search">Cari siswa</label><SearchField input-id="siswa-search" v-model="query" placeholder="Nama, NIS, atau kelompok" hint="Cari nama, NIS, kelompok, status, atau nominal SPP" /></div>
      <div class="directory-field"><label for="siswa-group-filter">Kelompok</label><Select :key="(groupError) ? 'locked' : 'editable'" input-id="siswa-group-filter" v-model="group" :options="groupOptions" option-label="label" option-value="value" placeholder="Semua" show-clear filter :disabled="groupError" empty-filter-message="Kelompok tidak ditemukan"><template #filtericon><Icon name="magnifying-glass" /></template><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
      <div class="directory-field"><label for="siswa-status-filter">Status siswa</label><Select input-id="siswa-status-filter" v-model="status" :options="statusOptions" option-label="label" option-value="value" placeholder="Semua" show-clear><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
    </div>
    <div v-if="error" class="directory-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang" severity="secondary" @click="emit('retry')" /></div>
    <div v-else-if="groupError" class="directory-notice"><Message severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>Daftar kelompok belum berhasil dimuat. Data siswa tetap tersedia.</Message><Button label="Muat ulang kelompok" severity="secondary" @click="emit('retry')" /></div>
    <div class="directory-results">
      <p role="status">{{ loading ? 'Memuat data siswa…' : error ? 'Data belum tersedia' : filtered.length ? `Menampilkan ${first + 1}–${Math.min(first + 10, filtered.length)} dari ${filtered.length} siswa${hasFilter ? ' yang cocok' : ''}` : 'Tidak ada siswa ditampilkan' }}</p>
      <Button v-if="hasFilter" label="Hapus filter" text @click="reset"><template #icon><Icon name="x" /></template></Button>
    </div>
    <div v-if="loading" class="directory-loading" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><span>Menyiapkan daftar siswa</span></div>
    <div v-else-if="!error && !filtered.length" class="directory-empty">
      <Icon :name="hasFilter ? 'magnifying-glass' : 'student'" />
      <h3>{{ hasFilter ? 'Tidak ada siswa yang cocok' : 'Mulai dari data siswa' }}</h3>
      <p>{{ hasFilter ? 'Coba kata kunci lain atau hapus filter yang dipilih.' : 'Tambahkan siswa untuk mulai mengelola profil, kelompok, dan administrasinya.' }}</p>
      <Button :label="hasFilter ? 'Hapus filter' : 'Tambah siswa'" severity="secondary" @click="hasFilter ? reset() : emit('create')" />
    </div>
    <template v-else-if="!error">
      <DataTable class="directory-desktop" :value="pageRows" data-key="id" :table-style="{ minWidth: '720px' }" :pt="{ tableContainer: { tabindex: 0, role: 'region', 'aria-label': 'Tabel data siswa' } }">
        <Column header="Siswa"><template #body="{ data }"><button class="directory-name" :aria-label="`Ubah data ${data.nama}`" @click="emit('edit', data)">{{ data.nama }}</button><small class="directory-secondary">{{ data.nis ? `NIS ${data.nis}` : 'NIS belum diisi' }}</small></template></Column>
        <Column header="Kelompok"><template #body="{ data }"><span :class="{ 'directory-muted': data.kelompok == null }">{{ groupName(data) }}</span></template></Column>
        <Column header="Status"><template #body="{ data }"><Tag :value="SISWA_STATUS[data.status as SiswaStatus].label" :severity="SISWA_STATUS[data.status as SiswaStatus].severity" /></template></Column>
        <Column header="SPP per bulan" header-class="bee-numeric" body-class="bee-numeric"><template #body="{ data }">{{ formatRp(data.spp_nominal) }}</template></Column>
        <Column header="Tindakan" header-class="directory-actions-column" body-class="directory-actions-column"><template #body="{ data }"><div class="bee-actions"><Button severity="secondary" text :aria-label="`Ubah ${data.nama}`" @click="emit('edit', data)"><template #icon><Icon name="pencil-simple" /></template></Button><Button severity="secondary" text :aria-label="`Hapus ${data.nama}`" @click="emit('remove', data)"><template #icon><Icon name="trash" /></template></Button></div></template></Column>
      </DataTable>
      <ul class="directory-mobile" aria-label="Data siswa">
        <li v-for="row in pageRows" :key="row.id">
          <div class="mobile-record-heading"><div><button class="directory-name" :aria-label="`Ubah data ${row.nama}`" @click="emit('edit', row)">{{ row.nama }}</button><small class="directory-secondary">{{ row.nis ? `NIS ${row.nis}` : 'NIS belum diisi' }}</small></div><Tag :value="SISWA_STATUS[row.status].label" :severity="SISWA_STATUS[row.status].severity" /></div>
          <dl><div><dt>Kelompok</dt><dd>{{ groupName(row) }}</dd></div><div><dt>SPP per bulan</dt><dd class="tabular-nums">{{ formatRp(row.spp_nominal) }}</dd></div></dl>
          <div class="mobile-record-actions"><Button label="Ubah data" severity="secondary" text :aria-label="`Ubah ${row.nama}`" @click="emit('edit', row)"><template #icon><Icon name="pencil-simple" /></template></Button><Button severity="secondary" text :aria-label="`Hapus ${row.nama}`" @click="emit('remove', row)"><template #icon><Icon name="trash" /></template></Button></div>
        </li>
      </ul>
      <Paginator v-if="filtered.length > 10" v-model:first="first" :rows="10" :total-records="filtered.length" :page-link-size="3" template="PrevPageLink PageLinks NextPageLink"><template #prevpagelinkicon><Icon name="caret-left" /></template><template #nextpagelinkicon><Icon name="caret-right" /></template></Paginator>
    </template>
    <div class="directory-footnote"><Icon name="info" /><span>SPP di sini adalah tarif bulanan siswa. Status pembayaran tersedia pada menu Tagihan.</span></div>
  </section>
</template>

<style scoped>
.siswa-directory { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: clip; }
.directory-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.directory-heading h2 { font-size: var(--bee-type-section); font-weight: 600; line-height: 1.3; display: flex; align-items: center; gap: var(--bee-space-3); }
.directory-heading h2 span { font-size: var(--bee-type-ui); font-weight: 500; color: var(--bee-color-muted); background: var(--bee-color-neutral-tint); padding: 2px 8px; border-radius: var(--bee-radius-status); }
.directory-heading p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); }
.directory-toolbar { display: flex; flex-wrap: wrap; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-4); }
.directory-field { display: flex; flex-direction: column; gap: var(--bee-space-2); flex: 1 1 160px; min-width: 0; }
.directory-field label { font-weight: 500; font-size: var(--bee-type-caption); }
.directory-search { flex: 2 1 260px; }.directory-search :deep(.bee-search-field) { flex: none; min-width: 0; }
.directory-results { min-height: 52px; display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-2); padding: 0 var(--bee-space-5); border-top: 1px solid var(--app-border); }
.directory-results p { font-size: var(--bee-type-caption); color: var(--app-text-muted); margin: var(--bee-space-3) 0; }
.directory-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-4); }.directory-notice .p-message { flex: 1 1 300px; }
.directory-name { border: 0; padding: 0; background: transparent; color: var(--app-text); cursor: pointer; font: inherit; font-weight: 500; text-align: left; overflow-wrap: anywhere; }
.directory-name:hover { color: var(--bee-color-brand); text-decoration: underline; text-underline-offset: 3px; }
.directory-secondary { display: block; font-size: var(--bee-type-caption); color: var(--app-text-muted); margin-top: var(--bee-space-1); }.directory-muted { color: var(--app-text-muted); }
:deep(.directory-actions-column) { width: 144px; min-width: 144px; text-align: end; }
:deep(th.directory-actions-column .p-datatable-column-header-content) { justify-content: flex-end; }
/* Pull the last icon button in so its glyph lines up with the header text. */
:deep(td.directory-actions-column .bee-actions .p-button:last-child) { margin-inline-end: calc(var(--bee-space-3) * -1); }
:deep(.p-datatable-tbody > tr > td) { height: var(--bee-size-row-multiline); padding-block: var(--bee-space-3); }
.directory-footnote { display: flex; align-items: flex-start; gap: var(--bee-space-2); padding: var(--bee-space-4) var(--bee-space-5); border-top: 1px solid var(--app-border); color: var(--app-text-muted); font-size: var(--bee-type-caption); }.directory-footnote .bee-icon { width: 16px; height: 16px; margin-top: 2px; }
.directory-empty { display: grid; justify-items: center; text-align: center; padding: var(--bee-space-7) var(--bee-space-5); }.directory-empty > .bee-icon { width: 32px; height: 32px; color: var(--bee-color-muted); margin-bottom: var(--bee-space-4); }.directory-empty h3 { font-size: var(--bee-type-section); font-weight: 500; }.directory-empty p { max-width: 45ch; color: var(--app-text-muted); margin: var(--bee-space-2) 0 var(--bee-space-5); }
.directory-loading { display: flex; gap: var(--bee-space-3); align-items: center; justify-content: center; min-height: 240px; color: var(--app-text-muted); }
.directory-mobile { display: none; }
@media (max-width: 767px) {
  .directory-heading { padding: var(--bee-space-4); align-items: flex-start; flex-direction: column; gap: var(--bee-space-2); }.directory-heading > .p-button { padding-inline: 0; }
  .directory-toolbar { padding-inline: var(--bee-space-4); gap: var(--bee-space-3); }.directory-search { flex-basis: 100%; }.directory-field:not(.directory-search) { flex-basis: calc(50% - 6px); }
  .directory-results { padding-inline: var(--bee-space-4); }.directory-results .p-button { padding-inline: var(--bee-space-2); font-size: var(--bee-type-caption); }
  .directory-desktop { display: none; }.directory-mobile { display: block; list-style: none; margin: 0; padding: 0; }.directory-mobile li { padding: var(--bee-space-4); border-top: 1px solid var(--app-border); }
  .mobile-record-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--bee-space-3); }.mobile-record-heading > div { min-width: 0; }.mobile-record-heading .p-tag { flex-shrink: 0; }
  .directory-mobile dl { margin: var(--bee-space-4) 0 var(--bee-space-2); display: grid; gap: var(--bee-space-2); }.directory-mobile dl > div { display: flex; align-items: baseline; justify-content: space-between; gap: var(--bee-space-3); }.directory-mobile dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); flex-shrink: 0; }.directory-mobile dd { margin: 0; text-align: right; overflow-wrap: anywhere; }
  .mobile-record-actions { display: flex; justify-content: space-between; }.mobile-record-actions > .p-button:first-child { padding-left: 0; }
  .directory-footnote { padding: var(--bee-space-4); }
}
</style>
