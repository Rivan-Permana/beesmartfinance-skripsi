<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { coaManageApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Coa, Golongan, SubGolongan } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()
const canWrite = computed(() => auth.hasRole(["Finance"]))
const isPrincipal = computed(() => auth.hasRole(["SchoolPrincipal"]))

const tab = ref("akun")
const loading = ref(false)

const golongan = ref<Golongan[]>([])
const subGolongan = ref<SubGolongan[]>([])
const akun = ref<Coa[]>([])

const golonganMap = computed(() => {
  const m = new Map<number, Golongan>()
  golongan.value.forEach((g) => m.set(g.id, g))
  return m
})

const subMap = computed(() => {
  const m = new Map<string, SubGolongan>()
  subGolongan.value.forEach((s) => m.set(s.kode_sub, s))
  return m
})

async function loadAll() {
  loading.value = true
  try {
    const [g, s, a] = await Promise.all([
      coaManageApi.listGolongan(),
      coaManageApi.listSubGolongan(),
      coaManageApi.listCoa(),
    ])
    golongan.value = g
    subGolongan.value = s
    akun.value = a.sort((x, y) => x.kode_akun.localeCompare(y.kode_akun))
  } catch (e) {
    notifyError(toast, e, "Gagal memuat chart of accounts.")
  } finally {
    loading.value = false
  }
}

// --- dialogs ---
const dialog = ref(false)
const dialogKind = ref<"golongan" | "sub" | "akun">("akun")
const saving = ref(false)
const editingKey = ref<string | number | null>(null)

const formGolongan = reactive({ kode_golongan: "", nama_golongan: "", deskripsi: "" })
const formSub = reactive({ golongan: null as number | null, kode_sub: "", nama_sub: "" })
const formAkun = reactive({
  kode_akun: "",
  sub_golongan: null as string | null,
  nama_akun: "",
  posisi_normal: "D" as "D" | "K",
  is_active: true,
})

const POSISI_OPTS = [
  { label: "Debit (D)", value: "D" },
  { label: "Kredit (K)", value: "K" },
]

function openCreate(kind: typeof dialogKind.value) {
  dialogKind.value = kind
  editingKey.value = null
  if (kind === "golongan") {
    formGolongan.kode_golongan = ""
    formGolongan.nama_golongan = ""
    formGolongan.deskripsi = ""
  } else if (kind === "sub") {
    formSub.golongan = golongan.value[0]?.id ?? null
    formSub.kode_sub = ""
    formSub.nama_sub = ""
  } else {
    formAkun.kode_akun = ""
    formAkun.sub_golongan = subGolongan.value[0]?.kode_sub ?? null
    formAkun.nama_akun = ""
    formAkun.posisi_normal = "D"
    formAkun.is_active = true
  }
  dialog.value = true
}

function openEditGolongan(row: Golongan) {
  dialogKind.value = "golongan"
  editingKey.value = row.id
  formGolongan.kode_golongan = row.kode_golongan
  formGolongan.nama_golongan = row.nama_golongan
  formGolongan.deskripsi = row.deskripsi ?? ""
  dialog.value = true
}

function openEditSub(row: SubGolongan) {
  dialogKind.value = "sub"
  editingKey.value = row.id
  formSub.golongan = row.golongan
  formSub.kode_sub = row.kode_sub
  formSub.nama_sub = row.nama_sub
  dialog.value = true
}

function openEditAkun(row: Coa) {
  dialogKind.value = "akun"
  editingKey.value = row.kode_akun
  formAkun.kode_akun = row.kode_akun
  formAkun.sub_golongan = row.sub_golongan
  formAkun.nama_akun = row.nama_akun
  formAkun.posisi_normal = row.posisi_normal
  formAkun.is_active = row.is_active
  dialog.value = true
}

async function save() {
  saving.value = true
  try {
    if (dialogKind.value === "golongan") {
      const payload = { ...formGolongan, deskripsi: formGolongan.deskripsi || null }
      if (editingKey.value) {
        await coaManageApi.updateGolongan(editingKey.value as number, payload)
      } else {
        await coaManageApi.createGolongan(payload)
      }
    } else if (dialogKind.value === "sub") {
      const payload = { golongan: formSub.golongan!, kode_sub: formSub.kode_sub, nama_sub: formSub.nama_sub }
      if (editingKey.value) {
        await coaManageApi.updateSubGolongan(editingKey.value as number, payload)
      } else {
        await coaManageApi.createSubGolongan(payload)
      }
    } else {
      const payload = { ...formAkun }
      if (editingKey.value) {
        await coaManageApi.updateCoa(editingKey.value as string, payload)
      } else {
        await coaManageApi.createCoa(payload)
      }
    }
    notifySuccess(toast, "Data disimpan")
    dialog.value = false
    await loadAll()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan.")
  } finally {
    saving.value = false
  }
}

function confirmRemove(kind: "golongan" | "sub" | "akun", key: string | number, label: string) {
  confirm.require({
    message: `Hapus ${label}?`,
    header: "Konfirmasi",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        if (kind === "golongan") await coaManageApi.removeGolongan(key as number)
        else if (kind === "sub") await coaManageApi.removeSubGolongan(key as number)
        else await coaManageApi.removeCoa(key as string)
        notifySuccess(toast, "Dihapus")
        await loadAll()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus.")
      }
    },
  })
}

function golLabel(kode: string) {
  return subMap.value.get(kode)?.nama_sub ?? kode
}

onMounted(loadAll)
</script>

<template>
  <PageLayout title="Chart of Accounts" subtitle="Kelola golongan, sub-golongan, dan akun">
    <Message v-if="canWrite" severity="info" :closable="false" class="mb">
      <strong>Daftar Akun (COA)</strong> — akun akuntansi sekolah.
      Tambah atau ubah di sini jika ada akun operasional baru.
      Untuk menghapus, pastikan akun belum dipakai di jurnal.
    </Message>
    <Message v-else-if="isPrincipal" severity="info" :closable="false" class="mb">
      <strong>Mode lihat saja.</strong> Daftar akun untuk monitoring Kepala Sekolah.
      Perubahan akun dilakukan oleh <strong>Staff Keuangan</strong>.
    </Message>
    <Message v-else severity="info" :closable="false" class="mb">
      Daftar akun akuntansi sekolah — hanya untuk referensi.
    </Message>

    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="akun">Akun ({{ akun.length }})</Tab>
        <Tab value="sub">Sub-golongan</Tab>
        <Tab value="gol">Golongan</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="akun">
          <div class="tab-actions">
            <Button v-if="canWrite" label="Tambah Akun" icon="pi pi-plus" size="small" @click="openCreate('akun')" />
          </div>
          <DataTable :value="akun" :loading="loading" paginator :rows="15" data-key="kode_akun" striped-rows>
            <Column field="kode_akun" header="Kode" sortable />
            <Column field="nama_akun" header="Nama Akun" />
            <Column header="Sub-golongan">
              <template #body="{ data }">{{ data.sub_golongan ? golLabel(data.sub_golongan) : "—" }}</template>
            </Column>
            <Column header="Posisi">
              <template #body="{ data }">
                <Tag :value="data.posisi_normal === 'D' ? 'Debit' : 'Kredit'" severity="secondary" />
              </template>
            </Column>
            <Column header="Aktif">
              <template #body="{ data }">
                <Tag :value="data.is_active ? 'Aktif' : 'Nonaktif'" :severity="data.is_active ? 'success' : 'warn'" />
              </template>
            </Column>
            <Column v-if="canWrite" header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text rounded aria-label="Edit akun" @click="openEditAkun(data)" />
                  <Button icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus akun" @click="confirmRemove('akun', data.kode_akun, data.nama_akun)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="sub">
          <div class="tab-actions">
            <Button v-if="canWrite" label="Tambah Sub-golongan" icon="pi pi-plus" size="small" @click="openCreate('sub')" />
          </div>
          <DataTable :value="subGolongan" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
            <Column field="kode_sub" header="Kode" />
            <Column field="nama_sub" header="Nama" />
            <Column header="Golongan">
              <template #body="{ data }">{{ golonganMap.get(data.golongan)?.nama_golongan ?? data.golongan }}</template>
            </Column>
            <Column v-if="canWrite" header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text rounded aria-label="Edit sub-golongan" @click="openEditSub(data)" />
                  <Button icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus sub-golongan" @click="confirmRemove('sub', data.id, data.nama_sub)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="gol">
          <div class="tab-actions">
            <Button v-if="canWrite" label="Tambah Golongan" icon="pi pi-plus" size="small" @click="openCreate('golongan')" />
          </div>
          <DataTable :value="golongan" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
            <Column field="kode_golongan" header="Kode" />
            <Column field="nama_golongan" header="Nama" />
            <Column field="deskripsi" header="Deskripsi" />
            <Column v-if="canWrite" header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text rounded aria-label="Edit golongan" @click="openEditGolongan(data)" />
                  <Button icon="pi pi-trash" text rounded severity="danger" aria-label="Hapus golongan" @click="confirmRemove('golongan', data.id, data.nama_golongan)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog
      v-model:visible="dialog"
      :header="dialogKind === 'akun' ? (editingKey ? 'Edit Akun' : 'Tambah Akun') : dialogKind === 'sub' ? 'Sub-golongan' : 'Golongan'"
      modal
      :style="{ width: '32rem' }"
    >
      <div v-if="dialogKind === 'golongan'" class="form">
        <div class="field"><label>Kode *</label><InputText v-model="formGolongan.kode_golongan" :disabled="!!editingKey" fluid /></div>
        <div class="field"><label>Nama *</label><InputText v-model="formGolongan.nama_golongan" fluid /></div>
        <div class="field"><label>Deskripsi</label><InputText v-model="formGolongan.deskripsi" fluid /></div>
      </div>
      <div v-else-if="dialogKind === 'sub'" class="form">
        <div class="field">
          <label>Golongan *</label>
          <Select v-model="formSub.golongan" :options="golongan" option-label="nama_golongan" option-value="id" fluid />
        </div>
        <div class="field"><label>Kode Sub *</label><InputText v-model="formSub.kode_sub" :disabled="!!editingKey" fluid /></div>
        <div class="field"><label>Nama *</label><InputText v-model="formSub.nama_sub" fluid /></div>
      </div>
      <div v-else class="form">
        <div class="field"><label>Kode Akun *</label><InputText v-model="formAkun.kode_akun" :disabled="!!editingKey" fluid /></div>
        <div class="field">
          <label>Sub-golongan</label>
          <Select v-model="formAkun.sub_golongan" :options="subGolongan" option-label="nama_sub" option-value="kode_sub" filter fluid />
        </div>
        <div class="field"><label>Nama Akun *</label><InputText v-model="formAkun.nama_akun" fluid /></div>
        <div class="field">
          <label>Posisi Normal</label>
          <Select v-model="formAkun.posisi_normal" :options="POSISI_OPTS" option-label="label" option-value="value" fluid />
        </div>
        <div class="field inline">
          <label>Aktif</label>
          <ToggleSwitch v-model="formAkun.is_active" />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button v-if="canWrite" label="Simpan" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.mb { margin-bottom: 1rem; }
.tab-actions { margin-bottom: 0.75rem; }
.form { display: flex; flex-direction: column; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.inline { flex-direction: row; align-items: center; justify-content: space-between; }
.field label { font-weight: 600; font-size: 0.85rem; }
code { font-size: 0.85em; }
</style>
