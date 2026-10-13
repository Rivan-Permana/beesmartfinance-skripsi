<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import Textarea from "primevue/textarea"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"

import {
  armadaApi,
  buildJemputanRekap,
  jemputanRekapToCsv,
  pendaftaranJemputanApi,
  type JemputanRekapRow,
} from "./api"
import { downloadCsv, kehadiranApi, monthDateRange } from "@/features/absensi/api"
import { legacyExportApi } from "@/features/katering/legacyExport"
import { JEMPUTAN_TARIF_MINIMAL } from "@/core/config"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { siswaApi } from "@/features/siswa/api"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { ArmadaJemputan, PendaftaranJemputan, Siswa } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()
const tab = ref("armada")

// --- Armada (E4.1) ---
const armadaRows = ref<ArmadaJemputan[]>([])
const armadaLoading = ref(false)
const armadaDialog = ref(false)
const armadaSaving = ref(false)
const armadaEditingId = ref<number | null>(null)
const armadaForm = reactive({
  nama_supir: "",
  jenis_mobil: "",
  kapasitas: 7,
  keterangan: "",
})

async function loadArmada() {
  armadaLoading.value = true
  try {
    armadaRows.value = await armadaApi.list()
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data armada.")
  } finally {
    armadaLoading.value = false
  }
}

function openArmadaCreate() {
  armadaEditingId.value = null
  Object.assign(armadaForm, {
    nama_supir: "", jenis_mobil: "", kapasitas: 7, keterangan: "",
  })
  armadaDialog.value = true
}

function openArmadaEdit(row: ArmadaJemputan) {
  armadaEditingId.value = row.id
  Object.assign(armadaForm, {
    nama_supir: row.nama_supir,
    jenis_mobil: row.jenis_mobil ?? "",
    kapasitas: row.kapasitas ?? 7,
    keterangan: row.keterangan ?? "",
  })
  armadaDialog.value = true
}

async function saveArmada() {
  armadaSaving.value = true
  try {
    const payload = { ...armadaForm }
    if (armadaEditingId.value) {
      await armadaApi.update(armadaEditingId.value, payload)
      notifySuccess(toast, "Armada diperbarui.")
    } else {
      await armadaApi.create(payload)
      notifySuccess(toast, "Armada ditambahkan.")
    }
    armadaDialog.value = false
    await loadArmada()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan armada.")
  } finally {
    armadaSaving.value = false
  }
}

function confirmDeleteArmada(row: ArmadaJemputan) {
  confirm.require({
    message: `Hapus armada ${row.nama_supir}?`,
    header: "Konfirmasi",
    acceptLabel: "Hapus",
    rejectLabel: "Batal",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await armadaApi.remove(row.id)
        notifySuccess(toast, "Armada dihapus.")
        await loadArmada()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus armada.")
      }
    },
  })
}

// --- Pendaftaran (E4.2) ---
const pendaftaranRows = ref<PendaftaranJemputan[]>([])
const siswaList = ref<Siswa[]>([])
const pendaftaranLoading = ref(false)
const pendaftaranDialog = ref(false)
const pendaftaranSaving = ref(false)
const pendaftaranEditingId = ref<number | null>(null)
const pendaftaranForm = reactive({
  siswa: null as number | null,
  armada: null as number | null,
  harga: JEMPUTAN_TARIF_MINIMAL,
})

const siswaMap = computed(() => {
  const m = new Map<number, Siswa>()
  siswaList.value.forEach((s) => m.set(s.id, s))
  return m
})

const armadaMap = computed(() => {
  const m = new Map<number, string>()
  armadaRows.value.forEach((a) =>
    m.set(a.id, `${a.nama_supir}${a.jenis_mobil ? ` (${a.jenis_mobil})` : ""}`),
  )
  return m
})

const selectedSiswaAlamat = computed(() => {
  if (!pendaftaranForm.siswa) return ""
  return siswaMap.value.get(pendaftaranForm.siswa)?.alamat ?? "—"
})

async function loadPendaftaran() {
  pendaftaranLoading.value = true
  try {
    const [pend, siswa] = await Promise.all([
      pendaftaranJemputanApi.list(),
      siswaApi.listAll({ status: "aktif" }),
    ])
    pendaftaranRows.value = pend
    siswaList.value = siswa
  } catch (e) {
    notifyError(toast, e, "Gagal memuat pendaftaran jemputan.")
  } finally {
    pendaftaranLoading.value = false
  }
}

function openPendaftaranCreate() {
  pendaftaranEditingId.value = null
  Object.assign(pendaftaranForm, {
    siswa: null, armada: null, harga: JEMPUTAN_TARIF_MINIMAL,
  })
  pendaftaranDialog.value = true
}

function openPendaftaranEdit(row: PendaftaranJemputan) {
  pendaftaranEditingId.value = row.id
  Object.assign(pendaftaranForm, {
    siswa: row.siswa,
    armada: row.armada,
    harga: Number(row.harga) || JEMPUTAN_TARIF_MINIMAL,
  })
  pendaftaranDialog.value = true
}

async function savePendaftaran() {
  if (!pendaftaranForm.siswa) return
  pendaftaranSaving.value = true
  try {
    const payload = {
      siswa: pendaftaranForm.siswa,
      armada: pendaftaranForm.armada,
      harga: String(pendaftaranForm.harga),
    }
    if (pendaftaranEditingId.value) {
      await pendaftaranJemputanApi.update(pendaftaranEditingId.value, payload)
      notifySuccess(toast, "Pendaftaran diperbarui.")
    } else {
      await pendaftaranJemputanApi.create(payload)
      notifySuccess(toast, "Siswa terdaftar jemputan.")
    }
    pendaftaranDialog.value = false
    await loadPendaftaran()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan pendaftaran.")
  } finally {
    pendaftaranSaving.value = false
  }
}

function confirmDeletePendaftaran(row: PendaftaranJemputan) {
  const nama = siswaMap.value.get(row.siswa)?.nama ?? `#${row.siswa}`
  confirm.require({
    message: `Hapus pendaftaran jemputan ${nama}?`,
    header: "Konfirmasi",
    acceptLabel: "Hapus",
    rejectLabel: "Batal",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await pendaftaranJemputanApi.remove(row.id)
        notifySuccess(toast, "Pendaftaran dihapus.")
        await loadPendaftaran()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus pendaftaran.")
      }
    },
  })
}

// --- Rekap (E4.3) ---
const bulan = ref(new Date().getMonth() + 1)
const tahun = ref(new Date().getFullYear())
const rekapRows = ref<JemputanRekapRow[]>([])
const rekapLoading = ref(false)

const { query: rekapSearch, filtered: filteredRekapRows } = useTableSearch(rekapRows, (r) => [
  r.nis,
  r.nama,
  r.armada,
  formatRp(r.tarifPerTrip),
  formatRp(r.totalNominal),
  String(r.jemputDatang),
  String(r.jemputPulang),
])

const totalTagihan = computed(() =>
  filteredRekapRows.value.reduce((s, r) => s + r.totalNominal, 0),
)

const BULAN_LABEL = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

async function loadRekap() {
  rekapLoading.value = true
  try {
    const range = monthDateRange(bulan.value, tahun.value)
    const [pend, siswaRes, records] = await Promise.all([
      pendaftaranJemputanApi.list(),
      siswaApi.listAll({ status: "aktif" }),
      kehadiranApi.listAll(range),
    ])

    const sMap = new Map(
      siswaRes.map((s) => [
        s.id,
        { nis: s.nis, nama: s.nama, alamat: s.alamat },
      ]),
    )
    const aMap = armadaMap.value

    const absMap = new Map<number, { datang: number; pulang: number }>()
    for (const r of records) {
      if (!absMap.has(r.siswa)) absMap.set(r.siswa, { datang: 0, pulang: 0 })
      const a = absMap.get(r.siswa)!
      if (r.jemput_datang) a.datang += 1
      if (r.jemput_pulang) a.pulang += 1
    }

    rekapRows.value = buildJemputanRekap(pend, sMap, aMap, absMap)
  } catch (e) {
    notifyError(toast, e, "Gagal memuat rekap jemputan.")
  } finally {
    rekapLoading.value = false
  }
}

function exportRekapCsv() {
  if (rekapRows.value.length === 0) return
  const name = `rekap-jemputan-${tahun.value}-${String(bulan.value).padStart(2, "0")}.csv`
  downloadCsv(name, jemputanRekapToCsv(rekapRows.value))
}

async function exportLegacyCsv() {
  try {
    const name = `laporan-jemput-legacy-${tahun.value}-${String(bulan.value).padStart(2, "0")}.csv`
    await legacyExportApi.jemput(bulan.value, tahun.value, name)
    notifySuccess(toast, "Export legacy jemput berhasil.")
  } catch (e) {
    notifyError(toast, e, "Gagal export legacy jemput.")
  }
}

watch(tab, (t) => {
  if (t === "armada") loadArmada()
  if (t === "pendaftaran") {
    loadArmada()
    loadPendaftaran()
  }
  if (t === "rekap") {
    loadArmada()
    loadRekap()
  }
})

watch([bulan, tahun], () => {
  if (tab.value === "rekap") loadRekap()
})

onMounted(loadArmada)
</script>

<template>
  <PageLayout
    title="Jemputan"
    subtitle="Kelola armada, pendaftaran siswa, dan rekap tagihan jemputan"
  >
    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="armada">Armada</Tab>
        <Tab value="pendaftaran">Pendaftaran Siswa</Tab>
        <Tab value="rekap">Rekap Tagihan</Tab>
      </TabList>
      <TabPanels>
        <!-- Armada -->
        <TabPanel value="armada">
          <div class="tab-toolbar">
            <Button label="Tambah Armada" icon="pi pi-plus" @click="openArmadaCreate" />
          </div>
          <DataTable
            :value="armadaRows"
            :loading="armadaLoading"
            data-key="id"
            paginator
            :rows="10"
            striped-rows
          >
            <template #empty>
              <EmptyState message="Belum ada armada. Tambah supir & mobil terlebih dahulu." action-label="Tambah Armada" @action="openArmadaCreate" />
            </template>
            <Column field="nama_supir" header="Supir" />
            <Column field="jenis_mobil" header="Mobil" />
            <Column header="Kapasitas">
              <template #body="{ data }">{{ data.kapasitas ?? 0 }} penumpang</template>
            </Column>
            <Column field="keterangan" header="Keterangan" />
            <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text aria-label="Edit" @click="openArmadaEdit(data)" />
                  <Button icon="pi pi-trash" text severity="danger" aria-label="Hapus" @click="confirmDeleteArmada(data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <!-- Pendaftaran -->
        <TabPanel value="pendaftaran">
          <div class="tab-toolbar">
            <Button label="Daftarkan Siswa" icon="pi pi-plus" @click="openPendaftaranCreate" />
          </div>
          <DataTable
            :value="pendaftaranRows"
            :loading="pendaftaranLoading"
            data-key="id"
            paginator
            :rows="10"
            striped-rows
          >
            <template #empty>
              <EmptyState message="Belum ada siswa terdaftar jemputan." action-label="Daftarkan Siswa" @action="openPendaftaranCreate" />
            </template>
            <Column header="Siswa">
              <template #body="{ data }">{{ siswaMap.get(data.siswa)?.nama ?? `#${data.siswa}` }}</template>
            </Column>
            <Column header="Alamat">
              <template #body="{ data }">{{ siswaMap.get(data.siswa)?.alamat ?? "—" }}</template>
            </Column>
            <Column header="Armada">
              <template #body="{ data }">{{ data.armada ? armadaMap.get(data.armada) : "—" }}</template>
            </Column>
            <Column header="Harga / bulan">
              <template #body="{ data }">
                <span class="tabular-nums">{{ formatRp(data.harga) }}</span>
              </template>
            </Column>
            <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button icon="pi pi-pencil" text aria-label="Edit" @click="openPendaftaranEdit(data)" />
                  <Button icon="pi pi-trash" text severity="danger" aria-label="Hapus" @click="confirmDeletePendaftaran(data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <!-- Rekap -->
        <TabPanel value="rekap">
          <div class="tab-toolbar">
            <PeriodPicker v-model:bulan="bulan" v-model:tahun="tahun" />
            <Button
              label="Export CSV"
              icon="pi pi-download"
              severity="secondary"
              :disabled="rekapRows.length === 0 || rekapLoading"
              @click="exportRekapCsv"
            />
            <Button
              label="Export Legacy"
              icon="pi pi-file-export"
              severity="secondary"
              outlined
              :disabled="rekapLoading"
              @click="exportLegacyCsv"
            />
          </div>
          <SearchField
            v-model="rekapSearch"
            block
            hint="Cari NIS, nama, armada, harga jemputan"
          />

          <Message severity="info" :closable="false" class="info-msg">
            <strong>Cara hitung:</strong> Tagihan jemputan = (Datang + Pulang) × tarif per trip dari pendaftaran.
            Kolom <strong>Total</strong> = nominal tagihan bulan ini (selaras generate tagihan).
            <br />
            <span class="info-note">Catatan: penugasan pendamping guru per armada belum tersedia di versi ini — fitur direncanakan rilis berikutnya.</span>
          </Message>

          <DataTable
            :value="filteredRekapRows"
            :loading="rekapLoading"
            data-key="siswaId"
            paginator
            :rows="15"
            striped-rows
            class="rekap-count-table"
          >
            <template #empty>
              <EmptyState :message="`Belum ada pendaftaran jemputan untuk rekap ${BULAN_LABEL[bulan - 1]} ${tahun}.`" />
            </template>
            <Column field="nis" header="NIS" />
            <Column field="nama" header="Nama" />
            <Column field="armada" header="Armada" />
            <Column header="Tarif / trip">
              <template #body="{ data }">
                <span class="tabular-nums">{{ formatRp(data.tarifPerTrip) }}</span>
              </template>
            </Column>
            <Column field="jemputDatang" header-class="count-col count-col--wide" body-class="count-col count-col--wide">
              <template #header>
                <span title="Hari dijemput pagi">Datang</span>
              </template>
              <template #body="{ data }">
                <span class="count-val">{{ data.jemputDatang }}</span>
              </template>
            </Column>
            <Column field="jemputPulang" header-class="count-col count-col--wide" body-class="count-col count-col--wide">
              <template #header>
                <span title="Hari dijemput sore">Pulang</span>
              </template>
              <template #body="{ data }">
                <span class="count-val">{{ data.jemputPulang }}</span>
              </template>
            </Column>
            <Column header="Total">
              <template #body="{ data }">
                <span class="tabular-nums">{{ formatRp(data.totalNominal) }}</span>
              </template>
            </Column>
          </DataTable>

          <div v-if="filteredRekapRows.length > 0" class="total-bar bee-section-title">
            <span>Total tagihan jemputan bulan ini</span>
            <strong>{{ formatRp(totalTagihan) }}</strong>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Dialog Armada -->
    <Dialog
      v-model:visible="armadaDialog"
      :header="armadaEditingId ? 'Edit Armada' : 'Tambah Armada'"
      modal
      :style="{ width: '30rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Nama Supir *</label>
          <InputText v-model="armadaForm.nama_supir" fluid />
        </div>
        <div class="field">
          <label>Jenis Mobil</label>
          <InputText v-model="armadaForm.jenis_mobil" fluid placeholder="Avanza, Innova, …" />
        </div>
        <div class="field">
          <label>Kapasitas</label>
          <InputNumber v-model="armadaForm.kapasitas" :min="1" fluid />
        </div>
        <div class="field span2">
          <label>Keterangan / Rute</label>
          <Textarea v-model="armadaForm.keterangan" rows="2" auto-resize fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="armadaDialog = false" />
        <Button label="Simpan" :loading="armadaSaving" :disabled="!armadaForm.nama_supir.trim()" @click="saveArmada" />
      </template>
    </Dialog>

    <!-- Dialog Pendaftaran -->
    <Dialog
      v-model:visible="pendaftaranDialog"
      :header="pendaftaranEditingId ? 'Edit Pendaftaran' : 'Daftarkan Jemputan'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Siswa *</label>
          <Select
            v-model="pendaftaranForm.siswa"
            :options="siswaList"
            option-label="nama"
            option-value="id"
            filter
            placeholder="Pilih siswa"
            fluid
          />
        </div>
        <div class="field span2">
          <label>Alamat (dari data siswa)</label>
          <InputText :model-value="selectedSiswaAlamat" disabled fluid />
        </div>
        <div class="field span2">
          <label>Armada</label>
          <Select
            v-model="pendaftaranForm.armada"
            :options="armadaRows"
            :option-label="(a: ArmadaJemputan) => `${a.nama_supir} (${a.jenis_mobil || 'mobil'})`"
            option-value="id"
            show-clear
            placeholder="Pilih armada"
            fluid
          />
        </div>
        <div class="field span2">
          <label>Harga per bulan *</label>
          <InputNumber v-model="pendaftaranForm.harga" :min="0" fluid />
          <small>Minimal referensi: {{ formatRp(JEMPUTAN_TARIF_MINIMAL) }}</small>
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="pendaftaranDialog = false" />
        <Button
          label="Simpan"
          :loading="pendaftaranSaving"
          :disabled="!pendaftaranForm.siswa"
          @click="savePendaftaran"
        />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.tab-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 1rem;
}
.info-msg {
  margin-bottom: 1rem;
}
.info-note {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.85rem;
  opacity: 0.9;
}
.total-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  background: var(--app-bg);
  border-radius: var(--bee-radius-md, 12px);
  font-weight: 600;
}
.total-bar strong {
  color: var(--bee-navy);
  font-size: 1.05rem;
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
.field.span2 {
  grid-column: 1 / -1;
}
.field label {
  font-weight: 600;
  font-size: 0.85rem;
}
.field small {
  color: var(--app-text-muted);
}
</style>
