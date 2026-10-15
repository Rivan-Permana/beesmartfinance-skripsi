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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue"

import { legacyExportApi } from "./legacyExport"
import {
  buildKateringRekapFromRecords,
  formatTanggalId,
  kateringRekapToCsv,
  menuKateringApi,
  tarifKateringApi,
  weekdaysOfWeek,
  weekRange,
  type KateringRekapRow,
} from "./api"
import {
  downloadCsv,
  jenjangApi,
  kelompokApi,
  kehadiranApi,
  monthDateRange,
} from "@/features/absensi/api"
import { DEFAULT_TARIF_JUMAT, DEFAULT_TARIF_SEN_KAM } from "@/core/config"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { siswaApi } from "@/features/siswa/api"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Jenjang, KehadiranSiswa, Kelompok, MenuKatering } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const tab = ref("rekap")

// --- Rekap (E3.1) ---
const bulan = ref(new Date().getMonth() + 1)
const tahun = ref(new Date().getFullYear())
const jenjangList = ref<Jenjang[]>([])
const kelompokList = ref<Kelompok[]>([])
const jenjangFilter = ref<number | null>(null)
const kelompokFilter = ref<number | null>(null)
const rekapRows = ref<KateringRekapRow[]>([])
const rekapLoading = ref(false)
const tarifHarian = ref(DEFAULT_TARIF_SEN_KAM)
const tarifJumat = ref(DEFAULT_TARIF_JUMAT)
const tarifIsDefault = ref(true)
const tarifSaving = ref(false)
const studentBase = ref<
  { id: number; nis: string | null; nama: string; kelompok: string }[]
>([])
const kehadiranRecords = ref<KehadiranSiswa[]>([])

const kelompokFiltered = computed(() =>
  jenjangFilter.value
    ? kelompokList.value.filter((k) => k.jenjang === jenjangFilter.value)
    : kelompokList.value,
)

const jenjangOptions = computed(() => [
  { label: "Semua jenjang", value: null as number | null },
  ...jenjangList.value.map((j) => ({ label: j.kode, value: j.id })),
])

const kelompokOptions = computed(() => [
  { label: "Semua kelompok", value: null as number | null },
  ...kelompokFiltered.value.map((k) => ({ label: k.nama, value: k.id })),
])

const { query: rekapSearch, filtered: filteredRekapRows } = useTableSearch(rekapRows, (r) => [
  r.nis ?? "",
  r.nama,
  r.kelompok,
  String(r.hariSenKam),
  String(r.hariJumat),
  formatRp(r.total),
])

const totalTagihan = computed(() =>
  filteredRekapRows.value.reduce((s, r) => s + r.total, 0),
)

const BULAN_LABEL = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

function applyTarifToRekap() {
  rekapRows.value = buildKateringRekapFromRecords(
    studentBase.value,
    kehadiranRecords.value,
    tarifHarian.value,
    tarifJumat.value,
  )
}

async function loadTarif() {
  try {
    const data = await tarifKateringApi.get(bulan.value, tahun.value)
    tarifHarian.value = Number(data.tarif_harian)
    tarifJumat.value = Number(data.tarif_jumat)
    tarifIsDefault.value = data.is_default
  } catch {
    tarifHarian.value = DEFAULT_TARIF_SEN_KAM
    tarifJumat.value = DEFAULT_TARIF_JUMAT
    tarifIsDefault.value = true
  }
}

async function saveTarif() {
  tarifSaving.value = true
  try {
    const data = await tarifKateringApi.set({
      periode_bulan: bulan.value,
      periode_tahun: tahun.value,
      tarif_harian: tarifHarian.value,
      tarif_jumat: tarifJumat.value,
    })
    tarifHarian.value = Number(data.tarif_harian)
    tarifJumat.value = Number(data.tarif_jumat)
    tarifIsDefault.value = false
    applyTarifToRekap()
    notifySuccess(toast, `Tarif katering ${BULAN_LABEL[bulan.value - 1]} ${tahun.value} disimpan.`)
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan tarif katering.")
  } finally {
    tarifSaving.value = false
  }
}

async function loadRekap() {
  rekapLoading.value = true
  try {
    const range = monthDateRange(bulan.value, tahun.value)
    const params: Record<string, unknown> = { ...range }
    if (kelompokFilter.value) params.kelompok = kelompokFilter.value

    let studentParams: Record<string, unknown> = { status: "aktif" }
    if (kelompokFilter.value) {
      studentParams.kelompok = kelompokFilter.value
    } else if (jenjangFilter.value) {
      const ids = kelompokFiltered.value.map((k) => k.id)
      if (ids.length === 0) {
        rekapRows.value = []
        return
      }
    }

    const [students, records, kelompoks, jenjangs] = await Promise.all([
      siswaApi.listAll(studentParams),
      kehadiranApi.listAll(params),
      kelompokApi.list(),
      jenjangApi.list(),
    ])

    jenjangList.value = jenjangs
    kelompokList.value = kelompoks
    const kelompokNama = new Map(kelompoks.map((k) => [k.id, k.nama]))

    let studentList = students
    if (jenjangFilter.value && !kelompokFilter.value) {
      const allowed = new Set(kelompokFiltered.value.map((k) => k.id))
      studentList = students.filter((s) => s.kelompok && allowed.has(s.kelompok))
    }

    const absensi = records.filter((r) => r.ikut_katering)
    studentBase.value = studentList.map((s) => ({
      id: s.id,
      nis: s.nis,
      nama: s.nama,
      kelompok: s.kelompok ? kelompokNama.get(s.kelompok) ?? "-" : "-",
    }))
    kehadiranRecords.value = absensi
    applyTarifToRekap()
  } catch (e) {
    notifyError(toast, e, "Gagal memuat rekap katering.")
  } finally {
    rekapLoading.value = false
  }
}

function exportRekapCsv() {
  if (rekapRows.value.length === 0) return
  const name = `rekap-katering-${tahun.value}-${String(bulan.value).padStart(2, "0")}.csv`
  downloadCsv(name, kateringRekapToCsv(rekapRows.value))
}

async function exportLegacyCsv() {
  try {
    const name = `laporan-katering-legacy-${tahun.value}-${String(bulan.value).padStart(2, "0")}.csv`
    await legacyExportApi.katering(bulan.value, tahun.value, name)
    notifySuccess(toast, "Export legacy katering berhasil.")
  } catch (e) {
    notifyError(toast, e, "Gagal export legacy katering.")
  }
}

watch(jenjangFilter, () => {
  if (
    kelompokFilter.value &&
    !kelompokFiltered.value.some((k) => k.id === kelompokFilter.value)
  ) {
    kelompokFilter.value = null
  }
})

watch([bulan, tahun, jenjangFilter, kelompokFilter], async () => {
  if (tab.value === "rekap") {
    await loadTarif()
    await loadRekap()
  }
})

watch([tarifHarian, tarifJumat], () => {
  if (studentBase.value.length) applyTarifToRekap()
})

// --- Menu mingguan (E3.2) ---
const weekAnchor = ref(new Date())
const menuMap = ref<Map<string, MenuKatering>>(new Map())
const menuLoading = ref(false)
const menuDialog = ref(false)
const menuSaving = ref(false)
const menuEditingId = ref<number | null>(null)
const menuForm = reactive({ tanggal: "", keterangan: "" })
const menuGambarFile = ref<File | null>(null)
const menuGambarPreview = ref<string | null>(null)
const menuError = ref("")

function clearMenuPreview() {
  if (menuGambarPreview.value?.startsWith("blob:")) URL.revokeObjectURL(menuGambarPreview.value)
  menuGambarPreview.value = null
}

onUnmounted(clearMenuPreview)

const weekDates = computed(() => weekdaysOfWeek(weekAnchor.value))

const weekLabel = computed(() => {
  const d = weekDates.value
  if (d.length === 0) return ""
  return `${formatTanggalId(d[0])} – ${formatTanggalId(d[d.length - 1])}`
})

const menuRows = computed(() =>
  weekDates.value.map((tanggal) => ({
    tanggal,
    label: formatTanggalId(tanggal),
    menu: menuMap.value.get(tanggal) ?? null,
  })),
)

async function loadMenu() {
  menuLoading.value = true
  try {
    const dates = weekDates.value
    const items = await menuKateringApi.listAll(weekRange(dates))
    const map = new Map<string, MenuKatering>()
    for (const m of items) map.set(m.tanggal, m)
    menuMap.value = map
  } catch (e) {
    notifyError(toast, e, "Gagal memuat menu katering.")
  } finally {
    menuLoading.value = false
  }
}

function shiftWeek(delta: number) {
  const d = new Date(weekAnchor.value)
  d.setDate(d.getDate() + delta * 7)
  weekAnchor.value = d
}

function openMenuCreate(tanggal: string) {
  clearMenuPreview()
  menuError.value = ""
  menuEditingId.value = null
  menuForm.tanggal = tanggal
  menuForm.keterangan = ""
  menuGambarFile.value = null
  menuGambarPreview.value = null
  menuDialog.value = true
}

function openMenuEdit(row: MenuKatering) {
  clearMenuPreview()
  menuError.value = ""
  menuEditingId.value = row.id
  menuForm.tanggal = row.tanggal
  menuForm.keterangan = row.keterangan ?? ""
  menuGambarFile.value = null
  menuGambarPreview.value = row.gambar_url ?? null
  menuDialog.value = true
}

function onMenuFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  if (!file) return
  clearMenuPreview()
  menuError.value = ""
  menuGambarFile.value = file
  if (file) {
    menuGambarPreview.value = URL.createObjectURL(file)
  }
}

async function saveMenu() {
  if (menuSaving.value) return
  menuError.value = ""
  if (!menuForm.keterangan.trim() && !menuGambarFile.value && !menuGambarPreview.value) {
    menuError.value = "Isi keterangan atau pilih foto menu terlebih dahulu."
    return
  }
  menuSaving.value = true
  try {
    if (menuEditingId.value) {
      if (menuGambarFile.value) {
        await menuKateringApi.updateWithForm(menuEditingId.value, {
          keterangan: menuForm.keterangan,
          gambar: menuGambarFile.value,
        })
      } else {
        await menuKateringApi.update(menuEditingId.value, {
          keterangan: menuForm.keterangan,
        })
      }
      notifySuccess(toast, "Menu diperbarui.")
    } else {
      await menuKateringApi.createWithForm({
        tanggal: menuForm.tanggal,
        keterangan: menuForm.keterangan,
        gambar: menuGambarFile.value ?? undefined,
      })
      notifySuccess(toast, "Menu ditambahkan.")
    }
    menuDialog.value = false
    await loadMenu()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan menu.")
  } finally {
    menuSaving.value = false
  }
}

function confirmDeleteMenu(row: MenuKatering) {
  confirm.require({
    message: `Hapus menu ${formatTanggalId(row.tanggal)}?`,
    header: "Konfirmasi",
    acceptLabel: "Hapus",
    rejectLabel: "Batal",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await menuKateringApi.remove(row.id)
        notifySuccess(toast, "Menu dihapus.")
        await loadMenu()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus menu.")
      }
    },
  })
}

watch(tab, (t) => {
  if (t === "rekap") loadRekap()
  if (t === "menu") loadMenu()
})

watch(weekAnchor, () => {
  if (tab.value === "menu") loadMenu()
})

onMounted(async () => {
  await loadTarif()
  await loadRekap()
})
</script>

<template>
  <PageLayout
    title="Katering"
    subtitle="Rekap tagihan katering dari absensi & menu mingguan Senin–Jumat"
  >
    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="rekap">Rekap Tagihan</Tab>
        <Tab value="menu">Menu Mingguan</Tab>
      </TabList>
      <TabPanels>
        <!-- Rekap -->
        <TabPanel value="rekap">
          <div class="katering-toolbar">
            <div class="katering-toolbar__filters">
              <PeriodPicker v-model:bulan="bulan" v-model:tahun="tahun" />
              <Select
                v-model="jenjangFilter"
                :options="jenjangOptions"
                option-label="label"
                option-value="value"
                placeholder="Jenjang"
                show-clear
                class="toolbar-select"
              />
              <Select
                v-model="kelompokFilter"
                :options="kelompokOptions"
                option-label="label"
                option-value="value"
                placeholder="Kelompok"
                show-clear
                class="toolbar-select"
              />
            </div>

            <div class="katering-toolbar__tarif">
              <span class="toolbar-label">Sen–Kam</span>
              <div class="toolbar-tarif-input-wrap">
                <InputNumber
                  v-model="tarifHarian"
                  :min="0"
                  :use-grouping="true"
                  fluid
                />
              </div>
              <span class="toolbar-label">Jumat</span>
              <div class="toolbar-tarif-input-wrap">
                <InputNumber
                  v-model="tarifJumat"
                  :min="0"
                  :use-grouping="true"
                  fluid
                />
              </div>
              <Button
                label="Simpan"
                icon="pi pi-save"
                size="small"
                outlined
                :loading="tarifSaving"
                @click="saveTarif"
              />
            </div>

            <div class="katering-toolbar__actions">
              <Button
                label="Export CSV"
                icon="pi pi-download"
                size="small"
                severity="secondary"
                outlined
                :disabled="rekapRows.length === 0 || rekapLoading"
                @click="exportRekapCsv"
              />
              <Button
                label="Export Legacy"
                icon="pi pi-file-export"
                size="small"
                severity="secondary"
                outlined
                :disabled="rekapLoading"
                title="Layout mirror laporan katering.csv (TK A | TK B)"
                @click="exportLegacyCsv"
              />
            </div>
          </div>
          <SearchField
            v-model="rekapSearch"
            block
            hint="Cari NIS, nama, kelompok, tarif, total"
          />

          <Message severity="info" :closable="false" class="tarif-msg">
            <strong>Cara hitung:</strong> Total = (hari Sen–Kam × tarif Sen–Kam) + (hari Jumat × tarif Jumat).
            Tarif bisa <strong>diubah per bulan</strong> — klik <em>Simpan</em> setelah mengubah angka.
            <span v-if="tarifIsDefault" class="tarif-hint">
              Periode ini belum punya tarif tersimpan; dipakai sementara
              {{ formatRp(DEFAULT_TARIF_SEN_KAM) }} / {{ formatRp(DEFAULT_TARIF_JUMAT) }}.
            </span>
          </Message>

          <DataTable
            :value="filteredRekapRows"
            :loading="rekapLoading"
            data-key="siswaId"
            paginator
            :rows="15"
            striped-rows
            class="katering-rekap-table"
          >
            <template #empty>
              <EmptyState
                :message="`Belum ada hari katering ${BULAN_LABEL[bulan - 1]} ${tahun}. Tandai absensi dulu.`"
              />
            </template>
            <Column
              field="nis"
              header="NIS"
              header-class="katering-col katering-col--nis"
              body-class="katering-col katering-col--nis"
            />
            <Column
              field="nama"
              header="Nama"
              header-class="katering-col katering-col--nama"
              body-class="katering-col katering-col--nama"
            />
            <Column
              field="kelompok"
              header="Kelompok"
              header-class="katering-col katering-col--kel"
              body-class="katering-col katering-col--kel"
            />
            <Column
              field="hariSenKam"
              header="Sen–Kam"
              header-class="katering-col katering-col--hari"
              body-class="katering-col katering-col--hari"
            />
            <Column
              field="hariJumat"
              header="Jumat"
              header-class="katering-col katering-col--hari"
              body-class="katering-col katering-col--hari"
            />
            <Column
              field="hariKatering"
              header-class="katering-col katering-col--hari"
              body-class="katering-col katering-col--hari"
            >
              <template #header>
                <span title="Total hari ikut katering">Total hari</span>
              </template>
              <template #body="{ data }">
                <span class="count-val katering-hari">{{ data.hariKatering }}</span>
              </template>
            </Column>
            <Column
              header-class="katering-col katering-col--money"
              body-class="katering-col katering-col--money"
            >
              <template #header>Tarif</template>
              <template #body="{ data }">
                <div class="tarif-stack">
                  <span class="katering-rp tabular-nums">Sen–Kam: {{ formatRp(data.tarifSenKam) }}</span>
                  <span class="katering-rp tabular-nums katering-rp--jumat">Jumat: {{ formatRp(data.tarifJumat) }}</span>
                </div>
              </template>
            </Column>
            <Column
              header-class="katering-col katering-col--total"
              body-class="katering-col katering-col--total"
            >
              <template #header>Total</template>
              <template #body="{ data }">
                <span class="katering-rp katering-rp--total tabular-nums">{{ formatRp(data.total) }}</span>
              </template>
            </Column>
          </DataTable>

          <div v-if="filteredRekapRows.length > 0" class="total-bar bee-section-title">
            <span>Total rekap {{ BULAN_LABEL[bulan - 1] }} {{ tahun }}</span>
            <strong>{{ formatRp(totalTagihan) }}</strong>
          </div>
        </TabPanel>

        <!-- Menu -->
        <TabPanel value="menu">
          <div class="tab-toolbar">
            <Button icon="pi pi-chevron-left" text rounded aria-label="Minggu sebelumnya" @click="shiftWeek(-1)" />
            <span class="week-label">{{ weekLabel }}</span>
            <Button icon="pi pi-chevron-right" text rounded aria-label="Minggu berikutnya" @click="shiftWeek(1)" />
            <Button label="Minggu ini" severity="secondary" text size="small" @click="weekAnchor = new Date()" />
          </div>

          <DataTable :value="menuRows" :loading="menuLoading" data-key="tanggal" striped-rows>
            <template #empty>
              <EmptyState message="Belum ada menu untuk minggu ini." />
            </template>
            <Column header="Hari">
              <template #body="{ data }">{{ data.label }}</template>
            </Column>
            <Column header="Foto" style="width: 5rem">
              <template #body="{ data }">
                <img
                  v-if="data.menu?.gambar_url"
                  :src="data.menu.gambar_url"
                  alt=""
                  class="menu-thumb"
                />
                <span v-else class="muted">—</span>
              </template>
            </Column>
            <Column header="Menu">
              <template #body="{ data }">
                <span v-if="data.menu?.keterangan">{{ data.menu.keterangan }}</span>
                <span v-else class="muted">Belum diisi</span>
              </template>
            </Column>
            <Column header="Aksi" headerClass="bee-col-actions--sm" bodyClass="bee-col-actions--sm">
              <template #body="{ data }">
                <div class="bee-actions">
                  <Button
                    v-if="data.menu"
                    icon="pi pi-pencil"
                    text
                    rounded
                    aria-label="Edit menu"
                    @click="openMenuEdit(data.menu)"
                  />
                  <Button
                    v-else
                    label="Isi"
                    size="small"
                    text
                    @click="openMenuCreate(data.tanggal)"
                  />
                  <Button
                    v-if="data.menu"
                    icon="pi pi-trash"
                    text
                    rounded
                    severity="danger"
                    aria-label="Hapus menu"
                    @click="confirmDeleteMenu(data.menu)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog
      v-model:visible="menuDialog"
      :header="menuEditingId ? 'Edit Menu' : 'Tambah Menu'"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="form">
        <div class="field">
          <label>Tanggal</label>
          <InputText :model-value="formatTanggalId(menuForm.tanggal)" disabled fluid />
        </div>
        <div class="field">
          <label for="menu-keterangan">Menu / Keterangan</label>
          <Textarea id="menu-keterangan" v-model="menuForm.keterangan" rows="4" auto-resize fluid aria-describedby="menu-input-help" placeholder="Contoh: Nasi, ayam goreng, sayur bayam, buah pepaya" />
        </div>
        <div class="field">
          <label for="menu-foto">Foto menu</label>
          <input id="menu-foto" type="file" accept="image/*" aria-describedby="menu-input-help" @change="onMenuFileSelect" />
          <small id="menu-input-help">Isi keterangan, unggah foto, atau keduanya.</small>
          <img v-if="menuGambarPreview" :src="menuGambarPreview" alt="Pratinjau foto menu katering" class="menu-preview" />
        </div>
        <Message v-if="menuError" severity="error" :closable="false" role="alert">{{ menuError }}</Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="menuDialog = false" />
        <Button label="Simpan" :loading="menuSaving" :disabled="menuSaving" @click="saveMenu" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.katering-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
  margin-bottom: 0.85rem;
  padding: 0.75rem 1rem;
  background: var(--app-bg, #faf8f5);
  border: 1px solid var(--app-border, #e8e4dc);
  border-radius: var(--bee-radius-md, 12px);
}

.katering-toolbar__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.katering-toolbar__tarif {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-left: 0.85rem;
  border-left: 1px solid var(--app-border, #e8e4dc);
}

.katering-toolbar__actions {
  margin-left: auto;
}

.toolbar-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--app-text-muted);
  white-space: nowrap;
}

.katering-toolbar :deep(.period-picker .p-select) {
  min-width: 7.5rem;
}

.katering-toolbar :deep(.toolbar-select) {
  min-width: 8rem;
  max-width: 10rem;
}

.toolbar-tarif-input-wrap {
  width: 6.75rem;
}

.toolbar-tarif-input-wrap :deep(.p-inputnumber) {
  width: 100%;
}

.tab-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.65rem;
}
.tarif-msg {
  margin-bottom: 1rem;
}
.tarif-hint {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.85rem;
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
.week-label {
  font-weight: 600;
  min-width: 12rem;
  text-align: center;
}
.muted {
  color: var(--app-text-muted);
  font-style: italic;
}
.form {
  display: flex;
  flex-direction: column;
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
.menu-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 8px;
}
.menu-preview {
  margin-top: 0.5rem;
  max-width: 100%;
  max-height: 160px;
  border-radius: 8px;
  object-fit: cover;
}
</style>
