<script setup lang="ts">
import BeePaginator from "@/shared/components/BeePaginator.vue"
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Menu from "primevue/menu"
import type { MenuItem } from "primevue/menuitem"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import { formatRp } from "@/core/format"
import type { Tagihan, TagihanStatus } from "@/types/api"
import { canEditTagihan, canPayTagihan, perluDicocokkan, TAGIHAN_STATUS, tagihanPeriod, tagihanState } from "./presentation"

const props = defineProps<{ rows: Tagihan[]; names: ReadonlyMap<number, string>; loading?: boolean; error?: string }>()
const emit = defineEmits<{ create: []; retry: []; pay: [row: Tagihan]; edit: [row: Tagihan]; remove: [row: Tagihan]; history: [row: Tagihan]; invoice: [row: Tagihan] }>()
const status = ref<TagihanStatus | "reconcile" | null>(null)
const period = ref<string | null>(null)
const first = ref(0)
const active = ref<Tagihan | null>(null)
const menu = ref<InstanceType<typeof Menu> | null>(null)
const menuOpen = ref(false)
const statusOptions = [
  ...Object.entries(TAGIHAN_STATUS).map(([value, state]) => ({ value, label: state.label })),
  { value: "reconcile", label: "Perlu dicocokkan" },
]
function studentName(row: Tagihan) { return row.siswa_nama || props.names.get(row.siswa) || "Nama siswa belum dimuat" }
function periodKey(row: Tagihan) { return `${row.periode_tahun}-${String(row.periode_bulan).padStart(2, "0")}` }
const periodOptions = computed(() => Array.from(new Map(props.rows.map(row => [periodKey(row), { value: periodKey(row), label: tagihanPeriod(row) }])).values()).sort((a, b) => b.value.localeCompare(a.value)))
const { query, filtered: searched } = useTableSearch(() => props.rows, row => [studentName(row), tagihanPeriod(row), tagihanState(row).label, formatRp(row.total)])
const filtered = computed(() => searched.value.filter(row => (!period.value || periodKey(row) === period.value)
  && (!status.value || (status.value === "reconcile" ? perluDicocokkan(row) : !perluDicocokkan(row) && row.status === status.value))))
const hasFilter = computed(() => Boolean(query.value.trim() || period.value || status.value))
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 10))
watch([query, period, status, () => props.rows], () => { first.value = 0 })
function reset() { query.value = ""; period.value = null; status.value = null }
const menuItems = computed<MenuItem[]>(() => {
  const row = active.value
  if (!row) return []
  return [
    { label: "Riwayat pembayaran", icon: "clock", command: () => emit("history", row) },
    { label: "Lihat faktur", icon: "printer", command: () => emit("invoice", row) },
    ...(canEditTagihan(row) ? [
      { separator: true },
      { label: "Ubah tagihan", icon: "pencil-simple", command: () => emit("edit", row) },
      { label: "Batalkan tagihan", icon: "trash", class: "tagihan-action-danger", command: () => emit("remove", row) },
    ] : []),
  ]
})
function openActions(event: Event, row: Tagihan) { active.value = row; menu.value?.toggle(event) }
</script>

<template>
  <section class="tagihan-directory" aria-label="Daftar tagihan siswa" :aria-busy="loading">
    <div class="tagihan-heading"><h2>Daftar tagihan</h2><p>Periksa sisa tagihan sebelum mencatat pembayaran.</p></div>
    <div class="tagihan-toolbar">
      <div class="tagihan-field tagihan-search"><label for="tagihan-search">Cari tagihan</label><SearchField input-id="tagihan-search" v-model="query" placeholder="Nama siswa atau periode" hint="Cari nama siswa, periode, status, atau total tagihan" /></div>
      <div class="tagihan-field"><label for="tagihan-period">Periode tagihan</label><Select input-id="tagihan-period" v-model="period" :options="periodOptions" option-label="label" option-value="value" placeholder="Semua periode" show-clear><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
      <div class="tagihan-field"><label for="tagihan-status">Status pembayaran</label><Select input-id="tagihan-status" v-model="status" :options="statusOptions" option-label="label" option-value="value" placeholder="Semua status" show-clear><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
    </div>
    <div v-if="error" class="tagihan-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang tagihan" severity="secondary" @click="emit('retry')" /></div>
    <div class="tagihan-results"><p role="status">{{ loading ? 'Memuat tagihan…' : error ? 'Tagihan belum tersedia' : `${filtered.length} tagihan${hasFilter ? ' yang cocok' : ''}${filtered.length ? ` · Menampilkan ${first + 1}–${Math.min(first + 10, filtered.length)}` : ''}` }}</p><Button v-if="hasFilter" label="Hapus filter" text @click="reset" /></div>
    <div v-if="loading" class="tagihan-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan daftar tagihan</p></div>
    <div v-else-if="!error && !filtered.length" class="tagihan-empty"><Icon :name="hasFilter ? 'magnifying-glass' : 'file-text'" /><h3>{{ hasFilter ? 'Tidak ada tagihan yang cocok' : 'Belum ada tagihan siswa' }}</h3><p>{{ hasFilter ? 'Ubah kata kunci, periode, atau status pembayaran.' : 'Mulai dengan memilih siswa dan periode tagihannya.' }}</p><Button :label="hasFilter ? 'Hapus filter' : 'Buat tagihan'" severity="secondary" @click="hasFilter ? reset() : emit('create')" /></div>
    <template v-else-if="!error">
      <DataTable class="tagihan-desktop" :value="pageRows" data-key="id" :table-style="{ minWidth: '960px' }" :pt="{ tableContainer: { tabindex: 0, role: 'region', 'aria-label': 'Tabel tagihan siswa' } }">
        <Column header="Siswa dan periode"><template #body="{ data }"><strong class="tagihan-name">{{ studentName(data) }}</strong><small class="tagihan-secondary">{{ tagihanPeriod(data) }}</small></template></Column>
        <Column header="Total tagihan" header-class="bee-numeric" body-class="bee-numeric"><template #body="{ data }">{{ formatRp(data.total) }}</template></Column>
        <Column header="Dibayar" header-class="bee-numeric" body-class="bee-numeric"><template #body="{ data }"><span :class="{ 'tagihan-unknown': data.total_terbayar === null }">{{ data.total_terbayar === null ? 'Belum diketahui' : formatRp(data.total_terbayar) }}</span></template></Column>
        <Column header="Sisa tagihan" header-class="bee-numeric" body-class="bee-numeric"><template #body="{ data }"><strong v-if="data.sisa_tagihan !== null" class="tagihan-amount">{{ formatRp(data.sisa_tagihan) }}</strong><span v-else class="tagihan-unknown">Belum diketahui</span></template></Column>
        <Column header="Status"><template #body="{ data }"><Tag :value="tagihanState(data).label" :severity="tagihanState(data).severity" /></template></Column>
        <Column header="Tindakan" header-class="tagihan-action-column" body-class="tagihan-action-column"><template #body="{ data }"><div class="tagihan-actions"><Button v-if="canPayTagihan(data)" label="Catat pembayaran" severity="secondary" :aria-label="`Catat pembayaran ${studentName(data)} ${tagihanPeriod(data)}`" @click="emit('pay', data)" /><Button :label="canPayTagihan(data) ? undefined : 'Tindakan'" severity="secondary" text title="Tindakan lainnya" :aria-label="`Tindakan tagihan ${studentName(data)} ${tagihanPeriod(data)}`" aria-haspopup="menu" aria-controls="tagihan-action-menu" :aria-expanded="menuOpen && active?.id === data.id" @click="openActions($event, data)"><template #icon><Icon name="caret-down" /></template></Button></div></template></Column>
      </DataTable>
      <ul class="tagihan-mobile" aria-label="Tagihan siswa"><li v-for="row in pageRows" :key="row.id"><div class="tagihan-mobile-heading"><div><strong class="tagihan-name">{{ studentName(row) }}</strong><small class="tagihan-secondary">{{ tagihanPeriod(row) }}</small></div><Tag :value="tagihanState(row).label" :severity="tagihanState(row).severity" /></div><dl><div><dt>Total tagihan</dt><dd>{{ formatRp(row.total) }}</dd></div><div><dt>Dibayar</dt><dd>{{ row.total_terbayar === null ? 'Belum diketahui' : formatRp(row.total_terbayar) }}</dd></div><div><dt>Sisa tagihan</dt><dd class="tagihan-amount">{{ row.sisa_tagihan === null ? 'Belum diketahui' : formatRp(row.sisa_tagihan) }}</dd></div></dl><div class="tagihan-mobile-actions"><Button v-if="canPayTagihan(row)" label="Catat pembayaran" severity="secondary" @click="emit('pay', row)" /><Button label="Tindakan" severity="secondary" text :aria-label="`Tindakan tagihan ${studentName(row)} ${tagihanPeriod(row)}`" aria-haspopup="menu" aria-controls="tagihan-action-menu" :aria-expanded="menuOpen && active?.id === row.id" @click="openActions($event, row)"><template #icon><Icon name="caret-down" /></template></Button></div></li></ul>
      <BeePaginator v-if="filtered.length > 10" v-model:first="first" :rows="10" :total-records="filtered.length" />
    </template>
    <p class="tagihan-footnote"><Icon name="info" /><span>“Perlu dicocokkan” berarti pembayaran lama belum terhubung dengan bukti yang lengkap. Nominal belum diketahui tetap ditandai; periksa riwayat sebelum melanjutkan.</span></p>
    <Menu id="tagihan-action-menu" ref="menu" class="tagihan-action-menu" :model="menuItems" popup @show="menuOpen = true" @hide="menuOpen = false"><template #item="{ item, props: itemProps }"><a v-bind="itemProps.action"><Icon v-if="item.icon" :name="item.icon" /><span>{{ item.label }}</span></a></template></Menu>
  </section>
</template>

<style scoped>
.tagihan-directory { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: clip; }
.tagihan-heading { padding: var(--bee-space-5); }.tagihan-heading h2 { font-size: var(--bee-type-section); font-weight: 600; }.tagihan-heading p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); }
.tagihan-toolbar { display: flex; flex-wrap: wrap; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-5); }.tagihan-field { display: flex; flex-direction: column; gap: var(--bee-space-2); flex: 1 1 180px; min-width: 0; }.tagihan-search { flex: 2 1 260px; }.tagihan-search :deep(.bee-search-field) { flex: none; min-width: 0; }.tagihan-field label { font-weight: 500; font-size: var(--bee-type-caption); }
.tagihan-results { display: flex; justify-content: space-between; align-items: center; gap: var(--bee-space-3); min-height: 52px; padding: 0 var(--bee-space-5); border-top: 1px solid var(--app-border); }.tagihan-results p { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.tagihan-notice { padding: 0 var(--bee-space-5) var(--bee-space-5); display: flex; flex-wrap: wrap; gap: var(--bee-space-3); align-items: center; }
.tagihan-name { font-weight: 500; overflow-wrap: anywhere; }.tagihan-secondary { display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-top: var(--bee-space-1); }.tagihan-amount { font-weight: 500; font-variant-numeric: tabular-nums; }.tagihan-unknown { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
:deep(.p-datatable-tbody > tr > td) { height: var(--bee-size-row-multiline); padding-block: var(--bee-space-3); }:deep(.tagihan-action-column) { min-width: 260px; width: 260px; }.tagihan-actions { display: flex; align-items: center; gap: var(--bee-space-2); }.tagihan-actions > .p-button { min-height: var(--bee-size-control); white-space: nowrap; }
.tagihan-footnote { display: flex; align-items: flex-start; gap: var(--bee-space-2); margin: 0; padding: var(--bee-space-4) var(--bee-space-5); border-top: 1px solid var(--app-border); font-size: var(--bee-type-caption); color: var(--app-text-muted); }.tagihan-footnote .bee-icon { width: 16px; height: 16px; margin-top: 2px; }
.tagihan-empty { padding: var(--bee-space-7) var(--bee-space-5); text-align: center; display: grid; justify-items: center; }.tagihan-empty > .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); margin-bottom: var(--bee-space-3); }.tagihan-empty h3 { font-size: var(--bee-type-section); }.tagihan-empty p { color: var(--app-text-muted); max-width: 50ch; margin: var(--bee-space-2) 0 var(--bee-space-5); }
.tagihan-mobile { display: none; }
@media(max-width:767px) {
  .tagihan-heading { padding: var(--bee-space-4); }.tagihan-toolbar { padding-inline: var(--bee-space-4); gap: var(--bee-space-3); }.tagihan-search { flex-basis: 100%; }.tagihan-field:not(.tagihan-search) { flex-basis: 100%; }.tagihan-results { padding-inline: var(--bee-space-4); }
  .tagihan-desktop { display: none; }.tagihan-mobile { display: block; list-style: none; margin: 0; padding: 0; }.tagihan-mobile li { border-top: 1px solid var(--app-border); padding: var(--bee-space-4); }.tagihan-mobile-heading { display: flex; gap: var(--bee-space-3); align-items: flex-start; justify-content: space-between; }.tagihan-mobile-heading > div { min-width: 0; }.tagihan-mobile-heading .p-tag { flex-shrink: 0; max-width: 46%; }
  .tagihan-mobile dl { display: grid; gap: var(--bee-space-2); margin: var(--bee-space-4) 0; }.tagihan-mobile dl > div { display: flex; justify-content: space-between; gap: var(--bee-space-3); }.tagihan-mobile dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.tagihan-mobile dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }.tagihan-mobile-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-2); }.tagihan-footnote { padding: var(--bee-space-4); }
}
</style>

<style>
.tagihan-action-menu .p-menu-item-link { min-height: var(--bee-size-control); gap: var(--bee-space-3); }
.tagihan-action-menu .tagihan-action-danger .p-menu-item-link { color: var(--bee-color-critical); }
</style>
