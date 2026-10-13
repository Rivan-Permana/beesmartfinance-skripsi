<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Select from "primevue/select"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { asetApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { coaApi } from "@/features/jurnal/api"
import {
  filterCoaAsetTetap,
  filterCoaBebanPenyusutan,
} from "@/features/coa/filters"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Coa, FixedAsset } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<FixedAsset[]>([])
const coaList = ref<Coa[]>([])
const coaAsetOptions = computed(() => filterCoaAsetTetap(coaList.value))
const coaAkumulasiOptions = computed(() => filterCoaAsetTetap(coaList.value))
const coaBebanDeprOptions = computed(() => filterCoaBebanPenyusutan(coaList.value))
const loading = ref(false)
const canWrite = computed(() => auth.hasRole(["Finance"]))

function rp(v: string | number | null | undefined) {
  return formatRp(v)
}

async function load() {
  loading.value = true
  try {
    rows.value = (await asetApi.list()).results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data aset.")
  } finally {
    loading.value = false
  }
}

const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<{
  nama: string
  akun_aset: string | null
  akun_akumulasi: string | null
  akun_beban_depr: string | null
  tanggal_perolehan: Date
  harga_perolehan: number
  umur_manfaat_bulan: number
}>({
  nama: "",
  akun_aset: null,
  akun_akumulasi: null,
  akun_beban_depr: null,
  tanggal_perolehan: new Date(),
  harga_perolehan: 0,
  umur_manfaat_bulan: 12,
})

function openCreate() {
  editingId.value = null
  form.nama = ""
  form.akun_aset = null
  form.akun_akumulasi = null
  form.akun_beban_depr = null
  form.tanggal_perolehan = new Date()
  form.harga_perolehan = 0
  form.umur_manfaat_bulan = 12
  dialog.value = true
}

function openEdit(a: FixedAsset) {
  editingId.value = a.id
  form.nama = a.nama
  form.akun_aset = a.akun_aset
  form.akun_akumulasi = a.akun_akumulasi
  form.akun_beban_depr = a.akun_beban_depr
  form.tanggal_perolehan = new Date(a.tanggal_perolehan + "T12:00:00")
  form.harga_perolehan = Number(a.harga_perolehan)
  form.umur_manfaat_bulan = a.umur_manfaat_bulan
  dialog.value = true
}

const canDelete = (a: FixedAsset) => Number(a.akumulasi_penyusutan) === 0

async function save() {
  saving.value = true
  try {
    const payload = {
      nama: form.nama,
      akun_aset: form.akun_aset as string,
      akun_akumulasi: form.akun_akumulasi as string,
      akun_beban_depr: form.akun_beban_depr as string,
      tanggal_perolehan: form.tanggal_perolehan.toISOString().slice(0, 10),
      harga_perolehan: String(form.harga_perolehan),
      umur_manfaat_bulan: form.umur_manfaat_bulan,
    }
    if (editingId.value) {
      await asetApi.update(editingId.value, payload)
      notifySuccess(toast, "Aset diperbarui")
    } else {
      await asetApi.create(payload)
      notifySuccess(toast, "Aset tetap ditambahkan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan data aset.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(a: FixedAsset) {
  confirm.require({
    message: `Hapus aset "${a.nama}"? Hanya aset tanpa riwayat penyusutan.`,
    header: "Konfirmasi Hapus",
    icon: "pi pi-trash",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await asetApi.remove(a.id)
        notifySuccess(toast, "Aset dihapus.")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus aset.")
      }
    },
  })
}

const formValid = computed(
  () =>
    form.nama.trim() !== "" &&
    !!form.akun_aset &&
    !!form.akun_akumulasi &&
    !!form.akun_beban_depr &&
    form.harga_perolehan > 0 &&
    form.umur_manfaat_bulan > 0,
)

function susutkan(a: FixedAsset) {
  confirm.require({
    message: `Catat penyusutan ${a.nama} sebesar ${rp(a.penyusutan_per_bulan)} bulan ini? Jurnal beban penyusutan akan dibuat otomatis.`,
    header: "Konfirmasi Penyusutan",
    icon: "pi pi-chart-bar",
    rejectLabel: "Batal",
    acceptLabel: "Catat Penyusutan",
    accept: async () => {
      try {
        const res = await asetApi.susutkan(a.id)
        notifySuccess(toast, "Penyusutan tercatat", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal mencatat penyusutan.")
      }
    },
  })
}

onMounted(async () => {
  await load()
  try {
    coaList.value = await coaApi.list()
  } catch {
    /* dropdown akun kosong jika gagal */
  }
})
</script>

<template>
  <PageLayout title="Aset Tetap" subtitle="Catat aset dan jalankan penyusutan bulanan">
    <template #actions>
      <Button v-if="canWrite" label="Tambah Aset" icon="pi pi-plus" @click="openCreate" />
    </template>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada aset tetap.</template>
      <Column field="nama" header="Nama Aset" />
      <Column field="tanggal_perolehan" header="Diperoleh" />
      <Column header="Harga"><template #body="{ data }">{{ rp(data.harga_perolehan) }}</template></Column>
      <Column header="Umur">
        <template #body="{ data }">{{ data.umur_manfaat_bulan }} bln</template>
      </Column>
      <Column header="Akumulasi"><template #body="{ data }">{{ rp(data.akumulasi_penyusutan) }}</template></Column>
      <Column header="Penyusutan / bulan"><template #body="{ data }">{{ rp(data.penyusutan_per_bulan) }}</template></Column>
      <Column header="Aksi" headerClass="bee-col-actions--md" bodyClass="bee-col-actions--md">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button
              v-if="canWrite"
              icon="pi pi-pencil"
              text
              rounded
              aria-label="Edit aset"
              @click="openEdit(data)"
            />
            <Button
              v-if="canWrite"
              label="Susutkan"
              size="small"
              text
              @click="susutkan(data)"
            />
            <Button
              v-if="canWrite && canDelete(data)"
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              aria-label="Hapus aset"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Aset Tetap' : 'Tambah Aset Tetap'"
      modal
      :style="{ width: '34rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Nama Aset *</label>
          <InputText v-model="form.nama" fluid />
        </div>
        <div class="field">
          <label>Tanggal Perolehan</label>
          <DatePicker v-model="form.tanggal_perolehan" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field">
          <label>Harga Perolehan</label>
          <InputNumber v-model="form.harga_perolehan" :min="0" fluid />
        </div>
        <div class="field">
          <label>Umur Manfaat (bulan)</label>
          <InputNumber v-model="form.umur_manfaat_bulan" :min="1" fluid />
        </div>
        <div class="field">
          <label>Akun Aset *</label>
          <Select v-model="form.akun_aset" :options="coaAsetOptions" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih" fluid />
        </div>
        <div class="field">
          <label>Akun Akumulasi *</label>
          <Select v-model="form.akun_akumulasi" :options="coaAkumulasiOptions" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih" fluid />
        </div>
        <div class="field">
          <label>Akun Beban Penyusutan *</label>
          <Select v-model="form.akun_beban_depr" :options="coaBebanDeprOptions" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih" fluid />
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
.field label { font-weight: 600; font-size: 0.85rem; }
</style>
