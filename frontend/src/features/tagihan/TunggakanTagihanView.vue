<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import Button from "primevue/button"
import Message from "primevue/message"
import Paginator from "primevue/paginator"
import Select from "primevue/select"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"

import { friendlyError } from "@/core/errors"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Tagihan } from "@/types/api"
import { tagihanApi } from "./api"
import { perluDicocokkan, tagihanPeriod, tagihanState } from "./presentation"

const rows = ref<Tagihan[]>([])
const loading = ref(false)
const error = ref("")
const usePeriod = ref(false)
const month = ref(new Date().getMonth() + 1)
const year = ref(new Date().getFullYear())
const status = ref<"all" | "known" | "review">("all")
const first = ref(0)

function cents(value: string | null): bigint | null {
  const parts = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(value || "")
  if (!parts) return null
  const amount = BigInt(parts[2]!) * 100n + BigInt((parts[3] || "").padEnd(2, "0"))
  return parts[1] ? -amount : amount
}
function rupiah(value: bigint) {
  const positive = value < 0n ? -value : value
  const fraction = positive % 100n
  return "Rp " + (value < 0n ? "-" : "") + (positive / 100n).toLocaleString("id-ID")
    + (fraction ? "," + fraction.toString().padStart(2, "0") : "")
}
function reviewNeeded(row: Tagihan) {
  return perluDicocokkan(row) || cents(row.sisa_tagihan) === null
}
function studentName(row: Tagihan) { return row.siswa_nama || "Siswa #" + row.siswa }
function balance(row: Tagihan) {
  return reviewNeeded(row) ? "Belum diketahui" : rupiah(cents(row.sisa_tagihan)!)
}
function statusLabel(row: Tagihan) {
  return reviewNeeded(row) ? "Perlu dicocokkan" : tagihanState(row).label
}

const outstanding = computed(() => rows.value.filter((row) =>
  reviewNeeded(row) || (cents(row.sisa_tagihan) ?? 0n) > 0n,
))
const { query, filtered: searched } = useTableSearch(outstanding, (row) => [
  studentName(row), tagihanPeriod(row), statusLabel(row),
])
const filtered = computed(() => searched.value.filter((row) =>
  (!usePeriod.value || row.periode_bulan === month.value && row.periode_tahun === year.value)
  && (status.value === "all" || (status.value === "review" ? reviewNeeded(row) : !reviewNeeded(row))),
))
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 10))
const known = computed(() => filtered.value.filter((row) => !reviewNeeded(row)))
const reviewCount = computed(() => filtered.value.length - known.value.length)
const knownTotal = computed(() => known.value.reduce((sum, row) => sum + cents(row.sisa_tagihan)!, 0n))
const hasFilter = computed(() => !!query.value.trim() || usePeriod.value || status.value !== "all")
watch([query, usePeriod, month, year, status, rows], () => { first.value = 0 })

function clearFilters() {
  query.value = ""
  usePeriod.value = false
  status.value = "all"
}
async function load() {
  if (loading.value) return
  loading.value = true
  error.value = ""
  try { rows.value = await tagihanApi.listAll() }
  catch (cause) {
    rows.value = []
    const message = friendlyError(cause, "Daftar tunggakan belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <PageLayout title="Tunggakan tagihan" subtitle="Pantau sisa tagihan siswa dan data pembayaran yang masih perlu dicocokkan." :surface="false">
    <p class="outstanding-scope">{{ hasFilter ? "Ringkasan sesuai filter yang aktif." : "Ringkasan seluruh tagihan yang perlu ditinjau." }}</p>
    <section class="outstanding-summary" aria-label="Ringkasan tunggakan">
      <div class="outstanding-total"><span>Sisa yang diketahui</span><strong>{{ loading || error || !known.length ? "—" : rupiah(knownTotal) }}</strong><small>{{ loading || error ? "Data belum tersedia" : known.length + " tagihan dengan sisa diketahui" }}</small></div>
      <div class="outstanding-review"><span>Perlu dicocokkan</span><strong>{{ loading || error ? "—" : reviewCount }}</strong><small>Tagihan dengan sisa belum diketahui</small></div>
    </section>
    <p v-if="!loading && !error && reviewCount" class="outstanding-caveat"><Icon name="info" />Jumlah ini belum mencakup {{ reviewCount }} tagihan yang perlu dicocokkan.</p>

    <section class="outstanding-panel" aria-label="Daftar tunggakan tagihan" :aria-busy="loading">
      <header class="outstanding-heading"><div><h2>Daftar tagihan yang perlu ditinjau</h2><p>Tagihan dengan sisa positif atau pembayaran lama yang belum lengkap.</p></div><Button label="Muat ulang" severity="secondary" :disabled="loading" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></header>
      <div class="outstanding-toolbar">
        <div class="outstanding-field outstanding-search"><label for="outstanding-search">Cari tagihan</label><SearchField input-id="outstanding-search" v-model="query" placeholder="Nama siswa atau periode" hint="Mencari seluruh tagihan yang dimuat" /></div>
        <div class="outstanding-field"><label for="outstanding-status">Jenis perhatian</label><Select input-id="outstanding-status" v-model="status" :options="[{ value: 'all', label: 'Semua' }, { value: 'known', label: 'Sisa diketahui' }, { value: 'review', label: 'Perlu dicocokkan' }]" option-label="label" option-value="value" :disabled="loading || !!error"><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
      </div>
      <div class="outstanding-period"><label for="outstanding-period-toggle"><ToggleSwitch input-id="outstanding-period-toggle" v-model="usePeriod" :disabled="loading || !!error" />Periode tertentu</label><PeriodPicker v-if="usePeriod" v-model:bulan="month" v-model:tahun="year" /></div>
      <div v-if="error" class="outstanding-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang tagihan" severity="secondary" @click="load" /></div>
      <div class="outstanding-results"><p role="status">{{ loading ? "Memuat tagihan…" : error ? "Daftar belum tersedia" : filtered.length ? (first + 1) + "–" + Math.min(first + 10, filtered.length) + " dari " + filtered.length + " tagihan" : "Tidak ada tagihan ditampilkan" }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" text @click="clearFilters" /></div>
      <div v-if="loading" class="outstanding-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan daftar tagihan</p></div>
      <div v-else-if="!error && !filtered.length" class="outstanding-empty"><Icon :name="hasFilter ? 'magnifying-glass' : 'check-circle'" /><h3>{{ hasFilter ? "Tidak ada tagihan yang cocok" : "Tidak ada tunggakan tercatat" }}</h3><p>{{ hasFilter ? "Ubah pencarian, periode, atau jenis perhatian." : "Semua tagihan yang dimuat tidak memiliki sisa positif dan tidak menunggu pencocokan." }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" @click="clearFilters" /></div>
      <template v-else-if="!error">
        <table class="outstanding-table"><caption class="outstanding-sr-only">Tagihan dengan sisa positif atau perlu dicocokkan</caption><thead><tr><th>Siswa</th><th>Periode</th><th class="outstanding-number">Sisa tagihan</th><th>Status</th></tr></thead><tbody><tr v-for="row in pageRows" :key="row.id"><td><strong>{{ studentName(row) }}</strong></td><td>{{ tagihanPeriod(row) }}</td><td class="outstanding-number" :class="{ 'outstanding-unknown': reviewNeeded(row) }">{{ balance(row) }}</td><td><Tag :value="statusLabel(row)" :severity="reviewNeeded(row) ? 'warn' : tagihanState(row).severity" /></td></tr></tbody></table>
        <ul class="outstanding-cards" aria-label="Tagihan yang perlu ditinjau"><li v-for="row in pageRows" :key="row.id"><header><div><strong>{{ studentName(row) }}</strong><small>{{ tagihanPeriod(row) }}</small></div><Tag :value="statusLabel(row)" :severity="reviewNeeded(row) ? 'warn' : tagihanState(row).severity" /></header><dl><div><dt>Sisa tagihan</dt><dd :class="{ 'outstanding-unknown': reviewNeeded(row) }">{{ balance(row) }}</dd></div></dl></li></ul>
        <Paginator v-if="filtered.length > 10" v-model:first="first" :rows="10" :total-records="filtered.length" template="PrevPageLink PageLinks NextPageLink"><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></Paginator>
      </template>
      <p class="outstanding-footnote"><Icon name="info" />Halaman ini untuk memantau. Admin TU mencatat pembayaran dan memeriksa riwayat pada menu Tagihan.</p>
    </section>
  </PageLayout>
</template>

<style scoped>
.outstanding-scope { margin: 0 0 var(--bee-space-2); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.outstanding-summary { display: flex; flex-wrap: wrap; margin-bottom: var(--bee-space-4); background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.outstanding-summary > div { display: grid; align-content: center; gap: var(--bee-space-1); min-width: 220px; flex: 1; padding: var(--bee-space-5); }
.outstanding-summary > div + div { border-inline-start: 1px solid var(--app-border); }
.outstanding-summary span,.outstanding-summary small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.outstanding-summary strong { font-size: var(--bee-type-section); font-weight: 600; font-variant-numeric: tabular-nums; }
.outstanding-caveat { display: flex; align-items: start; gap: var(--bee-space-2); margin: 0 0 var(--bee-space-4); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.outstanding-caveat .bee-icon,.outstanding-footnote .bee-icon { width: 16px; height: 16px; flex: none; margin-top: 2px; }
.outstanding-panel { min-width: 0; overflow: hidden; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.outstanding-heading { display: flex; align-items: start; justify-content: space-between; flex-wrap: wrap; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.outstanding-heading h2 { margin: 0; font-size: var(--bee-type-section); font-weight: 600; }
.outstanding-heading p { margin: var(--bee-space-2) 0 0; color: var(--app-text-muted); }
.outstanding-toolbar { display: flex; flex-wrap: wrap; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-4); }
.outstanding-field { display: grid; gap: var(--bee-space-2); flex: 1 1 180px; min-width: 0; }
.outstanding-search { flex: 2 1 260px; }.outstanding-search .bee-search-field { min-width: 0; flex: none; }
.outstanding-field label { font-size: var(--bee-type-caption); font-weight: 500; }
.outstanding-period { display: flex; align-items: center; flex-wrap: wrap; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.outstanding-period > label { display: inline-flex; align-items: center; gap: var(--bee-space-2); font-size: var(--bee-type-caption); font-weight: 500; cursor: pointer; }
.outstanding-notice { display: flex; align-items: center; flex-wrap: wrap; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-4); }.outstanding-notice .p-message { flex: 1 1 300px; }
.outstanding-results { display: flex; justify-content: space-between; align-items: center; gap: var(--bee-space-3); min-height: 52px; padding: 0 var(--bee-space-5); border-top: 1px solid var(--app-border); }
.outstanding-results p { margin: 0; font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.outstanding-table { width: 100%; border-collapse: collapse; font-size: var(--bee-type-ui); }
.outstanding-table th { background: var(--bee-color-surface-subtle); color: var(--app-text-muted); font-size: var(--bee-type-caption); font-weight: 500; text-align: start; }
.outstanding-table th,.outstanding-table td { padding: var(--bee-space-4) var(--bee-space-5); border-bottom: 1px solid var(--app-border); }
.outstanding-table strong { font-weight: 500; }.outstanding-table .outstanding-number { text-align: end; font-variant-numeric: tabular-nums; white-space: nowrap; }
.outstanding-unknown { color: var(--app-text-muted); }
.outstanding-cards { display: none; list-style: none; padding: 0; margin: 0; }
.outstanding-footnote { display: flex; gap: var(--bee-space-2); align-items: start; margin: 0; padding: var(--bee-space-4) var(--bee-space-5); color: var(--app-text-muted); font-size: var(--bee-type-caption); border-top: 1px solid var(--app-border); }
.outstanding-empty { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-7) var(--bee-space-5); text-align: center; }
.outstanding-empty > .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); }.outstanding-empty h3,.outstanding-empty p { margin: 0; }.outstanding-empty h3 { font-size: var(--bee-type-section); font-weight: 500; }.outstanding-empty p { max-width: 45ch; color: var(--app-text-muted); }
.outstanding-sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
@media (max-width: 767px) {
  .outstanding-table { display: none; }.outstanding-cards { display: block; }
  .outstanding-cards li { padding: var(--bee-space-4); border-bottom: 1px solid var(--app-border); }
  .outstanding-cards header { display: flex; align-items: start; justify-content: space-between; gap: var(--bee-space-3); }
  .outstanding-cards header > div { min-width: 0; }.outstanding-cards header strong { font-weight: 500; overflow-wrap: anywhere; }.outstanding-cards header small { display: block; margin-top: var(--bee-space-1); color: var(--app-text-muted); }
  .outstanding-cards header .p-tag { flex-shrink: 0; max-width: 48%; }.outstanding-cards dl { margin: var(--bee-space-4) 0 0; }.outstanding-cards dl > div { display: flex; justify-content: space-between; gap: var(--bee-space-3); }.outstanding-cards dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.outstanding-cards dd { margin: 0; text-align: end; font-variant-numeric: tabular-nums; }
}
@media (max-width: 540px) {
  .outstanding-summary > div { flex-basis: 100%; padding: var(--bee-space-4); }.outstanding-summary > div + div { border-inline-start: 0; border-top: 1px solid var(--app-border); }
  .outstanding-heading { padding: var(--bee-space-4); }.outstanding-heading > .p-button { width: 100%; }
  .outstanding-toolbar,.outstanding-period { padding-inline: var(--bee-space-4); }.outstanding-field { flex-basis: 100%; }
  .outstanding-results,.outstanding-footnote { padding-inline: var(--bee-space-4); }
}
</style>
