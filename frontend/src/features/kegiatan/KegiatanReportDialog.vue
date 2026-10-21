<script setup lang="ts">
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { LaporanKegiatan } from "@/types/api"
import KegiatanUsage from "./KegiatanUsage.vue"
defineProps<{report:LaporanKegiatan|null}>()
const visible=defineModel<boolean>({default:false})
</script>
<template>
  <Dialog v-model:visible="visible" header="Laporan kegiatan" modal :draggable="false" :style="{width:'640px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup laporan kegiatan'}"><template #closeicon><Icon name="x" /></template>
    <section v-if="report" class="kegiatan-report"><h3>{{ report.kegiatan }}</h3><dl class="report-totals"><div><dt>Pagu</dt><dd>{{ formatRp(report.pagu) }}</dd></div><div><dt>Realisasi</dt><dd>{{ formatRp(report.realisasi) }}</dd></div><div><dt>Sisa pagu</dt><dd>{{ formatRp(report.sisa_pagu) }}</dd></div></dl><KegiatanUsage :pagu="report.pagu" :realisasi="report.realisasi" :ratio="report.rasio_utilisasi" /><h4>Rincian realisasi</h4><div v-if="!report.rincian.length" class="report-empty"><Icon name="file-text" /><p>Belum ada realisasi tercatat untuk kegiatan ini.</p></div><ol v-else class="report-records"><li v-for="(row,index) in report.rincian" :key="index"><div><strong>{{ row.deskripsi || 'Tanpa keterangan' }}</strong><small>{{ row.tanggal.split('-').reverse().join('/') }}</small></div><span>{{ formatRp(row.nominal) }}</span></li></ol></section>
    <template #footer><Button label="Tutup" severity="secondary" @click="visible=false" /></template>
  </Dialog>
</template>
<style scoped>
.kegiatan-report h3 { font-size: var(--bee-type-section); font-weight: 500; margin-bottom: var(--bee-space-5); }.report-totals { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: var(--bee-space-4); margin: 0 0 var(--bee-space-5); }.report-totals dt { font-size: var(--bee-type-caption); color: var(--app-text-muted); }.report-totals dd { font-variant-numeric: tabular-nums; margin: var(--bee-space-1) 0 0; font-weight: 500; font-size: var(--bee-type-body); overflow-wrap: anywhere; }.kegiatan-report h4 { font-size: var(--bee-type-body); font-weight: 500; margin: var(--bee-space-6) 0 var(--bee-space-4); }.report-records { list-style: none; padding: 0; margin: 0; }.report-records li { display: flex; justify-content: space-between; align-items: baseline; gap: var(--bee-space-4); padding: var(--bee-space-4) 0; border-top: 1px solid var(--app-border); }.report-records li > div { min-width: 0; }.report-records strong { font-weight: 400; overflow-wrap: anywhere; }.report-records small { display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-top: var(--bee-space-1); }.report-records li > span { font-variant-numeric: tabular-nums; white-space: nowrap; }.report-empty { display: flex; align-items: center; gap: var(--bee-space-3); color: var(--app-text-muted); padding: var(--bee-space-4) 0; }.report-empty p { margin: 0; }
@media(max-width:520px) { .report-totals { grid-template-columns: minmax(0,1fr); gap: var(--bee-space-3); }.report-totals > div { display: flex; justify-content: space-between; gap: var(--bee-space-3); }.report-totals dd { margin: 0; } }
</style>
