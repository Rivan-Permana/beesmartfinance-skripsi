<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import IconField from "primevue/iconfield"
import InputIcon from "primevue/inputicon"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { onMounted, reactive, ref } from "vue"

import { siswaApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import type { Siswa, SiswaStatus } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const rows = ref<Siswa[]>([])
const loading = ref(false)
const search = ref("")

const STATUS: { label: string; value: SiswaStatus }[] = [
  { label: "Aktif", value: "aktif" },
  { label: "Lulus", value: "lulus" },
  { label: "Cuti", value: "cuti" },
  { label: "Pindah", value: "pindah" },
  { label: "Mengulang Kelas", value: "mengulang" },
  { label: "Naik Kelas", value: "naik" },
]

const statusSeverity: Record<SiswaStatus, string> = {
  aktif: "success",
  naik: "info",
  mengulang: "warn",
  cuti: "warn",
  lulus: "secondary",
  pindah: "danger",
}

async function load() {
  loading.value = true
  try {
    const data = await siswaApi.list(search.value ? { search: search.value } : {})
    rows.value = data.results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data siswa.")
  } finally {
    loading.value = false
  }
}

// --- form dialog ---
const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<Partial<Siswa>>({})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    nis: "", nama: "", status: "aktif", spp_nominal: "0",
    nama_ayah: "", kontak_ayah: "", nama_ibu: "", kontak_ibu: "", alamat: "",
  })
  dialog.value = true
}

function openEdit(row: Siswa) {
  editingId.value = row.id
  Object.assign(form, { ...row })
  dialog.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingId.value) {
      await siswaApi.update(editingId.value, form)
      notifySuccess(toast, "Data siswa diperbarui")
    } else {
      await siswaApi.create(form)
      notifySuccess(toast, "Siswa baru ditambahkan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan data siswa.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: Siswa) {
  confirm.require({
    message: `Hapus siswa "${row.nama}"?`,
    header: "Konfirmasi",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await siswaApi.remove(row.id)
        notifySuccess(toast, "Siswa dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus siswa.")
      }
    },
  })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Data Siswa</h1>
      <Button label="Tambah Siswa" icon="pi pi-plus" @click="openCreate" />
    </div>

    <div class="toolbar">
      <IconField>
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="search"
          placeholder="Cari NIS / nama…"
          @keyup.enter="load"
        />
      </IconField>
      <Button label="Cari" severity="secondary" outlined @click="load" />
    </div>

    <DataTable
      :value="rows"
      :loading="loading"
      paginator
      :rows="10"
      data-key="id"
      striped-rows
    >
      <template #empty>Belum ada data siswa.</template>
      <Column field="nis" header="NIS" />
      <Column field="nama" header="Nama" />
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status"
            :severity="statusSeverity[data.status as SiswaStatus]"
          />
        </template>
      </Column>
      <Column header="SPP">
        <template #body="{ data }">Rp {{ Number(data.spp_nominal).toLocaleString("id-ID") }}</template>
      </Column>
      <Column header="Aksi" style="width: 8rem">
        <template #body="{ data }">
          <Button
            icon="pi pi-pencil"
            text
            rounded
            aria-label="Edit"
            @click="openEdit(data)"
          />
          <Button
            icon="pi pi-trash"
            text
            rounded
            severity="danger"
            aria-label="Hapus"
            @click="confirmDelete(data)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Siswa' : 'Tambah Siswa'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="form-grid">
        <div class="field">
          <label>NIS</label>
          <InputText v-model="form.nis as string" fluid />
        </div>
        <div class="field">
          <label>Nama *</label>
          <InputText v-model="form.nama" fluid />
        </div>
        <div class="field">
          <label>Status</label>
          <Select
            v-model="form.status"
            :options="STATUS"
            option-label="label"
            option-value="value"
            fluid
          />
        </div>
        <div class="field">
          <label>SPP (Rp)</label>
          <InputNumber
            v-model="(form.spp_nominal as unknown as number)"
            :min="0"
            fluid
          />
        </div>
        <div class="field">
          <label>Nama Ayah</label>
          <InputText v-model="form.nama_ayah as string" fluid />
        </div>
        <div class="field">
          <label>Kontak Ayah</label>
          <InputText v-model="form.kontak_ayah as string" fluid />
        </div>
        <div class="field">
          <label>Nama Ibu</label>
          <InputText v-model="form.nama_ibu as string" fluid />
        </div>
        <div class="field">
          <label>Kontak Ibu</label>
          <InputText v-model="form.kontak_ibu as string" fluid />
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
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.field label {
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
