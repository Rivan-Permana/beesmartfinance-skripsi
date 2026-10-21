<script setup lang="ts">
import { formatRp } from "@/core/format"
defineProps<{
  labels: string[]
  series: { label: string; data: (number | string | null)[] }[]
  unit?: "percent" | "money"
}>()
</script>

<template>
  <details class="chart-data">
    <summary>Lihat tabel angka</summary>
    <div tabindex="0" role="region" aria-label="Angka pada grafik" class="chart-data-scroll">
      <table><thead><tr><th scope="col">Keterangan</th><th v-for="item in series" :key="item.label" scope="col">{{ item.label }}</th></tr></thead>
        <tbody><tr v-for="(label, index) in labels" :key="`${label}-${index}`"><th scope="row">{{ label }}</th><td v-for="item in series" :key="item.label">{{ item.data[index] == null ? 'Belum diketahui' : unit === 'percent' ? `${item.data[index]}%` : formatRp(item.data[index]) }}</td></tr></tbody>
      </table>
    </div>
  </details>
</template>

<style scoped>
.chart-data { margin-top: var(--bee-space-4); font-size: var(--bee-type-caption); }
summary { padding-block: var(--bee-space-3); min-height: 44px; cursor: pointer; color: var(--bee-color-muted); }
.chart-data-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th,td { padding: var(--bee-space-3); border-bottom: 1px solid var(--bee-color-border); text-align: end; font-variant-numeric: tabular-nums; white-space: nowrap; }
th:first-child { text-align: start; white-space: normal; } th { font-weight: 500; }
</style>
