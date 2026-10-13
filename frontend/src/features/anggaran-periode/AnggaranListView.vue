<script setup lang="ts">
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
import { computed, onMounted, reactive, ref } from "vue"

import { anggaranApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { coaApi } from "@/features/jurnal/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Anggaran, Coa } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Anggaran[]>([])
const coaList = ref<Coa[]>([])
const loading = ref(false)
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
  coaList.value.filter((c) => c.kode_akun.startsWith("5")),
)

const pendapatanAkunCount = computed(() =>
  coaList.value.filter((c) => c.kode_akun.startsWith("4")).length,
)

function rp(v: string | number | null | undefined) {
  return formatRp(v)
}

async function load() {
  loading.value = true
  try { rows.value = (await anggaranApi.list()).results }
  catch (e) { notifyError(toast, e, "Gagal memuat data anggaran.") }
  finally { loading.value = false }
}

const dialog = ref(false)
const saving = ref(false)
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
  () => !!form.kode_akun && form.tahun_anggaran > 0 && form.nominal_anggaran > 0,
)

async function save() {
  if (!formValid.value) return
  saving.value = true
  const payload = {
    kode_akun: form.kode_akun as string,
    tahun_anggaran: form.tahun_anggaran,
    bulan: form.bulan,
    nominal_anggaran: String(form.nominal_anggaran),
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
    notifyError(toast, e, "Gagal menyimpan anggaran.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: Anggaran) {
  confirm.require({
    message: `Hapus anggaran akun ${row.kode_akun} tahun ${row.tahun_anggaran}?`,
    header: "Konfirmasi",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await anggaranApi.remove(row.id)
        notifySuccess(toast, "Anggaran dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus anggaran.")
      }
    },
  })
}

onMounted(async () => {
  await load()
  try { coaList.value = await coaApi.list() } catch { /* fallback */ }
})
</script>

<template>
  <PageLayout title="Anggaran" subtitle="Atur pagu beban (akun 5.x) — dipasangkan dengan pendapatan 4.x di laporan">
    <Message severity="info" :closable="false" class="mb">
      <strong>Anggaran</strong> diisi manual untuk akun <strong>beban (5.x)</strong> per tahun.
      Pendapatan (4.x, {{ pendapatanAkunCount }} akun) terisi otomatis dari tagihan &amp; jurnal pemasukan.
    </Message>
    <template #actions>
      <Button v-if="canWrite" label="Tambah Anggaran" icon="pi pi-plus" @click="openCreate" />
    </template>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada anggaran.</template>
      <Column header="Akun">
        <template #body="{ data }">
          <strong>{{ data.kode_akun }}</strong>
          <span class="muted"> — {{ coaNama.get(data.kode_akun) ?? "-" }}</span>
          <Tag value="Beban 5.x" severity="secondary" class="ml" />
        </template>
      </Column>
      <Column header="Tahun"><template #body="{ data }">{{ data.tahun_anggaran }}</template></Column>
      <Column header="Bulan">
        <template #body="{ data }">
          {{ data.bulan ? BULAN_OPTS[data.bulan].label : "Tahunan" }}
        </template>
      </Column>
      <Column header="Pagu"><template #body="{ data }">{{ rp(data.nominal_anggaran) }}</template></Column>
      <Column header="Carry-over">
        <template #body="{ data }">{{ data.carry_over ? "Ya" : "Tidak" }}</template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
        <template #body="{ data }">
          <div v-if="canWrite" class="bee-actions">
            <Button v-if="canWrite" icon="pi pi-pencil" text rounded aria-label="Edit" @click="openEdit(data)" />
            <Button v-if="canWrite" icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Anggaran' : 'Tambah Anggaran'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Akun Beban *</label>
          <Select v-model="form.kode_akun" :options="bebanCoaList" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih akun beban" fluid>
            <template #option="{ option }">
              <span>{{ option.kode_akun }} — {{ option.nama_akun }}</span>
            </template>
          </Select>
        </div>
        <div class="field">
          <label>Tahun Anggaran *</label>
          <InputNumber v-model="form.tahun_anggaran" :min="2020" :max="2100" :use-grouping="false" fluid />
        </div>
        <div class="field">
          <label>Bulan</label>
          <Select v-model="form.bulan" :options="BULAN_OPTS" option-label="label" option-value="value" fluid />
        </div>
        <div class="field span2">
          <label>Nominal Pagu *</label>
          <InputNumber v-model="form.nominal_anggaran" :min="0" fluid />
        </div>
        <div class="field span2">
          <label>Keterangan</label>
          <InputText v-model="form.keterangan" fluid />
        </div>
        <div class="field span2 inline">
          <label>Gulung ke tahun berikutnya (carry-over)</label>
          <ToggleSwitch v-model="form.carry_over" />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan" :disabled="!formValid" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field.inline { flex-direction: row; align-items: center; justify-content: space-between; }
.field label { font-weight: 600; font-size: 0.85rem; }
.muted { color: var(--app-text-muted); }
.mb { margin-bottom: 1rem; }
.ml { margin-left: 0.35rem; vertical-align: middle; }
</style>
