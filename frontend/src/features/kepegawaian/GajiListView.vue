<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { gajiApi, pegawaiApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { useAuthStore } from "@/stores/auth"
import type { Gaji, Pegawai } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()

const rows = ref<Gaji[]>([])
const pegawaiList = ref<Pegawai[]>([])
const loading = ref(false)

const canWrite = computed(() => auth.hasRole(["Finance"]))
const pegawaiNama = computed(() => {
  const map = new Map<number, string>()
  pegawaiList.value.forEach((p) => map.set(p.id, p.nama))
  return map
})

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
function rp(v: string | number | null | undefined) {
  return "Rp " + Number(v ?? 0).toLocaleString("id-ID")
}

async function load() {
  loading.value = true
  try {
    rows.value = (await gajiApi.list()).results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data gaji.")
  } finally {
    loading.value = false
  }
}

// --- form ---
const dialog = ref(false)
const saving = ref(false)
const form = reactive<Partial<Gaji>>({})

function openCreate() {
  const now = new Date()
  Object.assign(form, {
    pegawai: undefined,
    periode_bulan: now.getMonth() + 1,
    periode_tahun: now.getFullYear(),
    gaji_pokok: "0", tunjangan_jabatan: "0", tunjangan_pengabdian: "0",
    transport: "0", bonus_insentif: "0", thr: "0",
    potongan_pinjaman: "0", potongan_asuransi: "0",
  })
  dialog.value = true
}

async function save() {
  if (!form.pegawai) return
  saving.value = true
  try {
    await gajiApi.create(form)
    notifySuccess(toast, "Data gaji disimpan")
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan data gaji.")
  } finally {
    saving.value = false
  }
}

async function posting(g: Gaji) {
  try {
    const res = await gajiApi.posting(g.id)
    notifySuccess(toast, "Payroll diposting", res)
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal memposting gaji.")
  }
}

onMounted(async () => {
  await load()
  try {
    pegawaiList.value = (await pegawaiApi.list()).results
  } catch {
    /* dropdown kosong jika gagal */
  }
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Gaji Pegawai</h1>
      <Button v-if="canWrite" label="Buat Slip Gaji" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada data gaji.</template>
      <Column header="Pegawai">
        <template #body="{ data }">{{ pegawaiNama.get(data.pegawai) ?? `#${data.pegawai}` }}</template>
      </Column>
      <Column header="Periode">
        <template #body="{ data }">{{ BULAN[data.periode_bulan - 1] }} {{ data.periode_tahun }}</template>
      </Column>
      <Column header="Bruto"><template #body="{ data }">{{ rp(data.total_bruto) }}</template></Column>
      <Column header="Netto"><template #body="{ data }">{{ rp(data.total_netto) }}</template></Column>
      <Column header="Status Jurnal">
        <template #body="{ data }">
          <Tag
            :value="data.jurnal ? 'Sudah dijurnal' : 'Belum dijurnal'"
            :severity="data.jurnal ? 'success' : 'warn'"
          />
        </template>
      </Column>
      <Column header="Aksi" style="width: 9rem">
        <template #body="{ data }">
          <Button
            v-if="canWrite && !data.jurnal"
            label="Posting"
            size="small"
            text
            @click="posting(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="dialog" header="Buat Slip Gaji" modal :style="{ width: '36rem' }">
      <div class="form-grid">
        <div class="field span2">
          <label>Pegawai *</label>
          <Select
            v-model="form.pegawai"
            :options="pegawaiList"
            option-label="nama"
            option-value="id"
            filter
            placeholder="Pilih pegawai"
            fluid
          />
        </div>
        <div class="field">
          <label>Bulan</label>
          <Select
            v-model="form.periode_bulan"
            :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
            option-label="label"
            option-value="value"
            fluid
          />
        </div>
        <div class="field">
          <label>Tahun</label>
          <InputNumber v-model="form.periode_tahun as unknown as number" :min="2020" :max="2100" :use-grouping="false" fluid />
        </div>

        <div class="field"><label>Gaji Pokok</label><InputNumber v-model="form.gaji_pokok as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Tunjangan Jabatan</label><InputNumber v-model="form.tunjangan_jabatan as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Tunjangan Pengabdian</label><InputNumber v-model="form.tunjangan_pengabdian as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Transport</label><InputNumber v-model="form.transport as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Bonus / Insentif</label><InputNumber v-model="form.bonus_insentif as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>THR</label><InputNumber v-model="form.thr as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Potongan Pinjaman</label><InputNumber v-model="form.potongan_pinjaman as unknown as number" :min="0" fluid /></div>
        <div class="field"><label>Potongan Asuransi</label><InputNumber v-model="form.potongan_asuransi as unknown as number" :min="0" fluid /></div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan" :disabled="!form.pegawai" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.page-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field label { font-weight: 600; font-size: 0.85rem; }
</style>
