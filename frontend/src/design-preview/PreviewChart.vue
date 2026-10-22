<script setup lang="ts">
import { computed } from "vue"
import Chart from "primevue/chart"
import type { ChartData, ChartOptions } from "chart.js"
import { formatRp } from "@/core/format"

const props = defineProps<{
  title: string
  subtitle: string
  description: string
  type: "line" | "bar" | "doughnut"
  data: ChartData
  options?: ChartOptions
  unit?: "money" | "count"
}>()
const palette = ["#2e2a6e", "#b51268", "#2d8c83", "#c38b32"]
const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  cutout: props.type === "doughnut" ? "72%" : undefined,
  ...props.options,
  plugins: {
    legend: { display: props.type !== "doughnut", position: "bottom" as const, labels: { usePointStyle: true, pointStyleWidth: 8, boxWidth: 8, boxHeight: 8, padding: 20, color: "#56647a", font: { family: "Nunito Sans", size: 12 } } },
    tooltip: { callbacks: { label: (context: { dataset: { label?: string }; parsed: number | { x: number; y: number } }) => {
      const parsed = context.parsed
      const value = typeof parsed === "number" ? parsed : props.options?.indexAxis === "y" ? parsed.x : parsed.y
      return `${context.dataset.label ?? "Nilai"}: ${props.unit === "count" ? value : formatRp(value)}`
    } } },
    ...props.options?.plugins,
  },
}))
function display(value: unknown) {
  return props.unit === "count" ? String(value) : formatRp(Number(value))
}
</script>

<template>
  <section class="panel chart-card">
    <header class="panel-heading"><div><h2>{{ title }}</h2><p>{{ subtitle }}</p></div><slot name="actions" /></header>
    <slot name="summary" />
    <div class="chart-body" :class="{ 'chart-body--donut': type === 'doughnut' }">
      <Chart :type="type" :data="data" :options="options" :canvas-props="{ role: 'img', 'aria-label': `${title}. ${description}` }" />
      <ul v-if="type === 'doughnut'" class="composition-list">
        <li v-for="(label, i) in data.labels" :key="String(label)"><span><i :style="{ background: palette[i % palette.length] }" />{{ label }}</span><strong>{{ display(data.datasets[0]?.data[i]) }}</strong></li>
      </ul>
    </div>
    <p class="chart-description">{{ description }}</p>
    <details class="chart-data"><summary>Lihat angka {{ title.toLowerCase() }}</summary><div class="table-scroll"><table><caption class="sr-only">Angka contoh {{ title }}</caption><thead><tr><th scope="col">{{ type === 'doughnut' || options.indexAxis === 'y' ? 'Kategori' : 'Periode' }}</th><th v-for="(set, i) in data.datasets" :key="i" scope="col" class="num">{{ set.label ?? 'Nominal' }}</th></tr></thead><tbody><tr v-for="(label, i) in data.labels" :key="String(label)"><th scope="row">{{ label }}</th><td v-for="(set, j) in data.datasets" :key="j" class="num">{{ display(set.data[i]) }}</td></tr></tbody></table></div></details>
  </section>
</template>
