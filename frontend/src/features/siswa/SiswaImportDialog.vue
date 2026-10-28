<script setup lang="ts">
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { friendlyError } from "@/core/errors"
import type { ImporBiodataBaris, ImporBiodataHasil, JenisKelamin, Kelompok } from "@/types/api"
import { siswaApi } from "./api"
import { JENIS_KELAMIN, kelompokLabel } from "./presentation"

const props = defineProps<{ kelompok: Kelompok[] }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ saved: [result: ImporBiodataHasil] }>()

const FIELD_LABEL: Record<string, string> = {
  nama: "Nama", jenis_kelamin: "Jenis kelamin", tempat_lahir: "Tempat lahir", tanggal_lahir: "Tanggal lahir",
  alamat: "Alamat", nama_ayah: "Nama ayah", kontak_ayah: "HP ayah", nama_ibu: "Nama ibu", kontak_ibu: "HP ibu", kelompok: "Kelompok",
}
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const preview = ref<ImporBiodataHasil | null>(null)
const kelasMap = ref<Record<string, number | null>>({})
const loading = ref(false)
const saving = ref(false)
const error = ref("")

const groupOptions = computed(() => [
  { value: null, label: "Jangan ubah kelompok" },
  ...props.kelompok.map((item) => ({ value: item.id, label: kelompokLabel(item) })),
])
function groupName(id: unknown) {
  const group = props.kelompok.find((item) => item.id === id)
  return group ? kelompokLabel(group) : "Kelompok belum dimuat"
}
function show(field: string, value: unknown) {
  if (value == null || value === "") return "kosong"
  if (field === "kelompok") return groupName(value)
  if (field === "jenis_kelamin") return JENIS_KELAMIN[value as JenisKelamin] ?? String(value)
  if (field === "tanggal_lahir") return String(value).split("-").reverse().join("/")
  return String(value)
}
const groups = computed(() => {
  const rows = preview.value?.baris ?? []
  return [
    { key: "galat", title: "Bermasalah, dilewati", rows: rows.filter((r) => r.aksi === "galat") },
    { key: "baru", title: "Siswa baru", rows: rows.filter((r) => r.aksi === "baru") },
    { key: "ubah", title: "Data yang berubah", rows: rows.filter((r) => r.aksi === "ubah") },
  ].filter((group) => group.rows.length)
})
const toSave = computed(() => (preview.value?.ringkasan.baru ?? 0) + (preview.value?.ringkasan.ubah ?? 0))
const unmappedNew = computed(() => (preview.value?.kelas ?? []).filter((k) => kelasMap.value[k.kelas] == null
  && preview.value!.baris.some((r) => r.kelas === k.kelas && r.aksi === "baru")).map((k) => k.kelas))

watch(visible, (open) => {
  if (!open) return
  file.value = null; preview.value = null; kelasMap.value = {}; error.value = ""
  if (fileInput.value) fileInput.value.value = ""
})
async function run(simpan: boolean) {
  if (!file.value) return
  error.value = ""
  if (simpan) saving.value = true; else loading.value = true
  try {
    const result = await siswaApi.imporBiodata(file.value, preview.value ? kelasMap.value : null, simpan)
    if (simpan) { emit("saved", result); visible.value = false; return }
    preview.value = result
    kelasMap.value = Object.fromEntries(result.kelas.map((k) => [k.kelas, k.kelompok]))
  } catch (e) {
    const failure = friendlyError(e, simpan ? "Impor belum berhasil disimpan." : "Berkas belum berhasil dibaca.")
    error.value = [failure.summary, failure.detail].filter(Boolean).join(". ")
  } finally {
    loading.value = false; saving.value = false
  }
}
function pick(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] ?? null
  preview.value = null; kelasMap.value = {}
  if (file.value) run(false)
}
function setGroup(kelas: string, value: number | null) {
  kelasMap.value = { ...kelasMap.value, [kelas]: value ?? null }
  run(false)
}
function rowNote(row: ImporBiodataBaris) {
  return row.galat ?? (row.aksi === "baru" ? [row.nilai.jenis_kelamin && show("jenis_kelamin", row.nilai.jenis_kelamin), row.nilai.tanggal_lahir && `lahir ${show("tanggal_lahir", row.nilai.tanggal_lahir)}`].filter(Boolean).join(" · ") : "")
}
</script>

<template>
  <Dialog v-model:visible="visible" header="Impor biodata siswa" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" class="siswa-import-dialog" :style="{ width: '760px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup impor biodata' }">
    <template #closeicon><Icon name="x" /></template>
    <div class="import-body" :aria-busy="loading || saving">
      <section class="import-step">
        <p class="import-intro">Unggah tab biodata dari spreadsheet kelas. Di Google Sheets pilih <strong>File → Download → Comma-separated values (.csv)</strong>. Sistem menampilkan pratinjau dulu; belum ada data yang tersimpan sampai Anda menekan Simpan.</p>
        <label class="import-file" for="impor-berkas"><Icon name="file-arrow-up" /><span>{{ file ? file.name : 'Pilih berkas CSV' }}</span></label>
        <input id="impor-berkas" ref="fileInput" class="import-file-input" type="file" accept=".csv,text/csv" :disabled="loading || saving" @change="pick" />
        <p class="import-hint">Kolom yang dibaca: Kelas, Nama Siswa, JK, Tempat, Tanggal Lahir, Alamat, Nama Ayah, Nama Bunda, dan No. Tlp. Usia dihitung otomatis dari tanggal lahir. Alamat, nomor HP, dan tanggal dirapikan otomatis.</p>
      </section>
      <div v-if="error" role="alert"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message></div>
      <p v-if="loading" class="import-status" role="status"><Icon name="arrows-clockwise" class="bee-spin" /> Membaca berkas…</p>
      <template v-if="preview && !loading">
        <section class="import-step" aria-labelledby="impor-kelas-title">
          <h3 id="impor-kelas-title">Pasangkan kelas ke kelompok</h3>
          <p class="import-hint">Saran dipilih dari nama kelompok yang mirip. Pilih "Jangan ubah kelompok" bila kelompok siswa tidak perlu diubah.</p>
          <ul class="import-classes">
            <li v-for="item in preview.kelas" :key="item.kelas">
              <label :for="`impor-kelas-${item.kelas}`"><strong>{{ item.kelas }}</strong> <span>{{ item.jumlah }} siswa</span></label>
              <Select :input-id="`impor-kelas-${item.kelas}`" :model-value="kelasMap[item.kelas] ?? null" :options="groupOptions" option-label="label" option-value="value" :disabled="saving" filter empty-filter-message="Kelompok tidak ditemukan" fluid @update:model-value="setGroup(item.kelas, $event)"><template #filtericon><Icon name="magnifying-glass" /></template><template #dropdownicon><Icon name="caret-down" /></template></Select>
            </li>
          </ul>
          <p v-if="unmappedNew.length" class="import-warn" role="status">Siswa baru dari {{ unmappedNew.join(', ') }} akan tersimpan tanpa kelompok.</p>
        </section>
        <section class="import-step" aria-labelledby="impor-ringkasan-title">
          <h3 id="impor-ringkasan-title">Ringkasan</h3>
          <dl class="import-summary">
            <div><dt>Siswa baru</dt><dd>{{ preview.ringkasan.baru }}</dd></div>
            <div><dt>Diperbarui</dt><dd>{{ preview.ringkasan.ubah }}</dd></div>
            <div><dt>Sudah sama</dt><dd>{{ preview.ringkasan.sama }}</dd></div>
            <div :class="{ 'is-critical': preview.ringkasan.galat }"><dt>Bermasalah</dt><dd>{{ preview.ringkasan.galat }}</dd></div>
          </dl>
          <p class="import-hint">Siswa baru berstatus aktif dengan SPP Rp 0 dan ditandai "Belum diisi" di daftar. Isi SPP-nya sebelum tagihan bulanan dibuat. Sel kosong di berkas tidak menghapus data yang sudah ada.</p>
        </section>
        <section v-for="group in groups" :key="group.key" class="import-step" :aria-labelledby="`impor-${group.key}-title`">
          <h3 :id="`impor-${group.key}-title`">{{ group.title }} <Tag :value="String(group.rows.length)" :severity="group.key === 'galat' ? 'danger' : group.key === 'baru' ? 'success' : 'info'" /></h3>
          <ul class="import-rows">
            <li v-for="row in group.rows" :key="row.baris">
              <div class="import-row-head"><strong>{{ row.nama }}</strong><span>{{ row.kelas }} · baris {{ row.baris }}</span></div>
              <p v-if="rowNote(row)" :class="{ 'import-error': row.galat }">{{ rowNote(row) }}</p>
              <dl v-if="row.aksi === 'baru' && row.nilai.alamat" class="import-changes"><div><dt>Alamat</dt><dd>{{ row.nilai.alamat }}</dd></div></dl>
              <dl v-if="row.aksi === 'ubah'" class="import-changes">
                <div v-for="(change, field) in row.perubahan" :key="field"><dt>{{ FIELD_LABEL[field] ?? field }}</dt><dd><span class="import-old">{{ show(String(field), change[0]) }}</span> → {{ show(String(field), change[1]) }}</dd></div>
              </dl>
              <ul v-if="row.peringatan.length" class="import-notes"><li v-for="note in row.peringatan" :key="note"><Icon name="warning" />{{ note }}</li></ul>
            </li>
          </ul>
        </section>
      </template>
    </div>
    <template #footer>
      <span v-if="saving" class="import-saving" role="status">Menyimpan…</span>
      <Button label="Batal" severity="secondary" :disabled="saving" @click="visible = false" />
      <Button :label="toSave ? `Simpan ${toSave} siswa` : 'Tidak ada yang disimpan'" :disabled="!preview || loading || !toSave" :loading="saving" @click="run(true)"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
    </template>
  </Dialog>
</template>

<style scoped>
.import-body { display: grid; gap: var(--bee-space-5); }
.import-step { display: grid; gap: var(--bee-space-3); min-width: 0; }
.import-step + .import-step { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-5); }
.import-step h3 { margin: 0; font-size: var(--bee-type-body); font-weight: 600; display: flex; align-items: center; gap: var(--bee-space-2); }
.import-intro { margin: 0; color: var(--app-text-muted); max-width: 64ch; }
.import-hint { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.5; max-width: 64ch; }
.import-file { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 44px; padding: 0 var(--bee-space-4); border: 1px dashed var(--app-border-strong, var(--app-border)); border-radius: var(--bee-radius-control); cursor: pointer; justify-self: start; max-width: 100%; overflow-wrap: anywhere; }
.import-file:hover { border-color: var(--bee-color-brand); color: var(--bee-color-brand); }
.import-file-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.import-file:has(+ .import-file-input:focus-visible) { outline: 2px solid var(--bee-color-brand); outline-offset: 2px; }
.import-status { margin: 0; display: flex; align-items: center; gap: var(--bee-space-2); color: var(--app-text-muted); }
.import-classes { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--bee-space-3) var(--bee-space-4); }
.import-classes li { display: grid; gap: var(--bee-space-2); min-width: 0; }
.import-classes label span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.import-warn { margin: 0; color: var(--bee-color-warning-text, var(--app-text)); font-size: var(--bee-type-caption); }
.import-summary { margin: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--bee-space-3); }
.import-summary div { padding: var(--bee-space-3); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); }
.import-summary dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.import-summary dd { margin: 0; font-size: var(--bee-type-section); font-weight: 600; font-variant-numeric: tabular-nums; }
.import-summary .is-critical dd { color: var(--bee-color-critical); }
.import-rows { list-style: none; margin: 0; padding: 0; display: grid; }
.import-rows > li { padding: var(--bee-space-3) 0; border-bottom: 1px solid var(--app-border); display: grid; gap: var(--bee-space-1); min-width: 0; }
.import-row-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: var(--bee-space-1) var(--bee-space-3); }
.import-row-head span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.import-rows p { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.import-rows p.import-error { color: var(--bee-color-critical); }
.import-changes { margin: 0; display: grid; gap: var(--bee-space-1); font-size: var(--bee-type-caption); }
.import-changes div { display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: var(--bee-space-2); }
.import-changes dt { color: var(--app-text-muted); }
.import-changes dd { margin: 0; overflow-wrap: anywhere; }
.import-old { color: var(--app-text-muted); text-decoration: line-through; }
.import-notes { list-style: none; margin: 0; padding: 0; font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.import-notes li { display: flex; align-items: center; gap: var(--bee-space-1); }
.import-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media (max-width: 560px) {
  .import-classes, .import-summary { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
  .import-classes { grid-template-columns: minmax(0, 1fr); }
  .import-changes div { grid-template-columns: minmax(0, 1fr); gap: 0; }
}
</style>
