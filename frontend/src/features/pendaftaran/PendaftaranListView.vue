<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"
import { useRouter } from "vue-router"

import { pendaftaranSiswaApi } from "./api"
import { jenjangApi } from "@/features/absensi/api"
import { formatRp } from "@/core/format"
import { notifyError, notifySuccess } from "@/core/errors"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Jenjang, PendaftaranSiswa, PendaftaranSiswaStatus } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()
const router = useRouter()

const rows = ref<PendaftaranSiswa[]>([])
const jenjangList = ref<Jenjang[]>([])
const loading = ref(false)
const filterStatus = ref<PendaftaranSiswaStatus | null>(null)

const STATUS_OPTIONS = [
  { label: "Semua status", value: null as PendaftaranSiswaStatus | null },
  { label: "Sit-in / Trial", value: "TRIAL" as const },
  { label: "Terdaftar", value: "REGISTERED" as const },
  { label: "Batal", value: "BATAL" as const },
]

const statusLabel: Record<PendaftaranSiswaStatus, string> = {
  TRIAL: "Sit-in / Trial",
  REGISTERED: "Terdaftar",
  BATAL: "Batal",
}

const statusSeverity: Record<PendaftaranSiswaStatus, string> = {
  TRIAL: "warn",
  REGISTERED: "success",
  BATAL: "danger",
}

const jenjangMap = computed(() => {
  const m = new Map<number, string>()
  jenjangList.value.forEach((j) => m.set(j.id, j.kode))
  return m
})

const filteredRows = computed(() =>
  filterStatus.value ? rows.value.filter((r) => r.status === filterStatus.value) : rows.value,
)

const { query: searchQuery, filtered: displayRows } = useTableSearch(filteredRows, (row) => [
  row.nama_calon,
  row.jenjang ? jenjangMap.value.get(row.jenjang) ?? String(row.jenjang) : "",
  formatDate(row.tanggal_daftar),
  formatRp(row.biaya_sitin),
  formatRp(row.biaya_pendaftaran),
  statusLabel[row.status],
  row.jurnal_sitin ? "jurnal sit-in sudah" : "jurnal sit-in belum",
  row.jurnal_pendaftaran ? "jurnal daftar sudah" : "jurnal daftar belum",
])

function toDateStr(d: Date | null): string {
  if (!d) return new Date().toISOString().slice(0, 10)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

async function load() {
  loading.value = true
  try {
    const [data, jenjangs] = await Promise.all([
      pendaftaranSiswaApi.list(),
      jenjangApi.list(),
    ])
    rows.value = data.results
    jenjangList.value = jenjangs
  } catch (e) {
    notifyError(toast, e, "Gagal memuat pendaftaran siswa.")
  } finally {
    loading.value = false
  }
}

// --- form CRUD ---
const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  nama_calon: "",
  jenjang: null as number | null,
  tanggal_daftar: new Date() as Date | null,
  biaya_sitin: 100_000,
  biaya_pendaftaran: 500_000,
})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    nama_calon: "",
    jenjang: jenjangList.value[0]?.id ?? null,
    tanggal_daftar: new Date(),
    biaya_sitin: 100_000,
    biaya_pendaftaran: 500_000,
  })
  dialog.value = true
}

function openEdit(row: PendaftaranSiswa) {
  editingId.value = row.id
  Object.assign(form, {
    nama_calon: row.nama_calon,
    jenjang: row.jenjang,
    tanggal_daftar: new Date(row.tanggal_daftar + "T00:00:00"),
    biaya_sitin: Number(row.biaya_sitin),
    biaya_pendaftaran: Number(row.biaya_pendaftaran),
  })
  dialog.value = true
}

async function save() {
  if (!form.nama_calon.trim()) return
  saving.value = true
  try {
    const payload = {
      nama_calon: form.nama_calon.trim(),
      jenjang: form.jenjang,
      tanggal_daftar: toDateStr(form.tanggal_daftar),
      biaya_sitin: String(form.biaya_sitin),
      biaya_pendaftaran: String(form.biaya_pendaftaran),
    }
    if (editingId.value) {
      await pendaftaranSiswaApi.update(editingId.value, payload)
      notifySuccess(toast, "Pendaftaran diperbarui.")
    } else {
      await pendaftaranSiswaApi.create(payload)
      notifySuccess(toast, "Calon siswa ditambahkan.", {
        detail: "Status awal: Sit-in / Trial.",
      })
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan pendaftaran.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: PendaftaranSiswa) {
  confirm.require({
    header: "Hapus pendaftaran?",
    message: `Hapus data calon "${row.nama_calon}"?`,
    acceptLabel: "Hapus",
    rejectLabel: "Batal",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await pendaftaranSiswaApi.remove(row.id)
        notifySuccess(toast, "Pendaftaran dihapus.")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus pendaftaran.")
      }
    },
  })
}

function confirmBayarSitin(row: PendaftaranSiswa) {
  confirm.require({
    header: "Bayar Sit-in",
    message: `Catat pembayaran sit-in ${formatRp(row.biaya_sitin)} untuk ${row.nama_calon}? Jurnal DRAFT akan dibuat otomatis.`,
    acceptLabel: "Bayar & Jurnal",
    rejectLabel: "Batal",
    accept: async () => {
      try {
        const res = await pendaftaranSiswaApi.bayarSitin(row.id)
        notifySuccess(toast, "Pembayaran sit-in tercatat.", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal mencatat pembayaran sit-in.")
      }
    },
  })
}

// --- finalisasi ---
const finalDialog = ref(false)
const finalSaving = ref(false)
const finalTarget = ref<PendaftaranSiswa | null>(null)
const sppNominal = ref(400_000)

function openFinalisasi(row: PendaftaranSiswa) {
  finalTarget.value = row
  sppNominal.value = 400_000
  finalDialog.value = true
}

async function runFinalisasi() {
  if (!finalTarget.value) return
  finalSaving.value = true
  try {
    const res = await pendaftaranSiswaApi.finalisasi(
      finalTarget.value.id,
      String(sppNominal.value),
    )
    notifySuccess(toast, `${finalTarget.value.nama_calon} resmi terdaftar sebagai siswa.`, {
      detail: "Jurnal biaya pendaftaran DRAFT dibuat otomatis.",
    })
    finalDialog.value = false
    finalTarget.value = null
    await load()
    if (res.siswa) {
      confirm.require({
        header: "Lanjut ke data siswa?",
        message: "Calon sudah jadi siswa aktif. Buka halaman Data Siswa untuk melengkapi profil?",
        acceptLabel: "Buka Data Siswa",
        rejectLabel: "Nanti",
        accept: () => router.push("/siswa"),
      })
    }
  } catch (e) {
    notifyError(toast, e, "Gagal finalisasi pendaftaran.")
  } finally {
    finalSaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <PageLayout
    title="Pendaftaran Siswa"
    subtitle="Alur sit-in → bayar sit-in → finalisasi menjadi siswa resmi"
  >
    <template #actions>
      <Button label="Daftar Calon Baru" icon="pi pi-user-plus" @click="openCreate" />
    </template>

    <template #filters>
      <SearchField
        v-model="searchQuery"
        hint="Cari nama calon, jenjang, status, biaya"
      />
      <Select
        v-model="filterStatus"
        :options="STATUS_OPTIONS"
        option-label="label"
        option-value="value"
        placeholder="Filter status"
        class="bee-filter-field"
      />
    </template>

    <Message severity="info" :closable="false" class="bee-mb">
      <strong>Alur pendaftaran calon siswa:</strong>
      <ol class="info-steps">
        <li><strong>Daftar calon</strong> — input data calon & biaya sit-in/pendaftaran.</li>
        <li><strong>Bayar sit-in</strong> — catat pembayaran uang percobaan (trial class).</li>
        <li><strong>Finalisasi</strong> — calon resmi jadi siswa + tentukan nominal SPP bulanan.</li>
      </ol>
      Setiap pembayaran otomatis membuat jurnal akuntansi berstatus <strong>DRAFT</strong> (perlu diposting di menu Jurnal).
    </Message>

    <DataTable
      :value="displayRows"
      :loading="loading"
      data-key="id"
      striped-rows
    >
      <template #empty>
        <EmptyState message="Belum ada calon siswa. Klik Daftar Calon Baru untuk memulai." />
      </template>

      <Column field="nama_calon" header="Nama Calon" sortable />
      <Column field="jenjang" header="Jenjang">
        <template #body="{ data }">
          {{ data.jenjang ? jenjangMap.get(data.jenjang) ?? `#${data.jenjang}` : "—" }}
        </template>
      </Column>
      <Column field="tanggal_daftar" header="Tanggal Daftar">
        <template #body="{ data }">
          {{ formatDate(data.tanggal_daftar) }}
        </template>
      </Column>
      <Column header="Biaya Sit-in">
        <template #body="{ data }">
          {{ formatRp(data.biaya_sitin) }}
        </template>
      </Column>
      <Column header="Biaya Pendaftaran">
        <template #body="{ data }">
          {{ formatRp(data.biaya_pendaftaran) }}
        </template>
      </Column>
      <Column header="Status" style="width: 7rem">
        <template #body="{ data }">
          <Tag :value="statusLabel[data.status as PendaftaranSiswaStatus]" :severity="statusSeverity[data.status as PendaftaranSiswaStatus]" />
        </template>
      </Column>
      <Column header="Jurnal Sit-in" style="width: 6.5rem">
        <template #body="{ data }">
          <Tag
            v-if="data.jurnal_sitin"
            value="Sudah"
            severity="info"
            title="Jurnal pembayaran sit-in sudah dibuat"
          />
          <span v-else class="muted">Belum</span>
        </template>
      </Column>
      <Column header="Jurnal Daftar" style="width: 6.5rem">
        <template #body="{ data }">
          <Tag
            v-if="data.jurnal_pendaftaran"
            value="Sudah"
            severity="success"
            title="Jurnal biaya pendaftaran sudah dibuat"
          />
          <span v-else class="muted">Belum</span>
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--xl" bodyClass="bee-col-actions--xl">
        <template #body="{ data }">
          <div class="bee-actions">
            <template v-if="data.status === 'TRIAL'">
              <Button
                v-if="!data.jurnal_sitin && Number(data.biaya_sitin) > 0"
                label="Bayar Sit-in"
                size="small"
                severity="success"
                outlined
                @click="confirmBayarSitin(data)"
              />
              <Button
                label="Finalisasi"
                size="small"
                @click="openFinalisasi(data)"
              />
              <Button
                icon="pi pi-pencil"
                size="small"
                text
                severity="secondary"
                @click="openEdit(data)"
              />
              <Button
                icon="pi pi-trash"
                size="small"
                text
                severity="danger"
                @click="confirmDelete(data)"
              />
            </template>
            <template v-else-if="data.status === 'REGISTERED' && data.siswa">
              <Button
                label="Lihat Siswa"
                size="small"
                text
                @click="router.push('/siswa')"
              />
            </template>
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Form calon -->
    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Pendaftaran' : 'Daftar Calon Siswa'"
      modal
      :style="{ width: 'min(480px, 96vw)' }"
    >
      <div class="bee-form-stack">
        <div class="bee-field">
          <label for="nama-calon">Nama calon</label>
          <InputText id="nama-calon" v-model="form.nama_calon" fluid />
        </div>
        <div class="bee-field">
          <label for="jenjang">Jenjang</label>
          <Select
            id="jenjang"
            v-model="form.jenjang"
            :options="jenjangList"
            option-label="kode"
            option-value="id"
            placeholder="Pilih jenjang"
            show-clear
            fluid
          />
        </div>
        <div class="bee-field">
          <label for="tanggal">Tanggal daftar</label>
          <DatePicker
            id="tanggal"
            v-model="form.tanggal_daftar"
            date-format="dd/mm/yy"
            show-icon
            fluid
          />
        </div>
        <div class="bee-field">
          <label for="sitin">Biaya sit-in</label>
          <InputNumber id="sitin" v-model="form.biaya_sitin" :min="0" fluid />
        </div>
        <div class="bee-field">
          <label for="pendaftaran">Biaya pendaftaran</label>
          <InputNumber id="pendaftaran" v-model="form.biaya_pendaftaran" :min="0" fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button
          label="Simpan"
          :loading="saving"
          :disabled="!form.nama_calon.trim()"
          @click="save"
        />
      </template>
    </Dialog>

    <!-- Finalisasi -->
    <Dialog
      v-model:visible="finalDialog"
      header="Finalisasi Pendaftaran"
      modal
      :style="{ width: 'min(420px, 96vw)' }"
    >
      <p v-if="finalTarget" class="bee-final-intro">
        Finalisasi <strong>{{ finalTarget.nama_calon }}</strong> menjadi siswa resmi.
        Biaya pendaftaran {{ formatRp(finalTarget.biaya_pendaftaran) }} akan dijurnal otomatis.
      </p>
      <div class="bee-field">
        <label for="spp">Nominal SPP bulanan</label>
        <InputNumber id="spp" v-model="sppNominal" :min="0" fluid />
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="finalDialog = false" />
        <Button label="Finalisasi" :loading="finalSaving" @click="runFinalisasi" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.bee-filter-field {
  min-width: 12rem;
}

.bee-mb {
  margin-bottom: 1rem;
}

.info-steps {
  margin: 0.5rem 0 0.5rem 1.25rem;
  padding: 0;
  line-height: 1.55;
}

.info-steps li {
  margin-bottom: 0.25rem;
}

.bee-form-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bee-field label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
  color: var(--bee-navy-700);
}

.muted {
  color: var(--app-text-muted);
  font-size: 0.85rem;
}

.bee-final-intro {
  margin: 0 0 1rem;
  line-height: 1.5;
}
</style>
