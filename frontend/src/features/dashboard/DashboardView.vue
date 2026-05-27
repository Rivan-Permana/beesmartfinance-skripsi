<script setup lang="ts">
import Message from "primevue/message"
import ProgressBar from "primevue/progressbar"
import { computed, onMounted, ref } from "vue"

import { dashboardApi } from "./api"
import type { DashboardRingkasan } from "@/types/api"

const data = ref<DashboardRingkasan | null>(null)
const loading = ref(true)
const error = ref("")

function rp(v: string | number | undefined) {
  return "Rp " + Number(v ?? 0).toLocaleString("id-ID")
}

const utilisasi = computed(() => {
  const pagu = Number(data.value?.anggaran.pagu ?? 0)
  const real = Number(data.value?.anggaran.realisasi ?? 0)
  return pagu > 0 ? Math.round((real / pagu) * 100) : 0
})

const cards = computed(() => [
  { label: "Kas & Bank", value: rp(data.value?.kas), icon: "pi pi-wallet", tone: "navy" },
  { label: "Total Pendapatan", value: rp(data.value?.total_pendapatan), icon: "pi pi-arrow-down-left", tone: "green" },
  { label: "Total Beban", value: rp(data.value?.total_beban), icon: "pi pi-arrow-up-right", tone: "magenta" },
  { label: "Surplus / Defisit", value: rp(data.value?.surplus_defisit), icon: "pi pi-chart-line", tone: "orange" },
])

onMounted(async () => {
  try {
    data.value = await dashboardApi.ringkasan()
  } catch {
    error.value = "Gagal memuat ringkasan (butuh akses Finance/Principal)."
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <h1>Dashboard</h1>

    <Message v-if="error" severity="warn" :closable="false">{{ error }}</Message>

    <template v-else>
      <div class="kpi-grid">
        <div v-for="c in cards" :key="c.label" class="kpi" :class="c.tone">
          <i :class="c.icon" />
          <div>
            <div class="kpi-label">{{ c.label }}</div>
            <div class="kpi-value">{{ loading ? "…" : c.value }}</div>
          </div>
        </div>
      </div>

      <div class="budget">
        <div class="budget-head">
          <h3>Realisasi Anggaran</h3>
          <span>{{ utilisasi }}% terpakai</span>
        </div>
        <ProgressBar :value="utilisasi" />
        <div class="budget-meta">
          <span>Pagu: {{ rp(data?.anggaran.pagu) }}</span>
          <span>Realisasi: {{ rp(data?.anggaran.realisasi) }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 1rem 0 1.5rem;
}
.kpi {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 14px;
  padding: 1.1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.kpi i {
  font-size: 1.4rem;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
}
.kpi.navy i { background: var(--bee-navy); }
.kpi.magenta i { background: var(--bee-magenta); }
.kpi.orange i { background: var(--bee-orange); }
.kpi.green i { background: #2e9e5b; }
.kpi-label {
  font-size: 0.8rem;
  color: var(--app-text-muted);
}
.kpi-value {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--bee-navy);
}
.budget {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 14px;
  padding: 1.25rem;
  max-width: 640px;
}
.budget-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.budget-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 0.6rem;
  font-size: 0.85rem;
  color: var(--app-text-muted);
}
</style>
