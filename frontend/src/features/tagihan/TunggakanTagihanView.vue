<script setup lang="ts">
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref } from "vue"

import { tagihanApi } from "./api"
import { notifyError } from "@/core/errors"
import { formatRp } from "@/core/format"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import type { Tagihan } from "@/types/api"

const toast = useToast()
const rows = ref<Tagihan[]>([])
const loading = ref(false)

const filterSiswa = ref<number | null>(null)
const usePeriodFilter = ref(false)
const filterBulan = ref(new Date().getMonth() + 1)
const filterTahun = ref(new Date().getFullYear())

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const outstanding = computed(() =>
  rows.value.filter((t) => {
    if (!t.perlu_rekonsiliasi && t.status !== "BELUM" && t.status !== "SEBAGIAN") return false
    if (filterSiswa.value && t.siswa !== filterSiswa.value) return false
    if (usePeriodFilter.value) {
      if (t.periode_tahun !== filterTahun.value) return false
      if (t.periode_bulan !== filterBulan.value) return false
    }
    return true
  }),
)

const totalTunggakan = computed(() =>
  outstanding.value.reduce((s, t) => s + Number(t.sisa_tagihan ?? 0), 0),
)

async function load() {
  loading.value = true
  try {
    rows.value = await tagihanApi.listAll()
  } catch (e) {
    notifyError(toast, e, "Gagal memuat tunggakan tagihan.")
  } finally {
    loading.value = false
  }
}

function siswaNama(t: Tagihan) {
  return t.siswa_nama ?? `Siswa #${t.siswa}`
}

const siswaFilterOptions = computed(() => {
  const map = new Map<number, string>()
  for (const t of rows.value) {
    if (!map.has(t.siswa)) map.set(t.siswa, siswaNama(t))
  }
  return [...map.entries()]
    .map(([id, nama]) => ({ id, nama }))
    .sort((a, b) => a.nama.localeCompare(b.nama))
})

function periodeLabel(t: Tagihan) {
  return `${BULAN[t.periode_bulan - 1]} ${t.periode_tahun}`
}

onMounted(load)
</script>

<template>
  <PageLayout
    title="Tunggakan Tagihan"
    subtitle="Pantau tagihan belum lunas — koordinasi dengan Admin TU untuk penagihan."
  >
    <template #filters>
      <Select
        v-model="filterSiswa"
        :options="siswaFilterOptions"
        option-label="nama"
        option-value="id"
        filter
        show-clear
        placeholder="Semua siswa"
        style="min-width: 14rem"
      />
      <label class="period-toggle">
        <ToggleSwitch v-model="usePeriodFilter" />
        Filter periode
      </label>
      <PeriodPicker
        v-if="usePeriodFilter"
        v-model:bulan="filterBulan"
        v-model:tahun="filterTahun"
      />
    </template>

    <Message severity="info" :closable="false" class="mb">
      <strong>Hanya untuk pantau.</strong> Anda bisa lihat tagihan yang belum lunas di sini.
      Untuk mencatat pembayaran, Admin TU menggunakan menu <strong>Tagihan</strong> (bukan halaman ini).
    </Message>

    <div v-if="outstanding.length" class="summary">
      Total tunggakan: <strong>{{ formatRp(totalTunggakan) }}</strong>
      ({{ outstanding.length }} tagihan)
      <span v-if="outstanding.some((t) => t.perlu_rekonsiliasi)"> — nominal pembayaran lama yang belum direkonsiliasi belum termasuk.</span>
    </div>

    <DataTable
      :value="outstanding"
      :loading="loading"
      paginator
      :rows="10"
      data-key="id"
      striped-rows
    >
      <template #empty>
        <EmptyState message="Tidak ada tagihan outstanding untuk filter ini." />
      </template>
      <Column header="Siswa">
        <template #body="{ data }">{{ siswaNama(data) }}</template>
      </Column>
      <Column header="Periode">
        <template #body="{ data }">{{ periodeLabel(data) }}</template>
      </Column>
      <Column header="Sisa tagihan">
        <template #body="{ data }">
          <span class="tabular-nums">{{ data.sisa_tagihan === null ? 'Perlu rekonsiliasi' : formatRp(data.sisa_tagihan) }}</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.perlu_rekonsiliasi ? 'Perlu rekonsiliasi' : data.status" :severity="data.status === 'SEBAGIAN' || data.perlu_rekonsiliasi ? 'warn' : 'danger'" />
        </template>
      </Column>
    </DataTable>
  </PageLayout>
</template>

<style scoped>
.mb {
  margin-bottom: 1rem;
}
.summary {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: var(--app-text-muted);
}
.summary strong {
  color: var(--app-text);
  font-variant-numeric: tabular-nums;
}
.period-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
}
</style>
