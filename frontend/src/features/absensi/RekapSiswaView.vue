<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import Select from "primevue/select"
import ToggleSwitch from "primevue/toggleswitch"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"

import {
  buildRekapRows,
  countDistinctDays,
  downloadCsv,
  kelompokApi,
  kehadiranApi,
  monthDateRange,
  rekapAsOfDate,
  rekapToCsv,
  type RekapAbsensiRow,
} from "./api"
import { notifyError } from "@/core/errors"
import { siswaApi } from "@/features/siswa/api"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import {
  currentTahunPelajaran,
  defaultMonthForTa,
  isMonthInTa,
  listTahunPelajaran,
  type TahunPelajaran,
} from "@/shared/utils/tahunPelajaran"
import { useAuthStore } from "@/stores/auth"
import type { Kelompok, KehadiranSiswa } from "@/types/api"

const toast = useToast()
const router = useRouter()
const auth = useAuthStore()

const isTeacherReadOnly = computed(() =>
  auth.hasRole(["TeacherInCharge"]) && !auth.hasRole(["Administration"]),
)

const taList = listTahunPelajaran()
const activeTa = currentTahunPelajaran()
const selectedTa = ref<TahunPelajaran>(activeTa)
const archivedTaList = computed(() => taList.filter((t) => !t.isActive))

const bulan = ref(defaultMonthForTa(activeTa).bulan)
const tahun = ref(defaultMonthForTa(activeTa).tahun)
const kelompokList = ref<Kelompok[]>([])
const kelompokFilter = ref<number | null>(null)
const rows = ref<RekapAbsensiRow[]>([])
const rawRecords = ref<KehadiranSiswa[]>([])
const studentSnapshot = ref<{ id: number; nis: string | null; nama: string; kelompok: number | null }[]>([])
const loading = ref(false)
/** Default: hanya siswa yang sudah punya absensi di bulan ini */
const onlyWithData = ref(true)

const BULAN_LABEL = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const asOfDate = computed(() => rekapAsOfDate(bulan.value, tahun.value))

const periodLabel = computed(
  () => `${BULAN_LABEL[bulan.value - 1]} ${tahun.value}`,
)

const isCurrentMonth = computed(() => !!asOfDate.value)

const taOptions = computed(() =>
  taList.map((t) => ({ label: t.isActive ? `${t.kode} (aktif)` : t.kode, value: t.kode })),
)

const periodMinYear = computed(() => selectedTa.value.startYear)
const periodMaxYear = computed(() => selectedTa.value.endYear)

const distinctDays = computed(() => countDistinctDays(rawRecords.value, asOfDate.value))

const summaryText = computed(() => {
  const parts = [
    `${rows.value.length} siswa ditampilkan`,
    `${distinctDays.value} hari tercatat`,
  ]
  if (isCurrentMonth.value && asOfDate.value) {
    const [, , d] = asOfDate.value.split("-")
    parts.push(`s/d ${d} ${BULAN_LABEL[bulan.value - 1]}`)
  }
  return parts.join(" · ")
})

function applyTa(ta: TahunPelajaran) {
  selectedTa.value = ta
  const d = defaultMonthForTa(ta)
  bulan.value = d.bulan
  tahun.value = d.tahun
}

function onTaChange(kode: string) {
  const ta = taList.find((t) => t.kode === kode)
  if (ta) applyTa(ta)
}

function onPeriodChange() {
  if (!isMonthInTa(selectedTa.value, bulan.value, tahun.value)) {
    const d = defaultMonthForTa(selectedTa.value)
    bulan.value = d.bulan
    tahun.value = d.tahun
  }
}

const kelompokOptions = computed(() => [
  { label: "Semua kelompok", value: null as number | null },
  ...kelompokList.value.map((k) => ({ label: k.nama, value: k.id })),
])

function rebuildRows(
  students: { id: number; nis: string | null; nama: string; kelompok: number | null }[],
  kelompokNama: Map<number, string>,
  records: KehadiranSiswa[],
) {
  rows.value = buildRekapRows(students, kelompokNama, records, {
    asOfDate: asOfDate.value,
    onlyWithData: onlyWithData.value,
  })
}

async function load() {
  loading.value = true
  try {
    const range = monthDateRange(bulan.value, tahun.value)
    const params: Record<string, unknown> = { ...range }
    if (kelompokFilter.value) params.kelompok = kelompokFilter.value

    const [students, records, kelompoks] = await Promise.all([
      siswaApi.listAll({
        status: "aktif",
        ...(kelompokFilter.value ? { kelompok: kelompokFilter.value } : {}),
      }),
      kehadiranApi.listAll(params),
      kelompokApi.list(),
    ])

    kelompokList.value = kelompoks
    rawRecords.value = records
    studentSnapshot.value = students
    const kelompokNama = new Map(kelompoks.map((k) => [k.id, k.nama]))
    rebuildRows(students, kelompokNama, records)
  } catch (e) {
    notifyError(toast, e, "Gagal memuat rekap absensi.")
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  if (rows.value.length === 0) return
  const name = `rekap-absensi-${tahun.value}-${String(bulan.value).padStart(2, "0")}.csv`
  downloadCsv(name, rekapToCsv(rows.value))
}

watch(onlyWithData, () => {
  const kelompokNama = new Map(kelompokList.value.map((k) => [k.id, k.nama]))
  rebuildRows(studentSnapshot.value, kelompokNama, rawRecords.value)
})

watch([bulan, tahun, kelompokFilter], () => {
  onPeriodChange()
  load()
})
onMounted(load)
</script>

<template>
  <PageLayout
    title="Rekap Absensi Siswa"
    subtitle="Ringkasan kehadiran per bulan — diisi lewat menu Absensi Siswa"
  >
    <template #actions>
      <Button
        icon="pi pi-refresh"
        severity="secondary"
        text
        rounded
        aria-label="Muat ulang"
        :loading="loading"
        @click="load"
      />
      <Button
        label="Isi Absensi"
        icon="pi pi-calendar-plus"
        severity="secondary"
        @click="router.push('/absensi-siswa')"
      />
      <Button
        label="Export CSV"
        icon="pi pi-download"
        severity="secondary"
        outlined
        :disabled="rows.length === 0 || loading"
        @click="exportCsv"
      />
    </template>

    <template #filters>
      <Select
        :model-value="selectedTa.kode"
        :options="taOptions"
        option-label="label"
        option-value="value"
        placeholder="Tahun pelajaran"
        @update:model-value="onTaChange"
      />
      <PeriodPicker
        v-model:bulan="bulan"
        v-model:tahun="tahun"
        :min-year="periodMinYear"
        :max-year="periodMaxYear"
      />
      <Select
        v-model="kelompokFilter"
        :options="kelompokOptions"
        option-label="label"
        option-value="value"
        placeholder="Kelompok"
        show-clear
      />
    </template>

    <div class="rekap-toolbar">
      <div class="rekap-summary">
        <span class="rekap-summary__period">{{ periodLabel }} · TA {{ selectedTa.kode }}</span>
        <span class="rekap-summary__meta">{{ summaryText }}</span>
      </div>
      <label class="rekap-toggle">
        <ToggleSwitch v-model="onlyWithData" />
        <span>Hanya siswa yang sudah ada absensinya</span>
      </label>
    </div>

    <Message severity="info" :closable="false" class="rekap-hint">
      Angka = <strong>jumlah hari</strong> dalam bulan terpilih (contoh: Hadir 2 = hadir 2 hari berbeda).
      <template v-if="isCurrentMonth">
        Bulan ini hanya dihitung sampai <strong>hari ini</strong>, bukan sebulan penuh.
      </template>
      Isi atau ubah absensi harian di
      <a class="rekap-link" @click.prevent="router.push('/absensi-siswa')">Absensi Siswa</a>,
      lalu muat ulang halaman ini.
    </Message>

    <Message
      v-if="isTeacherReadOnly"
      severity="warn"
      :closable="false"
      class="teacher-banner"
    >
      Mode baca saja — hubungi Admin TU untuk koreksi absensi.
    </Message>

    <details v-if="archivedTaList.length" class="archive-details">
      <summary>Arsip tahun pelajaran lama</summary>
      <p>Pilih TA arsip lewat dropdown di atas (mis. 2025/2026), lalu pilih bulan Juli–Juni sesuai TA tersebut.</p>
    </details>

    <DataTable
      :value="rows"
      :loading="loading"
      data-key="siswaId"
      paginator
      :rows="20"
      striped-rows
      class="rekap-count-table"
    >
      <template #empty>
        <EmptyState
          :message="
            onlyWithData
              ? `Belum ada absensi ${periodLabel}. Buka Absensi Siswa, pilih kelompok & tanggal, lalu simpan.`
              : `Tidak ada siswa aktif untuk filter ini.`
          "
        />
      </template>

      <Column field="nis" header="NIS" header-class="rekap-col rekap-col--nis" body-class="rekap-col rekap-col--nis" />
      <Column field="nama" header="Nama Siswa" header-class="rekap-col rekap-col--nama" body-class="rekap-col rekap-col--nama" />
      <Column field="kelompok" header="Kelompok" header-class="rekap-col rekap-col--kel" body-class="rekap-col rekap-col--kel" />
      <Column field="hadir" header="Hadir" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.hadir === 0 }">{{ data.hadir }}</span>
        </template>
      </Column>
      <Column field="izin" header="Izin" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.izin === 0 }">{{ data.izin }}</span>
        </template>
      </Column>
      <Column field="sakit" header="Sakit" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.sakit === 0 }">{{ data.sakit }}</span>
        </template>
      </Column>
      <Column field="tidak_hadir" header="Alpa" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.tidak_hadir === 0 }">{{ data.tidak_hadir }}</span>
        </template>
      </Column>
      <Column field="katering" header="Katering" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.katering === 0 }">{{ data.katering }}</span>
        </template>
      </Column>
      <Column field="jemput_datang" header="Jemput Pagi" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.jemput_datang === 0 }">{{ data.jemput_datang }}</span>
        </template>
      </Column>
      <Column field="jemput_pulang" header="Jemput Sore" header-class="rekap-col rekap-col--count" body-class="rekap-col rekap-col--count">
        <template #body="{ data }">
          <span class="count-val" :class="{ zero: data.jemput_pulang === 0 }">{{ data.jemput_pulang }}</span>
        </template>
      </Column>
    </DataTable>
  </PageLayout>
</template>

<style scoped>
.rekap-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  background: var(--app-surface);
  border: 1px solid rgba(46, 42, 110, 0.08);
  border-radius: var(--bee-radius-lg);
}
.rekap-summary {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.rekap-summary__period {
  font-family: "Baloo 2", sans-serif;
  font-weight: 700;
  color: var(--bee-navy);
  font-size: 1.05rem;
}
.rekap-summary__meta {
  font-size: 0.82rem;
  color: var(--app-text-muted);
}
.rekap-toggle {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.85rem;
  color: var(--app-text);
  cursor: pointer;
  user-select: none;
}
.rekap-hint {
  margin-bottom: 1rem;
}
.rekap-link {
  color: var(--bee-magenta);
  font-weight: 700;
  cursor: pointer;
  text-decoration: underline;
}
.teacher-banner {
  margin-bottom: 1rem;
}
.archive-details {
  margin-bottom: 1rem;
  padding: 0.65rem 0.85rem;
  border-radius: var(--bee-radius-md);
  background: rgba(46, 42, 110, 0.04);
  font-size: 0.85rem;
  color: var(--app-text-muted);
}
.archive-details summary {
  cursor: pointer;
  font-weight: 700;
  color: var(--bee-navy);
}
.archive-details p {
  margin: 0.5rem 0 0;
  line-height: 1.45;
}
.count-val {
  font-weight: 700;
  color: var(--bee-navy);
  font-variant-numeric: tabular-nums;
}
.count-val.zero {
  color: var(--app-text-muted);
  font-weight: 500;
}
</style>
