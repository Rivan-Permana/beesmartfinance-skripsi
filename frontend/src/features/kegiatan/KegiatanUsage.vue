<script setup lang="ts">
import { computed } from "vue"
import ProgressBar from "primevue/progressbar"
import { formatRp } from "@/core/format"
import { budgetUsage } from "./presentation"
const props=defineProps<{pagu:string|number;realisasi:string|number;ratio:number}>()
const usage=computed(()=>budgetUsage(props.pagu,props.ratio))
</script>
<template>
  <div class="kegiatan-usage"><ProgressBar v-if="usage" :value="usage.value" :show-value="false" :aria-label="`Realisasi ${formatRp(realisasi)} dari pagu ${formatRp(pagu)}`" :aria-valuetext="`${usage.label} dari pagu`" /><small>{{ usage ? `${usage.label} dari pagu` : 'Persentase tidak tersedia' }}</small></div>
</template>
<style scoped>
.kegiatan-usage { min-width: 110px; }.kegiatan-usage :deep(.p-progressbar) { height: 6px; margin-top: var(--bee-space-2); }.kegiatan-usage :deep(.p-progressbar-value) { transition: none; background: var(--bee-color-chart-teal); }.kegiatan-usage small { display: block; margin-top: var(--bee-space-1); font-size: var(--bee-type-caption); color: var(--app-text-muted); }
</style>
