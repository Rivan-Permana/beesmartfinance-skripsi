<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { onMounted, reactive, ref } from "vue"

import { kelompokApi } from "@/features/absensi/api"
import { siswaApi } from "./api"
import { formatRp } from "@/core/format"
import { notifyError, notifySuccess } from "@/core/errors"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Kelompok, Siswa, SiswaStatus } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const rows = ref<Siswa[]>([])
const kelompokList = ref<Kelompok[]>([])
const loading = ref(false)

const kelompokMap = () => {
  const m = new Map<number, string>()
  kelompokList.value.forEach((k) => {
    m.set(k.id, `${k.jenjang_kode ?? ""} · ${k.nama}`.trim())
  })
  return m
}

/** Kolom yang tampil di tabel — jangan sertakan field tersembunyi (mis. nama ibu). */
const { query: search, filtered: filteredRows } = useTableSearch(rows, (row) => [
  row.nis,
  row.nama,
  row.status,
  formatRp(row.spp_nominal),
])

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
    const [data, kelompok] = await Promise.all([
      siswaApi.listAll(),
      kelompokApi.list(),
    ])
    rows.value = data
    kelompokList.value = kelompok
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
    nis: "", nama: "", status: "aktif", spp_nominal: "0", kelompok: null,
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
  <PageLayout title="Data Siswa" subtitle="Kelola siswa aktif PG/TK">
    <Message severity="info" :closable="false" class="mb">
      Untuk mengatur jenjang/kelompok atau pindah banyak siswa sekaligus, buka menu <strong>Kelompok</strong>.
    </Message>
    <template #actions>
      <Button label="Tambah Siswa" icon="pi pi-plus" @click="openCreate" />
    </template>
    <template #filters>
      <SearchField
        v-model="search"
        hint="Cari NIS, nama, status, atau SPP (kolom di tabel)"
      />
    </template>

    <DataTable
      :value="filteredRows"
      :loading="loading"
      paginator
      :rows="10"
      data-key="id"
      striped-rows
    >
      <template #empty>
        <EmptyState
          message="Belum ada data siswa."
          action-label="Tambah Siswa"
          @action="openCreate"
        />
      </template>
      <Column field="nis" header="NIS" />
      <Column field="nama" header="Nama" />
      <Column header="Kelompok">
        <template #body="{ data }">
          {{ data.kelompok ? kelompokMap().get(data.kelompok) ?? "—" : "—" }}
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status"
            :severity="statusSeverity[data.status as SiswaStatus]"
          />
        </template>
      </Column>
      <Column header="SPP">
        <template #body="{ data }">
          <span class="tabular-nums">{{ formatRp(data.spp_nominal) }}</span>
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
        <template #body="{ data }">
          <div class="bee-actions">
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
          <label>Kelompok</label>
          <Select
            v-model="form.kelompok"
            :options="kelompokList"
            option-label="nama"
            option-value="id"
            placeholder="Pilih kelompok"
            show-clear
            filter
            fluid
          >
            <template #option="{ option }">
              {{ option.jenjang_kode }} · {{ option.nama }}
            </template>
          </Select>
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
  </PageLayout>
</template>

<style scoped>
.mb { margin-bottom: 1rem; }
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
</style>
