<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { pegawaiApi, pinjamanApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { useAuthStore } from "@/stores/auth"
import type { Pegawai, Pinjaman } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Pinjaman[]>([])
const pegawaiList = ref<Pegawai[]>([])
const loading = ref(false)

const canWrite = computed(() => auth.hasRole(["Finance"]))
const pegawaiNama = computed(() => {
  const map = new Map<number, string>()
  pegawaiList.value.forEach((p) => map.set(p.id, p.nama))
  return map
})

function rp(v: string | number | null | undefined) {
  return "Rp " + Number(v ?? 0).toLocaleString("id-ID")
}

async function load() {
  loading.value = true
  try {
    rows.value = (await pinjamanApi.list()).results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data pinjaman.")
  } finally {
    loading.value = false
  }
}

// --- form ---
const dialog = ref(false)
const saving = ref(false)
const form = reactive<{
  pegawai: number | null
  tanggal_pinjaman: Date
  jumlah_pinjaman: number
  tenor_bulan: number
  angsuran_per_bulan: number
}>({
  pegawai: null,
  tanggal_pinjaman: new Date(),
  jumlah_pinjaman: 0,
  tenor_bulan: 1,
  angsuran_per_bulan: 0,
})

function openCreate() {
  form.pegawai = null
  form.tanggal_pinjaman = new Date()
  form.jumlah_pinjaman = 0
  form.tenor_bulan = 1
  form.angsuran_per_bulan = 0
  dialog.value = true
}

async function save() {
  if (!form.pegawai) return
  saving.value = true
  try {
    await pinjamanApi.create({
      pegawai: form.pegawai,
      tanggal_pinjaman: form.tanggal_pinjaman.toISOString().slice(0, 10),
      jumlah_pinjaman: String(form.jumlah_pinjaman || 0),
      tenor_bulan: form.tenor_bulan,
      angsuran_per_bulan: String(form.angsuran_per_bulan || 0),
    })
    notifySuccess(toast, "Pengajuan kasbon disimpan")
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan pengajuan kasbon.")
  } finally {
    saving.value = false
  }
}

function cairkan(p: Pinjaman) {
  confirm.require({
    message: `Cairkan kasbon ${pegawaiNama.value.get(p.pegawai) ?? ""} sebesar ${rp(p.jumlah_pinjaman)}? Jurnal kas akan dibuat otomatis.`,
    header: "Konfirmasi Pencairan",
    icon: "pi pi-wallet",
    rejectLabel: "Batal",
    acceptLabel: "Cairkan",
    accept: async () => {
      try {
        const res = await pinjamanApi.cairkan(p.id)
        notifySuccess(toast, "Kasbon dicairkan", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal mencairkan kasbon.")
      }
    },
  })
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
      <h1>Kasbon / Pinjaman Pegawai</h1>
      <Button v-if="canWrite" label="Ajukan Kasbon" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada pinjaman.</template>
      <Column header="Pegawai">
        <template #body="{ data }">{{ pegawaiNama.get(data.pegawai) ?? `#${data.pegawai}` }}</template>
      </Column>
      <Column field="tanggal_pinjaman" header="Tanggal" />
      <Column header="Jumlah"><template #body="{ data }">{{ rp(data.jumlah_pinjaman) }}</template></Column>
      <Column header="Tenor">
        <template #body="{ data }">{{ data.tenor_bulan }} bln</template>
      </Column>
      <Column header="Sisa"><template #body="{ data }">{{ rp(data.sisa_pinjaman) }}</template></Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.jurnal ? 'Sudah dicairkan' : 'Menunggu pencairan'"
            :severity="data.jurnal ? 'success' : 'warn'"
          />
        </template>
      </Column>
      <Column header="Aksi" style="width: 9rem">
        <template #body="{ data }">
          <Button
            v-if="canWrite && !data.jurnal"
            label="Cairkan"
            size="small"
            text
            @click="cairkan(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="dialog" header="Ajukan Kasbon" modal :style="{ width: '32rem' }">
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
          <label>Tanggal Pinjaman</label>
          <DatePicker v-model="form.tanggal_pinjaman" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field">
          <label>Jumlah</label>
          <InputNumber v-model="form.jumlah_pinjaman" :min="0" fluid />
        </div>
        <div class="field">
          <label>Tenor (bulan)</label>
          <InputNumber v-model="form.tenor_bulan" :min="1" fluid />
        </div>
        <div class="field">
          <label>Angsuran / bulan</label>
          <InputNumber v-model="form.angsuran_per_bulan" :min="0" fluid />
        </div>
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
