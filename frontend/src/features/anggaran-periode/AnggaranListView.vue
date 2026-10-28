<script setup lang="ts">
import BeePaginator from "@/shared/components/BeePaginator.vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Select from "primevue/select"
import Message from "primevue/message"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"

import { anggaranApi } from "./api"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { coaApi } from "@/features/jurnal/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import BudgetTabs from "./BudgetTabs.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { useAuthStore } from "@/stores/auth"
import type { Anggaran, Coa } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Anggaran[]>([])
const coaList = ref<Coa[]>([])
const loading = ref(false)
const error = ref("")
const coaError = ref("")
const query = ref("")
const year = ref<number | null>(null)
const tableFirst = ref(0)
const canWrite = computed(() => auth.hasRole(["Finance"]))

const BULAN_OPTS = [
  { label: "Tahunan (semua bulan)", value: null },
  ...Array.from({ length: 12 }, (_, i) => ({
    label: ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"][i],
    value: i + 1,
  })),
]

const coaNama = computed(() => {
  const m = new Map<string, string>()
  coaList.value.forEach((c) => m.set(c.kode_akun, c.nama_akun))
  return m
})

const bebanCoaList = computed(() =>
  coaList.value.filter((c) => c.kode_akun.startsWith("5") && (c.is_active || c.kode_akun === form.kode_akun)),
)

const yearOptions = computed(() => [...new Set(rows.value.map((row) => row.tahun_anggaran))].sort((a, b) => b - a).map((value) => ({ label: String(value), value })))
const filtered = computed(() => rows.value.filter((row) =>
  (year.value === null || row.tahun_anggaran === year.value)
  && (!query.value.trim() || [row.kode_akun, coaNama.value.get(row.kode_akun) ?? "", row.keterangan ?? ""].some((text) => text.toLocaleLowerCase("id-ID").includes(query.value.trim().toLocaleLowerCase("id-ID")))),
))
watch([query, year], () => { tableFirst.value = 0 })

function rp(v: string | number | null | undefined) {
  const amount = Number(v)
  return Number.isFinite(amount) ? "Rp " + amount.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"
}

async function load() {
  if (loading.value) return
  loading.value = true
  error.value = ""
  try { rows.value = await anggaranApi.listAll() }
  catch (cause) {
    rows.value = []
    const message = friendlyError(cause, "Anggaran belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  }
  finally { loading.value = false }
}
async function loadCoa() {
  coaError.value = ""
  try { coaList.value = await coaApi.list() }
  catch (cause) {
    coaList.value = []
    const message = friendlyError(cause, "Pilihan akun beban belum tersedia")
    coaError.value = [message.summary, message.detail].filter(Boolean).join(". ")
  }
}

const dialog = ref(false)
const saving = ref(false)
const formError = ref("")
const editingId = ref<number | null>(null)
const form = reactive<{
  kode_akun: string | null
  tahun_anggaran: number
  bulan: number | null
  nominal_anggaran: number
  keterangan: string
  carry_over: boolean
}>({
  kode_akun: null,
  tahun_anggaran: new Date().getFullYear(),
  bulan: null,
  nominal_anggaran: 0,
  keterangan: "",
  carry_over: false,
})

function openCreate() {
  formError.value = ""
  editingId.value = null
  form.kode_akun = null
  form.tahun_anggaran = new Date().getFullYear()
  form.bulan = null
  form.nominal_anggaran = 0
  form.keterangan = ""
  form.carry_over = false
  dialog.value = true
}
function openEdit(row: Anggaran) {
  formError.value = ""
  editingId.value = row.id
  form.kode_akun = row.kode_akun
  form.tahun_anggaran = row.tahun_anggaran
  form.bulan = row.bulan
  form.nominal_anggaran = Number(row.nominal_anggaran)
  form.keterangan = row.keterangan ?? ""
  form.carry_over = row.carry_over
  dialog.value = true
}

const formValid = computed(
  () => !!form.kode_akun && Number.isInteger(form.tahun_anggaran) && form.tahun_anggaran >= 2020 && form.tahun_anggaran <= 2100 && form.nominal_anggaran > 0 && Number.isSafeInteger(Math.round(form.nominal_anggaran * 100)),
)

async function save() {
  if (saving.value || !canWrite.value || coaError.value) return
  if (!formValid.value) { formError.value = "Pilih akun beban, tahun 2020–2100, dan pagu positif yang dapat dihitung tepat hingga dua desimal."; return }
  formError.value = ""
  saving.value = true
  const payload = {
    kode_akun: form.kode_akun as string,
    tahun_anggaran: form.tahun_anggaran,
    bulan: form.bulan,
    nominal_anggaran: form.nominal_anggaran.toFixed(2),
    keterangan: form.keterangan || null,
    carry_over: form.carry_over,
  }
  try {
    if (editingId.value) {
      await anggaranApi.update(editingId.value, payload)
      notifySuccess(toast, "Anggaran diperbarui")
    } else {
      await anggaranApi.create(payload)
      notifySuccess(toast, "Anggaran ditambahkan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Belum dapat memastikan anggaran tersimpan. Periksa daftar sebelum mencoba lagi.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: Anggaran) {
  confirm.require({
    message: `Hapus pagu ${coaNama.value.get(row.kode_akun) ?? row.kode_akun} untuk ${row.tahun_anggaran} (${row.bulan ? BULAN_OPTS[row.bulan]?.label : "Tahunan"})? Baris ini tidak lagi masuk total pagu laporan.`,
    header: "Hapus anggaran?",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await anggaranApi.remove(row.id)
        notifySuccess(toast, "Anggaran dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Belum dapat memastikan anggaran terhapus. Periksa daftar sebelum mencoba lagi.")
      }
    },
  })
}

onMounted(async () => {
  await Promise.all([load(), loadCoa()])
})
</script>

<template>
  <PageLayout title="Anggaran Kegiatan" subtitle="Pagu beban per akun dan tahun kalender untuk laporan realisasi." :surface="false">
    <template #actions>
      <Button v-if="canWrite" label="Tambah anggaran" :disabled="loading || !!error || !!coaError || !bebanCoaList.length" @click="openCreate"><template #icon><Icon name="plus" /></template></Button>
    </template>
    <BudgetTabs current="akun" />

    <div class="budget-scope"><Icon name="info" /><p>Laporan realisasi menjumlah seluruh pagu akun pada <strong>tahun kalender</strong> yang sama, termasuk baris tahunan dan bulanan. Bulan dan penanda carry-over belum membatasi atau memindahkan pagu laporan secara otomatis.</p></div>
    <div v-if="coaError && canWrite" class="budget-notice"><Message severity="warn" :closable="false">{{ coaError }} Daftar tetap dapat dibaca, tetapi penambahan dan pengubahan anggaran ditahan.</Message><Button label="Muat ulang akun" severity="secondary" @click="loadCoa" /></div>
    <section class="budget-panel" aria-label="Daftar anggaran" :aria-busy="loading">
      <div class="budget-toolbar"><div class="budget-field budget-search"><label for="budget-search">Cari anggaran</label><SearchField input-id="budget-search" v-model="query" placeholder="Kode, akun, atau keterangan" hint="Mencari seluruh anggaran yang dimuat" /></div><div class="budget-field"><label for="budget-year">Tahun anggaran</label><Select input-id="budget-year" v-model="year" :options="yearOptions" option-label="label" option-value="value" placeholder="Semua tahun" show-clear :disabled="loading || !!error" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div><Button label="Muat ulang" severity="secondary" :disabled="loading" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template></Button></div>
      <div v-if="error" class="budget-notice"><Message severity="error" :closable="false">{{ error }}</Message><Button label="Coba muat ulang anggaran" severity="secondary" @click="load" /></div>
      <p class="budget-results" role="status">{{ loading ? "Memuat anggaran…" : error ? "Daftar belum tersedia" : filtered.length ? filtered.length + " anggaran ditampilkan" : "Tidak ada anggaran ditampilkan" }}</p>
      <div v-if="!loading && !error && !filtered.length" class="budget-empty"><Icon :name="query || year ? 'magnifying-glass' : 'chart-pie'" /><h2>{{ query || year ? 'Tidak ada anggaran yang cocok' : 'Belum ada anggaran' }}</h2><p>{{ query || year ? 'Ubah pencarian atau tahun anggaran.' : 'Pagu beban belum dicatat untuk laporan realisasi.' }}</p><Button v-if="query || year" label="Hapus filter" severity="secondary" @click="query = ''; year = null" /></div>
      <p v-if="!error && filtered.length" class="budget-scroll-hint"><Icon name="caret-right" /> Geser tabel untuk melihat pagu, carry-over, dan aksi.</p>
      <div v-if="!error && (loading || filtered.length)" class="budget-table-scroll" role="region" tabindex="0" aria-label="Tabel anggaran dapat digulir horizontal">
    <DataTable :value="filtered.slice(tableFirst, tableFirst + 15)" :loading="loading" data-key="id" striped-rows>
      <Column header="Akun">
        <template #body="{ data }">
          <strong>{{ data.kode_akun }}</strong>
          <span class="muted"> — {{ coaNama.get(data.kode_akun) ?? "-" }}</span>
          <Tag value="Beban" severity="secondary" class="ml" />
        </template>
      </Column>
      <Column header="Tahun"><template #body="{ data }">{{ data.tahun_anggaran }}</template></Column>
      <Column header="Bulan">
        <template #body="{ data }">
          {{ data.bulan ? BULAN_OPTS[data.bulan]?.label ?? "Bulan tidak dikenal" : "Tahunan" }}
        </template>
      </Column>
      <Column header="Pagu"><template #body="{ data }">{{ rp(data.nominal_anggaran) }}</template></Column>
      <Column header="Carry-over">
        <template #body="{ data }">{{ data.carry_over ? "Ditandai" : "Tidak" }}</template>
      </Column>
      <Column v-if="canWrite" header="Tindakan" headerClass="bee-col-actions--md" bodyClass="bee-col-actions--md">
        <template #body="{ data }">
          <div v-if="canWrite" class="bee-actions">
            <Button label="Ubah" text severity="secondary" :disabled="!!coaError" @click="openEdit(data)" />
            <Button label="Hapus" text severity="danger" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
      </div>
      <BeePaginator v-model:first="tableFirst" :rows="15" :total-records="filtered.length" />
    </section>

    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Ubah anggaran' : 'Tambah anggaran'"
      modal
      class="budget-dialog"
      :closable="!saving"
      :dismissable-mask="!saving"
      :close-on-escape="!saving"
    >
      <div class="form-grid">
        <p class="budget-form-intro span2">Pagu masuk ke laporan realisasi sesuai tahun kalender. Jika ada baris tahunan dan bulanan pada akun yang sama, nominalnya dijumlahkan.</p>
        <div class="field span2">
          <label for="budget-account">Akun beban (wajib)</label>
          <Select input-id="budget-account" v-model="form.kode_akun" :options="bebanCoaList" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih akun beban" :disabled="saving" fluid>
            <template #option="{ option }">
              <span>{{ option.kode_akun }} — {{ option.nama_akun }}</span>
            </template>
          </Select>
        </div>
        <div class="field">
          <label for="budget-form-year">Tahun kalender (wajib)</label>
          <InputNumber input-id="budget-form-year" v-model="form.tahun_anggaran" :min="2020" :max="2100" :use-grouping="false" :disabled="saving" fluid />
        </div>
        <div class="field">
          <label for="budget-form-month">Bulan</label>
          <Select input-id="budget-form-month" v-model="form.bulan" :options="BULAN_OPTS" option-label="label" option-value="value" placeholder="Tahunan" :disabled="saving" fluid />
        </div>
        <div class="field span2">
          <label for="budget-amount">Pagu (wajib)</label>
          <InputNumber input-id="budget-amount" v-model="form.nominal_anggaran" mode="currency" currency="IDR" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="saving" fluid />
        </div>
        <div class="field span2">
          <label for="budget-note">Keterangan</label>
          <InputText id="budget-note" v-model="form.keterangan" :disabled="saving" fluid />
        </div>
        <div class="field span2 inline">
          <label for="budget-carry">Tandai carry-over</label>
          <ToggleSwitch input-id="budget-carry" v-model="form.carry_over" :disabled="saving" />
        </div>
        <small class="span2 budget-help">Penanda ini belum memindahkan sisa pagu ke tahun berikutnya secara otomatis.</small>
        <Message v-if="formError" severity="error" :closable="false" class="span2" role="alert">{{ formError }}</Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text :disabled="saving" @click="dialog = false" />
        <Button label="Simpan" :loading="saving" :disabled="saving || !!coaError" @click="save" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.budget-scope { display: flex; align-items: start; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); padding: var(--bee-space-4) var(--bee-space-5); background: var(--app-surface); border-inline-start: 3px solid var(--bee-color-info); border-radius: var(--bee-radius-control); }
.budget-scope .bee-icon { width: 20px; height: 20px; flex: none; color: var(--bee-color-info); }
.budget-scope p { margin: 0; max-width: 95ch; line-height: 1.55; }
.budget-panel { overflow: hidden; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.budget-toolbar { display: flex; flex-wrap: wrap; align-items: end; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.budget-field { display: grid; gap: var(--bee-space-2); flex: 1 1 190px; min-width: 0; }
.budget-field label { font-size: var(--bee-type-caption); font-weight: 600; }
.budget-search { flex: 2 1 280px; }
.budget-search :deep(.bee-search-field) { min-width: 0; }
.budget-notice { display: flex; align-items: center; flex-wrap: wrap; gap: var(--bee-space-3); margin-bottom: var(--bee-space-4); }
.budget-panel .budget-notice { padding-inline: var(--bee-space-5); }
.budget-notice .p-message { flex: 1 1 300px; }
.budget-results { margin: 0; padding: var(--bee-space-3) var(--bee-space-5); border-top: 1px solid var(--app-border); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.budget-empty { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-7) var(--bee-space-5); text-align: center; }
.budget-empty .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); }
.budget-empty h2 { margin: 0; font-size: var(--bee-type-section); }
.budget-empty p { margin: 0; color: var(--app-text-muted); }
.budget-table-scroll { overflow-x: auto; }
.budget-scroll-hint { display: none; align-items: center; gap: var(--bee-space-2); margin: 0; padding: var(--bee-space-3) var(--bee-space-5); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.budget-scroll-hint .bee-icon { width: 16px; height: 16px; }
.budget-table-scroll :deep(.p-datatable) { min-width: 820px; }
.budget-dialog { width: min(540px, calc(100vw - 32px)); }
.budget-form-intro { margin: 0; color: var(--app-text-muted); line-height: 1.5; }
.budget-help { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field.inline { flex-direction: row; align-items: center; justify-content: space-between; }
.field label { font-weight: 600; font-size: 0.85rem; }
.muted { color: var(--app-text-muted); }
.mb { margin-bottom: 1rem; }
.ml { margin-left: 0.35rem; vertical-align: middle; }
@media (max-width: 900px) { .budget-scroll-hint { display: flex; } }
@media (max-width: 540px) { .budget-toolbar > .budget-field { flex-basis: 100%; } .budget-toolbar > .p-button { width: 100%; } .form-grid { grid-template-columns: minmax(0, 1fr); } .field.span2,.span2 { grid-column: 1; } }
</style>
