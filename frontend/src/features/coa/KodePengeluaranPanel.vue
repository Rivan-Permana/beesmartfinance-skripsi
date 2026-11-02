<script setup lang="ts">
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import BeePaginator from "@/shared/components/BeePaginator.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Coa, KodePengeluaran, KodePengeluaranInput, KodePengeluaranUnit } from "@/types/api"
import { kodePengeluaranApi } from "./api"

/** Kode buku kas sekolah -> akun beban, dipakai untuk input cepat di menu Pengeluaran. */
const props = defineProps<{ accounts: Coa[]; canWrite: boolean }>()
const toast = useToast()
const confirm = useConfirm()
const rows = ref<KodePengeluaran[]>([])
const loading = ref(false)
const error = ref("")
const first = ref(0)
const UNIT_OPTIONS: { value: KodePengeluaranUnit; label: string }[] = [
  { value: "UMUM", label: "Umum (operasional)" }, { value: "TK", label: "TK" }, { value: "PG", label: "PG" },
]
const accountOptions = computed(() => props.accounts.filter((a) => a.is_active || a.kode_akun === form.akun)
  .map((a) => ({ value: a.kode_akun, label: `${a.kode_akun} — ${a.nama_akun}` })))
const { query, filtered } = useTableSearch(rows, (row) => [row.kode, row.unit, row.nama, row.akun, row.akun_nama])
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 10))
watch(query, () => { first.value = 0 })
const mapped = computed(() => rows.value.filter((row) => row.akun).length)

async function load() {
  loading.value = true
  error.value = ""
  try { rows.value = await kodePengeluaranApi.list() }
  catch (e) {
    const err = friendlyError(e, "Kode pengeluaran belum berhasil dimuat")
    error.value = [err.summary, err.detail].filter(Boolean).join(". ")
  } finally { loading.value = false }
}
onMounted(load)

const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref("")
const form = reactive<KodePengeluaranInput>({ kode: "", unit: "UMUM", nama: "", akun: null, aktif: true })
const kodeInvalid = computed(() => !/^\S{1,20}$/.test(form.kode.trim()))
function open(row?: KodePengeluaran) {
  editingId.value = row?.id ?? null
  Object.assign(form, { kode: row?.kode ?? "", unit: row?.unit ?? "UMUM", nama: row?.nama ?? "", akun: row?.akun ?? null, aktif: row?.aktif ?? true })
  formError.value = ""
  dialog.value = true
}
async function save() {
  if (saving.value || kodeInvalid.value) return
  saving.value = true
  formError.value = ""
  try {
    const payload = { ...form, kode: form.kode.trim().toUpperCase(), nama: form.nama.trim() }
    if (editingId.value) await kodePengeluaranApi.update(editingId.value, payload)
    else await kodePengeluaranApi.create(payload)
    notifySuccess(toast, editingId.value ? "Kode pengeluaran diperbarui" : "Kode pengeluaran ditambahkan")
    dialog.value = false
    await load()
  } catch (e) {
    const err = friendlyError(e, "Kode belum berhasil disimpan")
    formError.value = [err.summary, err.detail].filter(Boolean).join(". ")
  } finally { saving.value = false }
}
function remove(row: KodePengeluaran) {
  confirm.require({
    header: "Hapus kode?", message: `Kode ${row.kode} (${row.unit}) dihapus dari pilihan input cepat. Jurnal yang sudah dibuat tidak berubah.`,
    acceptLabel: "Hapus kode", rejectLabel: "Batal", acceptProps: { severity: "danger" },
    accept: async () => {
      try { await kodePengeluaranApi.remove(row.id); notifySuccess(toast, "Kode dihapus"); await load() }
      catch (e) { notifyError(toast, e, "Kode belum berhasil dihapus") }
    },
  })
}
</script>

<template>
  <section class="kode-panel" aria-label="Kode pengeluaran sekolah" :aria-busy="loading">
    <header class="kode-heading">
      <div><h2>Kode pengeluaran sekolah</h2><p>Kode singkat dari buku kas (ATK, PLN, AB3 TK) yang otomatis memilih akun saat Staf TU membuat draf pengeluaran. Kode tanpa akun belum dikonfirmasi artinya.</p></div>
      <Button v-if="canWrite" label="Tambah kode" :disabled="loading" @click="open()"><template #icon><Icon name="plus" /></template></Button>
    </header>
    <div class="kode-toolbar"><SearchField input-id="kode-search" v-model="query" placeholder="Cari kode, nama, atau akun" hint="Cari kode, nama, atau akun" /><p v-if="!loading && !error" role="status">{{ mapped }} dari {{ rows.length }} kode sudah dipetakan</p></div>
    <div v-if="error" class="kode-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang" severity="secondary" @click="load" /></div>
    <div v-else-if="loading" class="kode-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Memuat kode</p></div>
    <div v-else-if="!filtered.length" class="kode-empty"><Icon name="magnifying-glass" /><p>{{ rows.length ? "Tidak ada kode yang cocok." : "Belum ada kode pengeluaran." }}</p></div>
    <template v-else>
      <table class="kode-table"><caption class="kode-sr-only">Kode pengeluaran sekolah</caption>
        <thead><tr><th>Kode</th><th>Nama</th><th>Akun</th><th>Status</th><th v-if="canWrite" class="kode-actions">Tindakan</th></tr></thead>
        <tbody><tr v-for="row in pageRows" :key="row.id">
          <td><strong>{{ row.kode }}</strong><small>{{ row.unit === "UMUM" ? "Umum" : row.unit }}</small></td>
          <td>{{ row.nama || "—" }}</td>
          <td><template v-if="row.akun">{{ row.akun }} <small>{{ row.akun_nama }}</small></template><Tag v-else value="Belum dipetakan" severity="warn" /></td>
          <td><Tag :value="row.aktif ? 'Aktif' : 'Nonaktif'" :severity="row.aktif ? 'success' : 'secondary'" /></td>
          <td v-if="canWrite" class="kode-actions"><Button label="Ubah" severity="secondary" :aria-label="`Ubah kode ${row.kode} ${row.unit}`" @click="open(row)" /><Button severity="secondary" text :aria-label="`Hapus kode ${row.kode} ${row.unit}`" @click="remove(row)"><template #icon><Icon name="trash" /></template></Button></td>
        </tr></tbody>
      </table>
      <ul class="kode-cards" aria-label="Kode pengeluaran sekolah"><li v-for="row in pageRows" :key="row.id">
        <div class="kode-card-title"><strong>{{ row.kode }}</strong><span>{{ row.unit === "UMUM" ? "Umum" : row.unit }}</span><Tag v-if="!row.aktif" value="Nonaktif" severity="secondary" /></div>
        <p>{{ row.nama || "Tanpa nama" }}</p>
        <p v-if="row.akun" class="kode-card-akun">{{ row.akun }} · {{ row.akun_nama }}</p><Tag v-else value="Belum dipetakan" severity="warn" />
        <div v-if="canWrite" class="kode-card-actions"><Button label="Ubah kode" severity="secondary" @click="open(row)" /><Button label="Hapus" severity="secondary" text @click="remove(row)" /></div>
      </li></ul>
      <BeePaginator v-if="filtered.length > 10" v-model:first="first" :rows="10" :total-records="filtered.length" />
    </template>

    <Dialog v-model:visible="dialog" :header="editingId ? 'Ubah kode pengeluaran' : 'Tambah kode pengeluaran'" modal class="coa-dialog" :closable="!saving" :close-on-escape="!saving" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup formulir kode' }"><template #closeicon><Icon name="x" /></template>
      <form id="kode-form" class="kode-form" @submit.prevent="save">
        <div class="kode-field"><label for="kode-kode">Kode <span>(wajib, satu kata)</span></label><InputText id="kode-kode" v-model="form.kode" maxlength="20" :invalid="!!form.kode && kodeInvalid" :disabled="saving" fluid placeholder="Contoh: ATK" /></div>
        <div class="kode-field"><label for="kode-unit">Unit</label><Select input-id="kode-unit" v-model="form.unit" :options="UNIT_OPTIONS" option-label="label" option-value="value" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select><small>Pakai TK/PG bila akunnya berbeda per jenjang, misalnya AB3.</small></div>
        <div class="kode-field kode-wide"><label for="kode-nama">Nama</label><InputText id="kode-nama" v-model="form.nama" maxlength="120" :disabled="saving" fluid placeholder="Contoh: Alat tulis kantor" /></div>
        <div class="kode-field kode-wide"><label for="kode-akun">Akun</label><Select input-id="kode-akun" v-model="form.akun" :options="accountOptions" option-label="label" option-value="value" placeholder="Belum dipetakan" show-clear filter :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select><small>Kosongkan bila arti kode belum pasti.</small></div>
        <label class="kode-toggle kode-wide"><ToggleSwitch v-model="form.aktif" :disabled="saving" />Aktif untuk input cepat</label>
        <Message v-if="formError" severity="error" :closable="false" class="kode-wide" role="alert">{{ formError }}</Message>
      </form>
      <template #footer><Button label="Batal" severity="secondary" text :disabled="saving" @click="dialog = false" /><Button type="submit" form="kode-form" label="Simpan" :disabled="kodeInvalid" :loading="saving" /></template>
    </Dialog>
  </section>
</template>

<style scoped>
.kode-panel { margin-top: var(--bee-space-5); background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: clip; }
.kode-heading { display: flex; align-items: start; justify-content: space-between; flex-wrap: wrap; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.kode-heading h2 { margin: 0; font-size: var(--bee-type-section); font-weight: 600; }.kode-heading p { margin: var(--bee-space-2) 0 0; max-width: 72ch; color: var(--app-text-muted); }
.kode-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-4); }
.kode-toolbar :deep(.bee-search-field) { flex: 0 1 360px; min-width: 0; }.kode-toolbar p { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.kode-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-4); }.kode-notice .p-message { flex: 1 1 300px; }
.kode-empty { display: grid; justify-items: center; gap: var(--bee-space-2); padding: var(--bee-space-6) var(--bee-space-5); color: var(--app-text-muted); border-top: 1px solid var(--app-border); }.kode-empty p { margin: 0; }
.kode-table { width: 100%; border-collapse: collapse; font-size: var(--bee-type-ui); }
.kode-table th { background: var(--bee-color-surface-subtle); color: var(--app-text-muted); font-size: var(--bee-type-caption); font-weight: 500; text-align: start; }
.kode-table th, .kode-table td { padding: var(--bee-space-3) var(--bee-space-5); border-top: 1px solid var(--app-border); }
.kode-table strong { font-weight: 500; }.kode-table small { display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.kode-actions { text-align: end; white-space: nowrap; }
.kode-cards { display: none; list-style: none; margin: 0; padding: 0; }
.kode-sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.kode-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--bee-space-4); }
.kode-field { display: grid; align-content: start; gap: var(--bee-space-2); min-width: 0; }.kode-field label { font-weight: 500; }.kode-field label span { font-weight: 400; color: var(--app-text-muted); }.kode-field small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.kode-wide { grid-column: 1 / -1; }
.kode-toggle { display: inline-flex; align-items: center; gap: var(--bee-space-2); cursor: pointer; }
@media (max-width: 767px) {
  .kode-heading, .kode-toolbar, .kode-notice { padding-inline: var(--bee-space-4); }.kode-heading > .p-button { width: 100%; }
  .kode-table { display: none; }.kode-cards { display: block; }
  .kode-cards li { display: grid; gap: var(--bee-space-2); justify-items: start; padding: var(--bee-space-4); border-top: 1px solid var(--app-border); }
  .kode-cards p { margin: 0; overflow-wrap: anywhere; }.kode-card-akun { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
  .kode-card-title { display: flex; align-items: center; gap: var(--bee-space-2); }.kode-card-title span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
  .kode-card-actions { display: flex; gap: var(--bee-space-2); }
  .kode-form { grid-template-columns: minmax(0, 1fr); }
}
</style>
