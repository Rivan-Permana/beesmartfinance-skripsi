<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import MultiSelect from "primevue/multiselect"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"

import { jenjangApi, kelompokApi } from "@/features/absensi/api"
import { siswaApi } from "@/features/siswa/api"
import { notifyError, notifySuccess } from "@/core/errors"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import type { Jenjang, Kelompok, Siswa } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()
const tab = ref("kelompok")
const loading = ref(false)

const jenjangList = ref<Jenjang[]>([])
const kelompokList = ref<Kelompok[]>([])
const filterJenjang = ref<number | null>(null)

// --- jenjang dialog ---
const jenjangDialog = ref(false)
const jenjangSaving = ref(false)
const jenjangEditingId = ref<number | null>(null)
const jenjangForm = reactive({ kode: "", nama: "" })

// --- kelompok dialog ---
const kelompokDialog = ref(false)
const kelompokSaving = ref(false)
const kelompokEditingId = ref<number | null>(null)
const kelompokForm = reactive({ nama: "", jenjang: null as number | null })

// --- pindah siswa ---
const dariKelompok = ref<number | null>(null)
const keKelompok = ref<number | null>(null)
const siswaDari = ref<Siswa[]>([])
const selectedSiswa = ref<Siswa[]>([])
const pindahLoading = ref(false)

const filteredKelompok = computed(() => {
  if (!filterJenjang.value) return kelompokList.value
  return kelompokList.value.filter((k) => k.jenjang === filterJenjang.value)
})

const jenjangOptions = computed(() =>
  jenjangList.value.map((j) => ({ label: `${j.kode} — ${j.nama}`, value: j.id })),
)

const kelompokOptions = computed(() =>
  kelompokList.value.map((k) => ({
    label: `${k.jenjang_kode ?? "?"} · ${k.nama}`,
    value: k.id,
  })),
)

async function loadAll() {
  loading.value = true
  try {
    const [j, k] = await Promise.all([jenjangApi.list(), kelompokApi.list()])
    jenjangList.value = j
    kelompokList.value = k
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data jenjang/kelompok.")
  } finally {
    loading.value = false
  }
}

function openJenjangCreate() {
  jenjangEditingId.value = null
  jenjangForm.kode = ""
  jenjangForm.nama = ""
  jenjangDialog.value = true
}

function openJenjangEdit(row: Jenjang) {
  jenjangEditingId.value = row.id
  jenjangForm.kode = row.kode
  jenjangForm.nama = row.nama
  jenjangDialog.value = true
}

async function saveJenjang() {
  jenjangSaving.value = true
  try {
    if (jenjangEditingId.value) {
      await jenjangApi.update(jenjangEditingId.value, { ...jenjangForm })
      notifySuccess(toast, "Jenjang diperbarui")
    } else {
      await jenjangApi.create({ ...jenjangForm })
      notifySuccess(toast, "Jenjang ditambahkan")
    }
    jenjangDialog.value = false
    await loadAll()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan jenjang.")
  } finally {
    jenjangSaving.value = false
  }
}

function confirmRemoveJenjang(row: Jenjang) {
  confirm.require({
    message: `Hapus jenjang ${row.kode}?`,
    header: "Konfirmasi",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await jenjangApi.remove(row.id)
        notifySuccess(toast, "Jenjang dihapus")
        await loadAll()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus jenjang.")
      }
    },
  })
}

function openKelompokCreate() {
  kelompokEditingId.value = null
  kelompokForm.nama = ""
  kelompokForm.jenjang = filterJenjang.value ?? jenjangList.value[0]?.id ?? null
  kelompokDialog.value = true
}

function openKelompokEdit(row: Kelompok) {
  kelompokEditingId.value = row.id
  kelompokForm.nama = row.nama
  kelompokForm.jenjang = row.jenjang
  kelompokDialog.value = true
}

async function saveKelompok() {
  if (!kelompokForm.jenjang) return
  kelompokSaving.value = true
  try {
    const payload = { nama: kelompokForm.nama, jenjang: kelompokForm.jenjang }
    if (kelompokEditingId.value) {
      await kelompokApi.update(kelompokEditingId.value, payload)
      notifySuccess(toast, "Kelompok diperbarui")
    } else {
      await kelompokApi.create(payload)
      notifySuccess(toast, "Kelompok ditambahkan")
    }
    kelompokDialog.value = false
    await loadAll()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan kelompok.")
  } finally {
    kelompokSaving.value = false
  }
}

function confirmRemoveKelompok(row: Kelompok) {
  confirm.require({
    message: `Hapus kelompok ${row.nama}?`,
    header: "Konfirmasi",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await kelompokApi.remove(row.id)
        notifySuccess(toast, "Kelompok dihapus")
        await loadAll()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus kelompok.")
      }
    },
  })
}

async function loadSiswaDari() {
  selectedSiswa.value = []
  if (!dariKelompok.value) {
    siswaDari.value = []
    return
  }
  pindahLoading.value = true
  try {
    siswaDari.value = await siswaApi.listAll({
      kelompok: dariKelompok.value,
      status: "aktif",
    })
  } catch (e) {
    notifyError(toast, e, "Gagal memuat siswa.")
  } finally {
    pindahLoading.value = false
  }
}

watch(dariKelompok, loadSiswaDari)

async function pindahSiswa() {
  if (!keKelompok.value || selectedSiswa.value.length === 0) return
  pindahLoading.value = true
  try {
    const res = await kelompokApi.pindahSiswa(
      keKelompok.value,
      selectedSiswa.value.map((s) => s.id),
    )
    notifySuccess(toast, "Siswa dipindah", { detail: res.detail })
    selectedSiswa.value = []
    await loadSiswaDari()
    await loadAll()
  } catch (e) {
    notifyError(toast, e, "Gagal memindahkan siswa.")
  } finally {
    pindahLoading.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <PageLayout
    title="Pengelolaan Kelompok"
    subtitle="Atur jenjang, kelompok kelas, dan pindah siswa antar kelompok"
  >
    <Message severity="info" :closable="false" class="mb">
      <strong>Jenjang</strong> = tingkat (PG, TKA, TKB).
      <strong>Kelompok</strong> = rombel di dalam jenjang.
      Pindahkan siswa saat naik kelas atau pindah rombel — absensi & tagihan mengikuti kelompok baru.
    </Message>

    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="jenjang">Jenjang ({{ jenjangList.length }})</Tab>
        <Tab value="kelompok">Kelompok ({{ kelompokList.length }})</Tab>
        <Tab value="pindah">Pindah Siswa</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="jenjang">
          <div class="tab-actions">
            <Button label="Tambah Jenjang" icon="pi pi-plus" size="small" @click="openJenjangCreate" />
          </div>
          <DataTable :value="jenjangList" :loading="loading" data-key="id" striped-rows paginator :rows="10">
            <Column field="kode" header="Kode" sortable />
            <Column field="nama" header="Nama" sortable />
            <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text rounded aria-label="Edit jenjang" @click="openJenjangEdit(data)" />
                  <Button icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus jenjang" @click="confirmRemoveJenjang(data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="kelompok">
          <div class="tab-actions">
            <Select
              v-model="filterJenjang"
              :options="[{ label: 'Semua jenjang', value: null }, ...jenjangOptions]"
              option-label="label"
              option-value="value"
              placeholder="Filter jenjang"
              show-clear
            />
            <Button label="Tambah Kelompok" icon="pi pi-plus" size="small" @click="openKelompokCreate" />
          </div>
          <DataTable :value="filteredKelompok" :loading="loading" data-key="id" striped-rows paginator :rows="12">
            <Column header="Jenjang">
              <template #body="{ data }">{{ data.jenjang_kode }}</template>
            </Column>
            <Column field="nama" header="Kelompok" sortable />
            <Column header="Siswa aktif">
              <template #body="{ data }">{{ data.siswa_aktif ?? 0 }}</template>
            </Column>
            <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text rounded aria-label="Edit kelompok" @click="openKelompokEdit(data)" />
                  <Button icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus kelompok" @click="confirmRemoveKelompok(data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="pindah">
          <div class="pindah-form">
            <div class="field">
              <label>Dari kelompok</label>
              <Select
                v-model="dariKelompok"
                :options="kelompokOptions"
                option-label="label"
                option-value="value"
                placeholder="Pilih kelompok asal"
                filter
                fluid
              />
            </div>
            <div class="field">
              <label>Siswa yang dipindah</label>
              <MultiSelect
                v-model="selectedSiswa"
                :options="siswaDari"
                option-label="nama"
                placeholder="Pilih siswa"
                filter
                fluid
                :loading="pindahLoading"
                :disabled="!dariKelompok"
              />
            </div>
            <div class="field">
              <label>Ke kelompok</label>
              <Select
                v-model="keKelompok"
                :options="kelompokOptions.filter((o) => o.value !== dariKelompok)"
                option-label="label"
                option-value="value"
                placeholder="Pilih kelompok tujuan"
                filter
                fluid
              />
            </div>
            <Button
              label="Pindahkan"
              icon="pi pi-arrow-right"
              :loading="pindahLoading"
              :disabled="!keKelompok || selectedSiswa.length === 0"
              @click="pindahSiswa"
            />
          </div>
          <EmptyState
            v-if="dariKelompok && !pindahLoading && siswaDari.length === 0"
            message="Tidak ada siswa aktif di kelompok ini."
          />
        </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog v-model:visible="jenjangDialog" :header="jenjangEditingId ? 'Edit Jenjang' : 'Tambah Jenjang'" modal>
      <div class="form">
        <div class="field">
          <label>Kode *</label>
          <InputText v-model="jenjangForm.kode" :disabled="!!jenjangEditingId" fluid />
        </div>
        <div class="field">
          <label>Nama *</label>
          <InputText v-model="jenjangForm.nama" fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" text severity="secondary" @click="jenjangDialog = false" />
        <Button label="Simpan" :loading="jenjangSaving" @click="saveJenjang" />
      </template>
    </Dialog>

    <Dialog v-model:visible="kelompokDialog" :header="kelompokEditingId ? 'Edit Kelompok' : 'Tambah Kelompok'" modal>
      <div class="form">
        <div class="field">
          <label>Jenjang *</label>
          <Select v-model="kelompokForm.jenjang" :options="jenjangOptions" option-label="label" option-value="value" fluid />
        </div>
        <div class="field">
          <label>Nama kelompok *</label>
          <InputText v-model="kelompokForm.nama" fluid placeholder="Contoh: TKA Melati" />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" text severity="secondary" @click="kelompokDialog = false" />
        <Button label="Simpan" :loading="kelompokSaving" @click="saveKelompok" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.mb { margin-bottom: 1rem; }
.tab-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.pindah-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 28rem;
}
.form, .field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.field label { font-weight: 600; font-size: 0.85rem; }
</style>
