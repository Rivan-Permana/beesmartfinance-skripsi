<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import ToggleSwitch from "primevue/toggleswitch"
import Tag from "primevue/tag"
import Textarea from "primevue/textarea"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { pegawaiApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { useAuthStore } from "@/stores/auth"
import type { Pegawai } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Pegawai[]>([])
const loading = ref(false)
const canWrite = computed(() => auth.hasRole(["Finance"]))

async function load() {
  loading.value = true
  try {
    const data = await pegawaiApi.list()
    rows.value = data.results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data pegawai.")
  } finally {
    loading.value = false
  }
}

const dialog = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<Pegawai>>({})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    nip: "", nama: "", jabatan: "", nomor_hp: "", alamat: "", status_aktif: true,
  })
  dialog.value = true
}
function openEdit(row: Pegawai) {
  editingId.value = row.id
  Object.assign(form, { ...row })
  dialog.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingId.value) {
      await pegawaiApi.update(editingId.value, form)
      notifySuccess(toast, "Data pegawai diperbarui")
    } else {
      await pegawaiApi.create(form)
      notifySuccess(toast, "Pegawai ditambahkan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan data pegawai.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: Pegawai) {
  confirm.require({
    message: `Hapus data pegawai "${row.nama}"?`,
    header: "Konfirmasi",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await pegawaiApi.remove(row.id)
        notifySuccess(toast, "Pegawai dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus pegawai.")
      }
    },
  })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Pegawai</h1>
      <Button v-if="canWrite" label="Tambah Pegawai" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada data pegawai.</template>
      <Column field="nip" header="NIP" />
      <Column field="nama" header="Nama" />
      <Column field="jabatan" header="Jabatan" />
      <Column field="nomor_hp" header="No. HP" />
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status_aktif ? 'Aktif' : 'Non-aktif'"
            :severity="data.status_aktif ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="Aksi" style="width: 8rem">
        <template #body="{ data }">
          <Button
            v-if="canWrite"
            icon="pi pi-pencil"
            text
            rounded
            aria-label="Edit"
            @click="openEdit(data)"
          />
          <Button
            v-if="canWrite"
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
      :header="editingId ? 'Edit Pegawai' : 'Tambah Pegawai'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="form-grid">
        <div class="field">
          <label>NIP</label>
          <InputText v-model="form.nip as string" fluid />
        </div>
        <div class="field">
          <label>Nama *</label>
          <InputText v-model="form.nama" fluid />
        </div>
        <div class="field">
          <label>Jabatan</label>
          <InputText v-model="form.jabatan as string" fluid />
        </div>
        <div class="field">
          <label>No. HP</label>
          <InputText v-model="form.nomor_hp as string" fluid />
        </div>
        <div class="field span2">
          <label>Alamat</label>
          <Textarea v-model="form.alamat as string" rows="2" auto-resize fluid />
        </div>
        <div class="field span2 inline">
          <label>Pegawai aktif</label>
          <ToggleSwitch v-model="form.status_aktif" />
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
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;
}
.form-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem;
}
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field.inline { flex-direction: row; align-items: center; gap: 0.75rem; }
.field label { font-weight: 600; font-size: 0.85rem; }
</style>
