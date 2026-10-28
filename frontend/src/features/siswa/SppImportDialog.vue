<script setup lang="ts">
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { friendlyError } from "@/core/errors"
import { formatRp } from "@/core/format"
import type { ImporSppBaris, ImporSppHasil } from "@/types/api"
import { siswaApi } from "./api"

const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ saved: [result: ImporSppHasil] }>()

const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const preview = ref<ImporSppHasil | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref("")

const groups = computed(() => {
  const rows = preview.value?.baris ?? []
  return [
    { key: "cek", title: "Perlu dicek, tidak diisi", severity: "warn", rows: rows.filter((r) => r.aksi === "cek") },
    { key: "galat", title: "Tidak ditemukan di sistem", severity: "danger", rows: rows.filter((r) => r.aksi === "galat") },
    { key: "isi", title: "SPP yang akan diisi", severity: "success", rows: rows.filter((r) => r.aksi === "isi") },
    { key: "beda", title: "SPP sistem berbeda, tidak diubah", severity: "info", rows: rows.filter((r) => r.aksi === "beda") },
  ].filter((group) => group.rows.length)
})
const toSave = computed(() => preview.value?.ringkasan.isi ?? 0)

watch(visible, (open) => {
  if (!open) return
  file.value = null; preview.value = null; error.value = ""
  if (fileInput.value) fileInput.value.value = ""
})
async function run(simpan: boolean) {
  if (!file.value) return
  error.value = ""
  if (simpan) saving.value = true; else loading.value = true
  try {
    const result = await siswaApi.imporSpp(file.value, simpan)
    if (simpan) { emit("saved", result); visible.value = false; return }
    preview.value = result
  } catch (e) {
    const failure = friendlyError(e, simpan ? "SPP belum berhasil disimpan." : "Berkas belum berhasil dibaca.")
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
function detail(row: ImporSppBaris) {
  if (row.aksi === "isi") return `${formatRp(row.spp_baru)} per bulan`
  if (row.aksi === "beda") return `Sistem ${formatRp(row.spp_lama)} · berkas ${formatRp(row.spp_baru)}`
  const nilai = row.nilai.length ? ` Nominal di berkas: ${row.nilai.map(formatRp).join(", ")}.` : ""
  return `${row.alasan ?? ""}${nilai}`
}
</script>

<template>
  <Dialog v-model:visible="visible" header="Impor SPP dari tab master" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" class="spp-import-dialog" :style="{ width: '720px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup impor SPP' }">
    <template #closeicon><Icon name="x" /></template>
    <div class="spp-body" :aria-busy="loading || saving">
      <section class="spp-step">
        <p class="spp-intro">Unggah tab <strong>master</strong> dari Recap Cash In (File → Download → Comma-separated values (.csv)). SPP diambil dari nominal SPP yang paling sering dibayar tiap siswa. Hanya siswa yang SPP-nya masih Rp 0 yang diisi; tagihan, biodata, dan biaya masuk tidak berubah.</p>
        <label class="spp-file" for="impor-spp-berkas"><Icon name="file-arrow-up" /><span>{{ file ? file.name : 'Pilih berkas CSV' }}</span></label>
        <input id="impor-spp-berkas" ref="fileInput" class="spp-file-input" type="file" accept=".csv,text/csv" :disabled="loading || saving" @change="pick" />
      </section>
      <div v-if="error" role="alert"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message></div>
      <p v-if="loading" class="spp-status" role="status"><Icon name="arrows-clockwise" class="bee-spin" /> Membaca berkas…</p>
      <template v-if="preview && !loading">
        <section class="spp-step" aria-labelledby="impor-spp-ringkasan">
          <h3 id="impor-spp-ringkasan">Ringkasan</h3>
          <dl class="spp-summary">
            <div><dt>Akan diisi</dt><dd>{{ preview.ringkasan.isi }}</dd></div>
            <div><dt>Sudah sama</dt><dd>{{ preview.ringkasan.sama }}</dd></div>
            <div><dt>Berbeda</dt><dd>{{ preview.ringkasan.beda }}</dd></div>
            <div :class="{ 'is-warn': preview.ringkasan.cek }"><dt>Perlu dicek</dt><dd>{{ preview.ringkasan.cek }}</dd></div>
            <div :class="{ 'is-critical': preview.ringkasan.galat }"><dt>Tidak ditemukan</dt><dd>{{ preview.ringkasan.galat }}</dd></div>
          </dl>
          <p class="spp-hint">Siswa "Perlu dicek" dan "Berbeda" tidak diubah. Isi atau perbaiki SPP mereka lewat form siswa.</p>
        </section>
        <section v-for="group in groups" :key="group.key" class="spp-step" :aria-labelledby="`impor-spp-${group.key}`">
          <h3 :id="`impor-spp-${group.key}`">{{ group.title }} <Tag :value="String(group.rows.length)" :severity="group.severity" /></h3>
          <ul class="spp-rows">
            <li v-for="row in group.rows" :key="row.baris">
              <div class="spp-row-head"><strong>{{ row.nama }}</strong><span>{{ row.kelas || 'Kelas kosong' }} · baris {{ row.baris }}</span></div>
              <p :class="{ 'spp-error': row.aksi === 'galat' }">{{ detail(row) }}</p>
            </li>
          </ul>
        </section>
      </template>
    </div>
    <template #footer>
      <span v-if="saving" class="spp-saving" role="status">Menyimpan…</span>
      <Button label="Batal" severity="secondary" :disabled="saving" @click="visible = false" />
      <Button :label="toSave ? `Isi SPP ${toSave} siswa` : 'Tidak ada yang diisi'" :disabled="!preview || loading || !toSave" :loading="saving" @click="run(true)"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
    </template>
  </Dialog>
</template>

<style scoped>
.spp-body { display: grid; gap: var(--bee-space-5); }
.spp-step { display: grid; gap: var(--bee-space-3); min-width: 0; }
.spp-step + .spp-step { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-5); }
.spp-step h3 { margin: 0; font-size: var(--bee-type-body); font-weight: 600; display: flex; align-items: center; gap: var(--bee-space-2); }
.spp-intro { margin: 0; color: var(--app-text-muted); max-width: 64ch; }
.spp-hint { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.5; max-width: 64ch; }
.spp-file { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 44px; padding: 0 var(--bee-space-4); border: 1px dashed var(--app-border-strong, var(--app-border)); border-radius: var(--bee-radius-control); cursor: pointer; justify-self: start; max-width: 100%; overflow-wrap: anywhere; }
.spp-file:hover { border-color: var(--bee-color-brand); color: var(--bee-color-brand); }
.spp-file-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.spp-file:has(+ .spp-file-input:focus-visible) { outline: 2px solid var(--bee-color-brand); outline-offset: 2px; }
.spp-status { margin: 0; display: flex; align-items: center; gap: var(--bee-space-2); color: var(--app-text-muted); }
.spp-summary { margin: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: var(--bee-space-3); }
.spp-summary div { padding: var(--bee-space-3); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); }
.spp-summary dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.spp-summary dd { margin: 0; font-size: var(--bee-type-section); font-weight: 600; font-variant-numeric: tabular-nums; }
.spp-summary .is-warn dd { color: var(--bee-color-warning-text, var(--app-text)); }
.spp-summary .is-critical dd { color: var(--bee-color-critical); }
.spp-rows { list-style: none; margin: 0; padding: 0; display: grid; }
.spp-rows > li { padding: var(--bee-space-3) 0; border-bottom: 1px solid var(--app-border); display: grid; gap: var(--bee-space-1); min-width: 0; }
.spp-row-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: var(--bee-space-1) var(--bee-space-3); }
.spp-row-head span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.spp-rows p { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.spp-rows p.spp-error { color: var(--bee-color-critical); }
.spp-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media (max-width: 560px) { .spp-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
