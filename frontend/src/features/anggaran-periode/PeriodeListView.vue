<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { periodeApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { useAuthStore } from "@/stores/auth"
import type { PeriodeAkuntansi } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<PeriodeAkuntansi[]>([])
const loading = ref(false)
const canCreate = computed(() => auth.hasRole(["Finance"]))
const canClose = computed(() => auth.hasRole(["SchoolPrincipal"]))

async function load() {
  loading.value = true
  try { rows.value = (await periodeApi.list()).results }
  catch (e) { notifyError(toast, e, "Gagal memuat periode akuntansi.") }
  finally { loading.value = false }
}

const dialog = ref(false)
const saving = ref(false)
const form = reactive<{ kode: string; tgl_mulai: Date; tgl_selesai: Date }>({
  kode: "",
  tgl_mulai: new Date(new Date().getFullYear(), 6, 1),    // 1 Juli
  tgl_selesai: new Date(new Date().getFullYear() + 1, 5, 30), // 30 Juni
})

function openCreate() {
  const y = new Date().getFullYear()
  form.kode = `${y}/${y + 1}`
  form.tgl_mulai = new Date(y, 6, 1)
  form.tgl_selesai = new Date(y + 1, 5, 30)
  dialog.value = true
}

async function save() {
  if (!form.kode.trim()) return
  saving.value = true
  try {
    await periodeApi.create({
      kode: form.kode,
      tgl_mulai: form.tgl_mulai.toISOString().slice(0, 10),
      tgl_selesai: form.tgl_selesai.toISOString().slice(0, 10),
    })
    notifySuccess(toast, "Periode akuntansi dibuat")
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal membuat periode.")
  } finally {
    saving.value = false
  }
}

function tutup(p: PeriodeAkuntansi) {
  confirm.require({
    message: `Tutup buku periode ${p.kode}? Sistem akan membuat jurnal penutup untuk akun pendapatan & beban ke ekuitas. Tindakan ini tidak dapat dibatalkan.`,
    header: "Konfirmasi Tutup Buku",
    icon: "pi pi-lock",
    rejectLabel: "Batal",
    acceptLabel: "Tutup Buku",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        const res = await periodeApi.tutup(p.id)
        notifySuccess(toast, "Periode ditutup", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menutup periode.")
      }
    },
  })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Periode Akuntansi</h1>
      <Button v-if="canCreate" label="Tambah Periode" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada periode terdaftar.</template>
      <Column field="kode" header="Periode" />
      <Column field="tgl_mulai" header="Mulai" />
      <Column field="tgl_selesai" header="Selesai" />
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status === 'OPEN' ? 'Terbuka' : 'Tertutup'"
            :severity="data.status === 'OPEN' ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="Aksi" style="width: 12rem">
        <template #body="{ data }">
          <Button
            v-if="canClose && data.status === 'OPEN'"
            label="Tutup Buku"
            size="small"
            severity="danger"
            text
            @click="tutup(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="dialog" header="Tambah Periode" modal :style="{ width: '28rem' }">
      <div class="form-grid">
        <div class="field span2">
          <label>Kode Periode *</label>
          <InputText v-model="form.kode" placeholder="contoh: 2025/2026" fluid />
        </div>
        <div class="field">
          <label>Tanggal Mulai</label>
          <DatePicker v-model="form.tgl_mulai" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field">
          <label>Tanggal Selesai</label>
          <DatePicker v-model="form.tgl_selesai" date-format="yy-mm-dd" fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan" :loading="saving" @click="save" />
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
