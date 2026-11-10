<script setup lang="ts">
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { friendlyError } from "@/core/errors"
import { formatLocalDate, formatRp } from "@/core/format"
import type { ImporBiayaMasukBaris, ImporBiayaMasukHasil } from "@/types/api"
import { siswaApi } from "./api"
import { imporBiayaMasukDetail, tanggalSaldoAwalDefault } from "./presentation"

const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ saved: [result: ImporBiayaMasukHasil] }>()

const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const tanggal = ref<Date | null>(tanggalSaldoAwalDefault())
const preview = ref<ImporBiayaMasukHasil | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref("")

const groups = computed(() => {
  const rows = preview.value?.baris ?? []
  const by = (aksi: ImporBiayaMasukBaris["aksi"]) => rows.filter((r) => r.aksi === aksi)
  return [
    { key: "cek", title: "Perlu dicek, tidak diisi", severity: "warn", rows: by("cek") },
    { key: "galat", title: "Tidak ditemukan di sistem", severity: "danger", rows: by("galat") },
    { key: "isi", title: "Akan diisi", severity: "success", rows: by("isi") },
    { key: "sudah", title: "Saldo awal sudah tercatat", severity: "info", rows: by("sudah") },
  ].filter((group) => group.rows.length)
})
const toSave = computed(() => preview.value?.ringkasan.isi ?? 0)

watch(visible, (open) => {
  if (!open) return
  file.value = null; preview.value = null; error.value = ""; tanggal.value = tanggalSaldoAwalDefault()
  if (fileInput.value) fileInput.value.value = ""
})
async function run(simpan: boolean) {
  if (!file.value || !tanggal.value) return
  error.value = ""
  if (simpan) saving.value = true; else loading.value = true
  try {
    const result = await siswaApi.imporBiayaMasuk(file.value, formatLocalDate(tanggal.value), simpan)
    if (simpan) { emit("saved", result); visible.value = false; return }
    preview.value = result
  } catch (e) {
    const failure = friendlyError(e, simpan ? "Biaya masuk belum berhasil disimpan." : "Berkas belum berhasil dibaca.")
    error.value = [failure.summary, failure.detail].filter(Boolean).join(". ")
  } finally {
    loading.value = false; saving.value = false
  }
}
function pick(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] ?? null
  preview.value = null
  if (file.value) run(false)
}
function changeDate(value: Date | Date[] | (Date | null)[] | null | undefined) {
  tanggal.value = value instanceof Date ? value : null
  preview.value = null
  if (file.value && tanggal.value) run(false)
}
</script>

<template>
  <Dialog v-model:visible="visible" header="Impor biaya masuk dari tab master" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" class="bm-import-dialog" :style="{ width: '760px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup impor biaya masuk' }">
    <template #closeicon><Icon name="x" /></template>
    <div class="bm-body" :aria-busy="loading || saving">
      <section class="bm-step">
        <p class="bm-intro">Untuk pindah pencatatan dari spreadsheet. Unggah tab <strong>master</strong> dari Recap Cash In sebagai CSV. Tiap siswa mendapat isian biaya masuk, diskon, dan satu tagihan biaya masuk. Jumlah cicilan yang sudah dibayar dicatat sebagai <strong>penerimaan saldo awal</strong>, tanpa jurnal, karena uangnya sudah masuk saldo awal kas.</p>
        <div class="bm-inputs">
          <div class="bm-field">
            <label for="impor-bm-tanggal">Tanggal saldo awal</label>
            <DatePicker input-id="impor-bm-tanggal" :model-value="tanggal" date-format="dd/mm/yy" :disabled="loading || saving" aria-describedby="impor-bm-tanggal-help" @update:model-value="changeDate"><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker>
            <small id="impor-bm-tanggal-help">Tanggal terakhir data spreadsheet, biasanya 31/12.</small>
          </div>
          <div class="bm-field">
            <span class="bm-label">Berkas CSV</span>
            <label class="bm-file" for="impor-bm-berkas"><Icon name="file-arrow-up" /><span>{{ file ? file.name : 'Pilih berkas CSV' }}</span></label>
            <input id="impor-bm-berkas" ref="fileInput" class="bm-file-input" type="file" accept=".csv,text/csv" :disabled="loading || saving || !tanggal" @change="pick" />
          </div>
        </div>
      </section>
      <div v-if="error" role="alert"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message></div>
      <p v-if="loading" class="bm-status" role="status"><Icon name="arrows-clockwise" class="bee-spin" /> Membaca berkas…</p>
      <template v-if="preview && !loading">
        <section class="bm-step" aria-labelledby="impor-bm-ringkasan">
          <h3 id="impor-bm-ringkasan">Ringkasan</h3>
          <dl class="bm-summary">
            <div><dt>Akan diisi</dt><dd>{{ preview.ringkasan.isi }}</dd></div>
            <div><dt>Sudah tercatat</dt><dd>{{ preview.ringkasan.sudah }}</dd></div>
            <div :class="{ 'is-warn': preview.ringkasan.cek }"><dt>Perlu dicek</dt><dd>{{ preview.ringkasan.cek }}</dd></div>
            <div :class="{ 'is-critical': preview.ringkasan.galat }"><dt>Tidak ditemukan</dt><dd>{{ preview.ringkasan.galat }}</dd></div>
          </dl>
          <dl class="bm-totals">
            <div><dt>Total ditagihkan</dt><dd>{{ formatRp(preview.ringkasan.total_ditagih) }}</dd></div>
            <div><dt>Saldo awal terbayar</dt><dd>{{ formatRp(preview.ringkasan.total_terbayar) }}</dd></div>
            <div><dt>Sisa tunggakan</dt><dd>{{ formatRp(preview.ringkasan.total_ditagih - preview.ringkasan.total_terbayar) }}</dd></div>
          </dl>
          <p class="bm-hint">{{ preview.ringkasan.lewati ? `${preview.ringkasan.lewati} siswa tanpa biaya masuk dilewati. ` : '' }}Siswa "Perlu dicek" tidak diubah; isi lewat form siswa lalu catat penerimaannya. Cocokkan total terbayar dengan spreadsheet sebelum menyimpan.</p>
        </section>
        <section v-for="group in groups" :key="group.key" class="bm-step" :aria-labelledby="`impor-bm-${group.key}`">
          <h3 :id="`impor-bm-${group.key}`">{{ group.title }} <Tag :value="String(group.rows.length)" :severity="group.severity" /></h3>
          <ul class="bm-rows">
            <li v-for="row in group.rows" :key="row.baris">
              <div class="bm-row-head"><strong>{{ row.nama }}</strong><span>{{ row.kelas || 'Kelas kosong' }} · baris {{ row.baris }}</span></div>
              <p :class="{ 'bm-error': row.aksi === 'galat' }">{{ imporBiayaMasukDetail(row) }}</p>
            </li>
          </ul>
        </section>
      </template>
    </div>
    <template #footer>
      <span v-if="saving" class="bm-saving" role="status">Menyimpan…</span>
      <Button label="Batal" severity="secondary" :disabled="saving" @click="visible = false" />
      <Button :label="toSave ? `Simpan ${toSave} siswa` : 'Tidak ada yang diisi'" :disabled="!preview || loading || !toSave" :loading="saving" @click="run(true)"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
    </template>
  </Dialog>
</template>

<style scoped>
.bm-body { display: grid; gap: var(--bee-space-5); }
.bm-step { display: grid; gap: var(--bee-space-3); min-width: 0; }
.bm-step + .bm-step { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-5); }
.bm-step h3 { margin: 0; font-size: var(--bee-type-body); font-weight: 600; display: flex; align-items: center; gap: var(--bee-space-2); }
.bm-intro { margin: 0; color: var(--app-text-muted); max-width: 64ch; }
.bm-hint { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.5; max-width: 64ch; }
.bm-inputs { display: flex; flex-wrap: wrap; gap: var(--bee-space-4); align-items: flex-start; }
.bm-field { display: grid; gap: var(--bee-space-2); min-width: 0; }
.bm-field label, .bm-label { font-weight: 500; }
.bm-field small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.bm-file { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 44px; padding: 0 var(--bee-space-4); border: 1px dashed var(--app-border-strong, var(--app-border)); border-radius: var(--bee-radius-control); cursor: pointer; justify-self: start; max-width: 100%; overflow-wrap: anywhere; font-weight: 400; }
.bm-file:hover { border-color: var(--bee-color-brand); color: var(--bee-color-brand); }
.bm-file-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.bm-file:has(+ .bm-file-input:focus-visible) { outline: 2px solid var(--bee-color-brand); outline-offset: 2px; }
.bm-status { margin: 0; display: flex; align-items: center; gap: var(--bee-space-2); color: var(--app-text-muted); }
.bm-summary, .bm-totals { margin: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--bee-space-3); }
.bm-totals { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.bm-summary div, .bm-totals div { padding: var(--bee-space-3); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); min-width: 0; }
.bm-summary dt, .bm-totals dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.bm-summary dd { margin: 0; font-size: var(--bee-type-section); font-weight: 600; font-variant-numeric: tabular-nums; }
.bm-totals dd { margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.bm-summary .is-warn dd { color: var(--bee-color-warning-text, var(--app-text)); }
.bm-summary .is-critical dd { color: var(--bee-color-critical); }
.bm-rows { list-style: none; margin: 0; padding: 0; display: grid; }
.bm-rows > li { padding: var(--bee-space-3) 0; border-bottom: 1px solid var(--app-border); display: grid; gap: var(--bee-space-1); min-width: 0; }
.bm-row-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: var(--bee-space-1) var(--bee-space-3); }
.bm-row-head span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.bm-rows p { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.bm-rows p.bm-error { color: var(--bee-color-critical); }
.bm-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media (max-width: 560px) { .bm-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } .bm-totals { grid-template-columns: minmax(0, 1fr); } }
</style>
