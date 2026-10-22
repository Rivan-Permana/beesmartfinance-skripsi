<script setup lang="ts">
import Select from "primevue/select"
import Icon from "./PhosphorIcon.vue"
import { computed } from "vue"

const bulan = defineModel<number>("bulan", { default: () => new Date().getMonth() + 1 })
const tahun = defineModel<number>("tahun", { default: () => new Date().getFullYear() })

const props = withDefaults(
  defineProps<{
    /** Tahun awal dropdown (default: 2024 untuk arsip legacy). */
    minYear?: number
    /** Tahun akhir dropdown (default: tahun berjalan + 1). */
    maxYear?: number
  }>(),
  {
    minYear: 2024,
    maxYear: () => new Date().getFullYear() + 1,
  },
)

const BULAN = [
  { label: "Januari", value: 1 }, { label: "Februari", value: 2 }, { label: "Maret", value: 3 },
  { label: "April", value: 4 }, { label: "Mei", value: 5 }, { label: "Juni", value: 6 },
  { label: "Juli", value: 7 }, { label: "Agustus", value: 8 }, { label: "September", value: 9 },
  { label: "Oktober", value: 10 }, { label: "November", value: 11 }, { label: "Desember", value: 12 },
]

const tahunOptions = computed(() => {
  const end = props.maxYear ?? new Date().getFullYear() + 1
  const start = props.minYear ?? 2024
  const opts: { label: string; value: number }[] = []
  for (let y = end; y >= start; y -= 1) {
    opts.push({ label: String(y), value: y })
  }
  return opts
})
</script>

<template>
  <div class="period-picker">
    <Select v-model="bulan" :options="BULAN" option-label="label" option-value="value" placeholder="Bulan" aria-label="Bulan"><template #dropdownicon><Icon name="caret-down" /></template></Select>
    <Select v-model="tahun" :options="tahunOptions" option-label="label" option-value="value" placeholder="Tahun" aria-label="Tahun"><template #dropdownicon><Icon name="caret-down" /></template></Select>
  </div>
</template>

<style scoped>
.period-picker {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.period-picker :deep(.p-select) {
  min-width: 9rem;
}
</style>
