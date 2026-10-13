<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import DatePicker from "primevue/datepicker"
import InputText from "primevue/inputtext"
import ToggleSwitch from "primevue/toggleswitch"
import Tag from "primevue/tag"
import Textarea from "primevue/textarea"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { pegawaiApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Pegawai } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Pegawai[]>([])
const loading = ref(false)
const canWrite = computed(() => auth.hasRole(["Administration", "Finance"]))

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
    tanggal_mulai_kerja: null, tanggal_selesai_kerja: null,
  })
  dialog.value = true
}
function openEdit(row: Pegawai) {
  editingId.value = row.id
  Object.assign(form, {
    ...row,
    tanggal_mulai_kerja: row.tanggal_mulai_kerja ? new Date(row.tanggal_mulai_kerja) : null,
    tanggal_selesai_kerja: row.tanggal_selesai_kerja ? new Date(row.tanggal_selesai_kerja) : null,
  })
  dialog.value = true
}

function fmtDate(d: Date | null | undefined) {
  if (!d) return null
  return d.toISOString().slice(0, 10)
}

async function save() {
  saving.value = true
  const payload = {
    ...form,
    tanggal_mulai_kerja: fmtDate(form.tanggal_mulai_kerja as unknown as Date),
    tanggal_selesai_kerja: fmtDate(form.tanggal_selesai_kerja as unknown as Date),
  }
  try {
    if (editingId.value) {
      await pegawaiApi.update(editingId.value, payload)
      notifySuccess(toast, "Data pegawai diperbarui")
    } else {
      await pegawaiApi.create(payload)
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
  <PageLayout title="Data Pegawai" subtitle="Kelola pegawai aktif sekolah">
    <template #actions>
      <Button v-if="canWrite" label="Tambah Pegawai" icon="pi pi-plus" @click="openCreate" />
    </template>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada data pegawai.</template>
      <Column field="nip" header="NIP" />
      <Column field="nama" header="Nama" />
      <Column field="jabatan" header="Jabatan" />
      <Column header="Periode Kerja">
        <template #body="{ data }">
          <span v-if="data.tanggal_mulai_kerja" class="periode">
            {{ data.tanggal_mulai_kerja }}
            <template v-if="data.tanggal_selesai_kerja"> — {{ data.tanggal_selesai_kerja }}</template>
          </span>
          <span v-else class="muted">—</span>
        </template>
      </Column>
      <Column field="nomor_hp" header="No. HP" />
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status_aktif ? 'Aktif' : 'Non-aktif'"
            :severity="data.status_aktif ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
        <template #body="{ data }">
          <div v-if="canWrite" class="bee-actions">
            <Button
              icon="pi pi-pencil"
              text
              aria-label="Edit"
              @click="openEdit(data)"
            />
            <Button
              icon="pi pi-trash"
              text
              severity="danger"
              aria-label="Hapus"
              @click="confirmDelete(data)"
            />
          </div>
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
        <div class="field">
          <label>Mulai kerja</label>
          <DatePicker v-model="form.tanggal_mulai_kerja as unknown as Date" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field">
          <label>Selesai kerja</label>
          <DatePicker v-model="form.tanggal_selesai_kerja as unknown as Date" date-format="yy-mm-dd" fluid />
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
  </PageLayout>
</template>

<style scoped>
.form-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem;
}
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field.inline { flex-direction: row; align-items: center; gap: 0.75rem; }
.field label { font-weight: 600; font-size: 0.85rem; }
.muted { color: var(--app-text-muted); font-size: 0.85rem; }
.periode { font-size: 0.85rem; }
</style>
