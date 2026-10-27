<script setup lang="ts">
import { computed } from 'vue'
import Tag from 'primevue/tag'
import type { Gaji, Pegawai } from '@/types/api'
import { earnings, money } from './payroll'
const props=defineProps<{slip:Gaji;pegawai?:Pegawai|null;bulanLabel:string}>()
const nonzero=(value:string|null|undefined)=>value==null||value===''||!Number.isFinite(Number(value))||Number(value)!==0
const lines=computed(()=>earnings.map(field=>({label:field.label,value:props.slip[field.key]})).filter(line=>nonzero(line.value)))
const deductions=computed(()=>[{label:'Potongan kasbon',value:props.slip.potongan_pinjaman},{label:'Potongan asuransi',value:props.slip.potongan_asuransi}].filter(line=>nonzero(line.value)))
</script>
<template>
  <article class="salary-slip">
    <header class="salary-slip-brand"><img src="/logo-lebah.svg" alt="" width="40" height="40"><div><strong>RA Lebah Madu</strong><p>Slip gaji</p></div></header>
    <section class="salary-slip-person"><div><h3>{{ pegawai?.nama??`Pegawai #${slip.pegawai}` }}</h3><p>{{ bulanLabel }}</p><small v-if="pegawai?.jabatan">{{ pegawai.jabatan }}</small><small v-if="pegawai?.nip">NIP {{ pegawai.nip }}</small></div><Tag :value="slip.jurnal?'Jurnal dibuat':'Belum dijurnal'" :severity="slip.jurnal?'info':'warn'" /></section>
    <section class="salary-slip-net"><span>Gaji netto</span><strong :class="{'is-negative':Number(slip.total_netto)<0}">{{ money(slip.total_netto) }}</strong><small>Bruto {{ money(slip.total_bruto) }} dikurangi potongan {{ money(slip.total_potongan) }}.</small></section>
    <section class="salary-slip-section"><h4>Pendapatan</h4><table><caption class="employee-sr-only">Rincian pendapatan gaji</caption><tbody><tr v-for="line in lines" :key="line.label"><th scope="row">{{ line.label }}</th><td>{{ money(line.value) }}</td></tr><tr v-if="!lines.length"><th scope="row">Komponen pendapatan</th><td>{{ money(0) }}</td></tr></tbody><tfoot><tr><th scope="row">Total bruto</th><td>{{ money(slip.total_bruto) }}</td></tr></tfoot></table></section>
    <section class="salary-slip-section"><h4>Potongan</h4><table><caption class="employee-sr-only">Rincian potongan gaji</caption><tbody><tr v-for="line in deductions" :key="line.label"><th scope="row">{{ line.label }}</th><td>{{ money(line.value) }}</td></tr><tr v-if="!deductions.length"><th scope="row">Komponen potongan</th><td>{{ money(0) }}</td></tr></tbody><tfoot><tr><th scope="row">Total potongan</th><td>{{ money(slip.total_potongan) }}</td></tr></tfoot></table></section>
    <p class="salary-slip-note">Hari hadir tercatat: {{ slip.hari_hadir }}. Nominal mengikuti slip tersimpan; pembuatan jurnal dilakukan terpisah.</p>
  </article>
</template>
<style scoped>
.salary-slip { color: var(--app-text); font-size: var(--bee-type-ui); }
.salary-slip-brand { display: flex; align-items: center; gap: var(--bee-space-3); padding-bottom: var(--bee-space-5); border-bottom: 1px solid var(--app-border); }.salary-slip-brand strong { font-weight: 600; font-size: var(--bee-type-body); }.salary-slip-brand p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); }
.salary-slip-person { display: flex; align-items: start; justify-content: space-between; flex-wrap: wrap; gap: var(--bee-space-3); padding-block: var(--bee-space-5); }.salary-slip-person>div { flex: 1 1 180px; min-width: 0; }.salary-slip-person h3 { font-size: var(--bee-type-section); font-weight: 600; overflow-wrap: anywhere; margin: 0; }.salary-slip-person p { margin: var(--bee-space-2) 0; color: var(--app-text-muted); }.salary-slip-person small { display: block; font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.salary-slip-net { display: grid; gap: var(--bee-space-2); padding: var(--bee-space-4); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); }.salary-slip-net>span { font-size: var(--bee-type-caption); color: var(--app-text-muted); }.salary-slip-net strong { font-size: var(--bee-type-number-secondary); font-weight: 600; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }.salary-slip-net small { font-size: var(--bee-type-caption); color: var(--app-text-muted); }.salary-slip-net .is-negative { color: var(--bee-color-critical); }
.salary-slip-section { margin-top: var(--bee-space-5); }.salary-slip-section h4 { font-size: var(--bee-type-body); font-weight: 500; margin: 0 0 var(--bee-space-2); }.salary-slip-section table { width: 100%; border-collapse: collapse; }.salary-slip-section th { text-align: start; font-weight: 400; }.salary-slip-section td { text-align: end; font-variant-numeric: tabular-nums; white-space: nowrap; }.salary-slip-section th,.salary-slip-section td { padding: var(--bee-space-3) 0; border-bottom: 1px solid var(--app-border); }.salary-slip-section th { padding-inline-end: var(--bee-space-3); }.salary-slip-section tfoot th,.salary-slip-section tfoot td { font-weight: 500; border-bottom: 0; }
.salary-slip-note { font-size: var(--bee-type-caption); color: var(--app-text-muted); margin: var(--bee-space-5) 0 0; line-height: 1.6; }
@media print { .salary-slip-net { background: transparent; border: 1px solid var(--app-border); }.salary-slip-brand,.salary-slip-person,.salary-slip-net,.salary-slip-section { break-inside: avoid; } }
</style>
