<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"

import StaffAttendanceGrid, { type StaffAttendanceRow } from "./StaffAttendanceGrid.vue"
import { absenPegawaiApi, pegawaiApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import type { AbsenPegawaiRekap, AbsenPegawaiStatus, Pegawai } from "@/types/api"

const toast = useToast()
const tab = ref("harian")

const tanggal = ref<Date>(new Date())
const pegawaiList = ref<Pegawai[]>([])
const attendance = ref<Record<number, StaffAttendanceRow>>({})
const loading = ref(false)
const saving = ref(false)

const rekapBulan = ref(new Date().getMonth() + 1)
const rekapTahun = ref(new Date().getFullYear())
const rekap = ref<AbsenPegawaiRekap[]>([])
const loadingRekap = ref(false)

const tanggalStr = computed(() => {
  const d = tanggal.value
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
})

const activeStaff = computed(() => pegawaiList.value.filter((p) => p.status_aktif))

function statusToFlags(status: AbsenPegawaiStatus) {
  return {
    hadir: status === "hadir" ? 1 : 0,
    izin: status === "izin" ? 1 : 0,
    sakit: status === "sakit" ? 1 : 0,
    terlambat: status === "terlambat" ? 1 : 0,
  }
}

function flagsToStatus(row: { hadir: number; izin: number; sakit: number; terlambat: number }): AbsenPegawaiStatus {
  if (row.terlambat) return "terlambat"
  if (row.sakit) return "sakit"
  if (row.izin) return "izin"
  if (row.hadir) return "hadir"
  return "none"
}

function initAttendance(existing: { pegawai: number; hadir: number; izin: number; sakit: number; terlambat: number }[]) {
  const map: Record<number, StaffAttendanceRow> = {}
  const byPegawai = new Map(existing.map((e) => [e.pegawai, e]))
  for (const p of activeStaff.value) {
    const ex = byPegawai.get(p.id)
    map[p.id] = {
      pegawaiId: p.id,
      status: ex ? flagsToStatus(ex) : "hadir",
    }
  }
  attendance.value = map
}

async function loadDay() {
  loading.value = true
  try {
    const data = await absenPegawaiApi.list({ tanggal: tanggalStr.value })
    initAttendance(data.results)
  } catch (e) {
    notifyError(toast, e, "Gagal memuat absensi pegawai.")
  } finally {
    loading.value = false
  }
}

async function saveDay() {
  saving.value = true
  try {
    const items = Object.values(attendance.value).map((row) => ({
      pegawai: row.pegawaiId,
      ...statusToFlags(row.status),
    }))
    await absenPegawaiApi.bulkSave(tanggalStr.value, items)
    notifySuccess(toast, "Absensi pegawai tersimpan")
    await loadDay()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan absensi.")
  } finally {
    saving.value = false
  }
}

async function loadRekap() {
  loadingRekap.value = true
  try {
    rekap.value = await absenPegawaiApi.rekapBulanan(rekapBulan.value, rekapTahun.value)
  } catch (e) {
    notifyError(toast, e, "Gagal memuat rekap bulanan.")
  } finally {
    loadingRekap.value = false
  }
}

watch(tanggal, loadDay)

onMounted(async () => {
  try {
    pegawaiList.value = await pegawaiApi.listAll()
  } catch (e) {
    notifyError(toast, e, "Gagal memuat daftar pegawai.")
  }
  await loadDay()
})
</script>

<template>
  <PageLayout title="Absensi Pegawai" subtitle="Catat kehadiran harian pegawai sekolah">
    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="harian">Absensi Harian</Tab>
        <Tab value="rekap">Rekap Bulanan</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="harian">
          <div class="toolbar">
            <label>Tanggal</label>
            <DatePicker v-model="tanggal" date-format="yy-mm-dd" />
            <Button label="Simpan" icon="pi pi-check" :loading="saving" @click="saveDay" />
          </div>
          <StaffAttendanceGrid
            :staff="activeStaff"
            v-model="attendance"
            :readonly="loading"
          />
        </TabPanel>
        <TabPanel value="rekap">
          <div class="toolbar">
            <PeriodPicker v-model:bulan="rekapBulan" v-model:tahun="rekapTahun" />
            <Button label="Tampilkan" icon="pi pi-search" :loading="loadingRekap" @click="loadRekap" />
          </div>
          <DataTable :value="rekap" :loading="loadingRekap" striped-rows class="rekap-count-table">
            <template #empty>Klik Tampilkan untuk melihat rekap.</template>
            <Column
              field="nama"
              header="Pegawai"
              header-class="rekap-col--pegawai"
              body-class="rekap-col--pegawai"
            />
            <Column field="hadir" header="Hadir" header-class="count-col" body-class="count-col">
              <template #body="{ data }">
                <span class="count-val">{{ data.hadir }}</span>
              </template>
            </Column>
            <Column field="izin" header="Izin" header-class="count-col" body-class="count-col">
              <template #body="{ data }">
                <span class="count-val">{{ data.izin }}</span>
              </template>
            </Column>
            <Column field="sakit" header="Sakit" header-class="count-col" body-class="count-col">
              <template #body="{ data }">
                <span class="count-val">{{ data.sakit }}</span>
              </template>
            </Column>
            <Column field="terlambat" header="Terlambat" header-class="count-col" body-class="count-col">
              <template #body="{ data }">
                <span class="count-val">{{ data.terlambat }}</span>
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </PageLayout>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.toolbar label {
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
