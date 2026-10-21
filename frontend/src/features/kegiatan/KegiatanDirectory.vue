<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Menu from "primevue/menu"
import Message from "primevue/message"
import Paginator from "primevue/paginator"
import Select from "primevue/select"
import Tag from "primevue/tag"
import SearchField from "@/shared/components/SearchField.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import { formatRp } from "@/core/format"
import type { Kegiatan, KegiatanStatus, PeriodeAkuntansi } from "@/types/api"
import { KEGIATAN_STATUS, kegiatanStatusOptions } from "./presentation"
import KegiatanUsage from "./KegiatanUsage.vue"
const props=defineProps<{rows:Kegiatan[];periods:PeriodeAkuntansi[];loading?:boolean;error?:string;periodError?:boolean;canManage?:boolean;canRecord?:boolean}>()
const period=defineModel<number|null>("period",{default:null})
const emit=defineEmits<{create:[];edit:[row:Kegiatan];remove:[row:Kegiatan];record:[row:Kegiatan];report:[row:Kegiatan];retry:[];reloadPeriods:[]}>()
const status=ref<KegiatanStatus|null>(null)
const first=ref(0)
const menu=ref<InstanceType<typeof Menu>|null>(null)
const active=ref<Kegiatan|null>(null)
const menuOpen=ref(false)
const {query,filtered:searched}=useTableSearch(()=>props.rows,row=>[row.nama,row.periode_kode,KEGIATAN_STATUS[row.status].label])
const filtered=computed(()=>searched.value.filter(row=>!status.value || row.status===status.value))
const pageRows=computed(()=>filtered.value.slice(first.value,first.value+10))
const hasFilter=computed(()=>Boolean(query.value.trim() || status.value || period.value))
watch([query,status,period,()=>props.rows],()=>{first.value=0})
function reset(){query.value="";status.value=null;period.value=null}
const menuItems=computed(()=>{
  const row=active.value
  if(!row || !props.canManage) return []
  return [{label:"Ubah kegiatan",icon:"pencil-simple",command:()=>emit("edit",row)},...(Number(row.realisasi)===0?[{label:"Hapus kegiatan",icon:"trash",class:"kegiatan-action-danger",command:()=>emit("remove",row)}]:[])]
})
function openActions(event:Event,row:Kegiatan){active.value=row;menu.value?.toggle(event)}
function periodLabel(row:Kegiatan){return row.periode_kode || (row.periode===null?"Tanpa tahun pelajaran":"Tahun pelajaran belum dimuat")}
</script>

<template>
  <section class="kegiatan-directory" aria-label="Daftar kegiatan sekolah" :aria-busy="loading">
    <div class="kegiatan-heading"><h2>Daftar kegiatan</h2><p>Bandingkan pagu, realisasi, dan sisa anggaran pada setiap kegiatan.</p></div>
    <div class="kegiatan-toolbar"><div class="kegiatan-field kegiatan-search"><label for="kegiatan-search">Cari kegiatan</label><SearchField input-id="kegiatan-search" v-model="query" placeholder="Nama atau tahun pelajaran" hint="Cari nama kegiatan, tahun pelajaran, atau status" /></div><div class="kegiatan-field"><label for="kegiatan-period">Tahun pelajaran</label><Select :key="(periodError) ? 'locked' : 'editable'" input-id="kegiatan-period" v-model="period" :options="periods" option-label="kode" option-value="id" placeholder="Semua tahun pelajaran" show-clear :disabled="periodError"><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div><div class="kegiatan-field"><label for="kegiatan-status">Status kegiatan</label><Select input-id="kegiatan-status" v-model="status" :options="kegiatanStatusOptions" option-label="label" option-value="value" placeholder="Semua status" show-clear><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div></div>
    <div v-if="error" class="kegiatan-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang kegiatan" severity="secondary" @click="emit('retry')" /></div>
    <div v-if="periodError" class="kegiatan-notice"><Message severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>Pilihan tahun pelajaran belum berhasil dimuat. Daftar kegiatan tetap tersedia.</Message><Button label="Muat ulang tahun pelajaran" severity="secondary" @click="emit('reloadPeriods')" /></div>
    <div class="kegiatan-results"><p role="status">{{ loading ? 'Memuat kegiatan…' : error ? 'Kegiatan belum tersedia' : filtered.length ? `Menampilkan ${first+1}–${Math.min(first+10,filtered.length)} dari ${filtered.length} kegiatan` : 'Tidak ada kegiatan ditampilkan' }}</p><Button v-if="hasFilter" label="Hapus filter" text @click="reset" /></div>
    <div v-if="loading" class="kegiatan-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan daftar kegiatan</p></div>
    <div v-else-if="!error && !filtered.length" class="kegiatan-empty"><Icon :name="hasFilter?'magnifying-glass':'flag'" /><h3>{{ hasFilter?'Tidak ada kegiatan yang cocok':'Belum ada kegiatan' }}</h3><p>{{ hasFilter?'Coba kata kunci, status, atau tahun pelajaran lain.':canManage?'Buat kegiatan untuk menetapkan pagu dan penanggung jawab.':'Kegiatan yang dibuat kepala sekolah akan muncul di sini.' }}</p><Button v-if="hasFilter || canManage" :label="hasFilter?'Hapus filter':'Buat kegiatan'" severity="secondary" @click="hasFilter?reset():emit('create')" /></div>
    <template v-else-if="!error">
      <DataTable class="kegiatan-desktop" :value="pageRows" data-key="id" :table-style="{minWidth:'1000px'}" :pt="{tableContainer:{tabindex:0,role:'region','aria-label':'Tabel pagu dan realisasi kegiatan'}}">
        <Column header="Kegiatan"><template #body="{data}"><strong class="kegiatan-name">{{ data.nama }}</strong><small class="kegiatan-secondary">{{ periodLabel(data) }}</small><Tag :value="KEGIATAN_STATUS[data.status as KegiatanStatus].label" :severity="KEGIATAN_STATUS[data.status as KegiatanStatus].severity" class="kegiatan-status-tag" /></template></Column>
        <Column header="Pagu" header-class="bee-numeric" body-class="bee-numeric"><template #body="{data}">{{ formatRp(data.pagu) }}</template></Column>
        <Column header="Realisasi" header-class="bee-numeric" body-class="bee-numeric"><template #body="{data}">{{ formatRp(data.realisasi) }}<KegiatanUsage :pagu="data.pagu" :realisasi="data.realisasi" :ratio="data.rasio_utilisasi" /></template></Column>
        <Column header="Sisa pagu" header-class="bee-numeric" body-class="bee-numeric"><template #body="{data}"><strong class="kegiatan-amount" :class="{'kegiatan-over':Number(data.sisa_pagu)<0}">{{ formatRp(data.sisa_pagu) }}</strong></template></Column>
        <Column header="Tindakan" header-class="kegiatan-actions-column" body-class="kegiatan-actions-column"><template #body="{data}"><div class="kegiatan-actions"><Button v-if="canRecord" label="Catat realisasi" severity="secondary" :disabled="Number(data.sisa_pagu)<=0" :aria-label="`Catat realisasi ${data.nama}`" :title="Number(data.sisa_pagu)<=0?'Sisa pagu sudah habis':undefined" @click="emit('record',data)" /><Button label="Laporan" severity="secondary" text :aria-label="`Laporan ${data.nama}`" @click="emit('report',data)" /><Button v-if="canManage" severity="secondary" text :aria-label="`Tindakan kegiatan ${data.nama}`" aria-controls="kegiatan-action-menu" aria-haspopup="menu" :aria-expanded="menuOpen && active?.id===data.id" @click="openActions($event,data)"><template #icon><Icon name="caret-down" /></template></Button></div><small v-if="canRecord && Number(data.sisa_pagu)<=0" class="kegiatan-secondary">Sisa pagu sudah habis</small></template></Column>
      </DataTable>
      <ul class="kegiatan-mobile" aria-label="Kegiatan sekolah"><li v-for="row in pageRows" :key="row.id"><div class="kegiatan-mobile-heading"><div><strong class="kegiatan-name">{{ row.nama }}</strong><small class="kegiatan-secondary">{{ periodLabel(row) }}</small></div><Tag :value="KEGIATAN_STATUS[row.status].label" :severity="KEGIATAN_STATUS[row.status].severity" /></div><dl><div><dt>Pagu</dt><dd>{{ formatRp(row.pagu) }}</dd></div><div><dt>Realisasi</dt><dd>{{ formatRp(row.realisasi) }}</dd></div><div><dt>Sisa pagu</dt><dd class="kegiatan-amount" :class="{'kegiatan-over':Number(row.sisa_pagu)<0}">{{ formatRp(row.sisa_pagu) }}</dd></div></dl><KegiatanUsage :pagu="row.pagu" :realisasi="row.realisasi" :ratio="row.rasio_utilisasi" /><div class="kegiatan-mobile-actions"><Button v-if="canRecord" label="Catat realisasi" severity="secondary" :disabled="Number(row.sisa_pagu)<=0" @click="emit('record',row)" /><Button label="Laporan" severity="secondary" text :aria-label="`Laporan ${row.nama}`" @click="emit('report',row)" /><Button v-if="canManage" severity="secondary" text :aria-label="`Tindakan kegiatan ${row.nama}`" aria-controls="kegiatan-action-menu" aria-haspopup="menu" :aria-expanded="menuOpen && active?.id===row.id" @click="openActions($event,row)"><template #icon><Icon name="caret-down" /></template></Button></div><small v-if="canRecord && Number(row.sisa_pagu)<=0" class="kegiatan-secondary">Sisa pagu sudah habis</small></li></ul>
      <Paginator v-if="filtered.length>10" v-model:first="first" :rows="10" :total-records="filtered.length" :page-link-size="3" template="PrevPageLink PageLinks NextPageLink"><template #prevpagelinkicon><Icon name="caret-left" /></template><template #nextpagelinkicon><Icon name="caret-right" /></template></Paginator>
    </template>
    <p class="kegiatan-footnote"><Icon name="info" /><span>Persentase membandingkan realisasi dengan pagu kegiatan. Catatan realisasi diteruskan ke proses pencatatan keuangan.</span></p>
    <Menu id="kegiatan-action-menu" ref="menu" :model="menuItems" class="kegiatan-action-menu" popup @show="menuOpen=true" @hide="menuOpen=false"><template #item="{item,props:itemProps}"><a v-bind="itemProps.action"><Icon v-if="item.icon" :name="item.icon" /><span>{{ item.label }}</span></a></template></Menu>
  </section>
</template>
<style scoped>
.kegiatan-directory { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: clip; }.kegiatan-heading { padding: var(--bee-space-5); }.kegiatan-heading h2 { font-size: var(--bee-type-section); font-weight: 600; }.kegiatan-heading p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); }
.kegiatan-toolbar { display: flex; flex-wrap: wrap; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-5); }.kegiatan-field { display: flex; flex-direction: column; gap: var(--bee-space-2); flex: 1 1 180px; min-width: 0; }.kegiatan-search { flex: 2 1 260px; }.kegiatan-search :deep(.bee-search-field) { flex: none; min-width: 0; }.kegiatan-field label { font-size: var(--bee-type-caption); font-weight: 500; }
.kegiatan-results { display: flex; justify-content: space-between; align-items: center; gap: var(--bee-space-3); min-height: 52px; padding: 0 var(--bee-space-5); border-top: 1px solid var(--app-border); }.kegiatan-results p { font-size: var(--bee-type-caption); color: var(--app-text-muted); }.kegiatan-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.kegiatan-name { font-weight: 500; overflow-wrap: anywhere; }.kegiatan-secondary { display: block; font-size: var(--bee-type-caption); color: var(--app-text-muted); margin-top: var(--bee-space-1); }.kegiatan-status-tag { margin-top: var(--bee-space-2); }.kegiatan-amount { font-weight: 500; font-variant-numeric: tabular-nums; }.kegiatan-over { color: var(--bee-color-critical); }
:deep(.kegiatan-actions-column) { min-width: 320px; width: 320px; }.kegiatan-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-2); }:deep(.p-datatable-tbody > tr > td) { padding-block: var(--bee-space-4); }
.kegiatan-empty { text-align: center; padding: var(--bee-space-7) var(--bee-space-5); display: grid; justify-items: center; }.kegiatan-empty > .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); margin-bottom: var(--bee-space-4); }.kegiatan-empty h3 { font-size: var(--bee-type-section); }.kegiatan-empty p { color: var(--app-text-muted); margin-bottom: var(--bee-space-5); }
.kegiatan-footnote { display: flex; align-items: flex-start; gap: var(--bee-space-2); margin: 0; padding: var(--bee-space-4) var(--bee-space-5); border-top: 1px solid var(--app-border); font-size: var(--bee-type-caption); color: var(--app-text-muted); }.kegiatan-footnote .bee-icon { width: 16px; height: 16px; margin-top: 2px; }.kegiatan-mobile { display: none; }
@media(max-width:767px) {
  .kegiatan-heading { padding: var(--bee-space-4); }.kegiatan-toolbar { padding-inline: var(--bee-space-4); gap: var(--bee-space-3); }.kegiatan-field { flex-basis: 100%; }.kegiatan-results { padding-inline: var(--bee-space-4); }.kegiatan-desktop { display: none; }.kegiatan-mobile { display: block; margin: 0; padding: 0; list-style: none; }.kegiatan-mobile li { padding: var(--bee-space-4); border-top: 1px solid var(--app-border); }.kegiatan-mobile-heading { display: flex; justify-content: space-between; gap: var(--bee-space-3); align-items: flex-start; }.kegiatan-mobile-heading > div { min-width: 0; }.kegiatan-mobile-heading .p-tag { flex-shrink: 0; }.kegiatan-mobile dl { margin: var(--bee-space-4) 0; display: grid; gap: var(--bee-space-2); }.kegiatan-mobile dl > div { display: flex; justify-content: space-between; gap: var(--bee-space-3); }.kegiatan-mobile dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.kegiatan-mobile dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }.kegiatan-mobile-actions { display: flex; flex-wrap: wrap; gap: var(--bee-space-2); margin-top: var(--bee-space-4); }.kegiatan-footnote { padding: var(--bee-space-4); }
}
</style>
<style>
.kegiatan-action-menu .p-menu-item-link { min-height: var(--bee-size-control); gap: var(--bee-space-3); }.kegiatan-action-menu .kegiatan-action-danger .p-menu-item-link { color: var(--bee-color-critical); }
</style>
