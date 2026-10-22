<script setup lang="ts">
import BeePaginator from "@/shared/components/BeePaginator.vue"
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { formatRp } from "@/core/format"
import type { Jurnal, JurnalStatus } from "@/types/api"
import { journalDate, journalSource, journalState, journalStates, journalTotals } from "./presentation"
const props = defineProps<{rows:Jurnal[];total:number;page:number;loading?:boolean;error?:string;search:string;status:JurnalStatus|null}>()
const emit=defineEmits<{filter:[value:{search:string;status:JurnalStatus|null}];page:[value:number];retry:[];inspect:[row:Jurnal]}>()
const query=ref(props.search)
const state=ref(props.status)
watch(()=>props.search,value=>{query.value=value})
watch(()=>props.status,value=>{state.value=value})
const options=Object.entries(journalStates).map(([value,item])=>({value,label:item.label}))
const filtered=computed(()=>Boolean(props.search||props.status))
const unapplied=computed(()=>query.value.trim()!==props.search||state.value!==props.status)
function apply(){emit("filter",{search:query.value.trim(),status:state.value})}
function reset(){query.value="";state.value=null;apply()}
function amount(row:Jurnal){const totals=journalTotals(row.detail);return row.perlu_rekonsiliasi||!row.detail.length||!totals?.balanced?"Belum diketahui":formatRp(totals.debit)}
</script>
<template>
  <section class="journal-directory" aria-label="Daftar jurnal" :aria-busy="loading">
    <header class="journal-heading"><h2>Daftar jurnal</h2><p>Periksa bukti, rincian akun, dan status sebelum melanjutkan pencatatan.</p></header>
    <form class="journal-toolbar" @submit.prevent="apply">
      <div class="journal-field journal-search"><label for="journal-search">Cari jurnal</label><SearchField input-id="journal-search" v-model="query" placeholder="Nomor bukti atau keterangan" hint="Pencarian server mencakup nomor bukti dan keterangan pada jenis jurnal yang sedang dibuka." /></div>
      <div class="journal-field"><label for="journal-status">Status jurnal</label><Select input-id="journal-status" v-model="state" :options="options" option-label="label" option-value="value" placeholder="Semua status" show-clear><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
      <Button label="Terapkan" severity="secondary" type="submit" :disabled="loading"><template #icon><Icon name="funnel" /></template></Button>
    </form>
    <p v-if="unapplied" class="journal-filter-note" role="status">Pilihan belum diterapkan. Daftar masih mengikuti filter sebelumnya.</p>
    <div class="journal-results"><p role="status">{{ loading?'Memuat jurnal…':error?'Daftar belum berhasil dimuat':total?`${(page-1)*10+1}–${Math.min(page*10,total)} dari ${total} jurnal`:'0 jurnal' }}</p><Button v-if="filtered||unapplied" label="Reset filter" text severity="secondary" :disabled="loading" @click="reset" /></div>
    <div v-if="error" class="journal-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Muat ulang jurnal" severity="secondary" @click="emit('retry')" /></div>
    <div v-else-if="loading" class="journal-empty" role="status"><Icon name="arrows-clockwise" /><p>Menyiapkan bukti dan rincian jurnal.</p></div>
    <div v-else-if="!rows.length" class="journal-empty"><Icon name="book-open" /><h3>{{ filtered?'Tidak ada jurnal yang cocok':'Belum ada jurnal' }}</h3><p>{{ filtered?'Sesuaikan kata pencarian atau status jurnal.':'Jurnal manual dan transaksi dari modul lain akan tampil di sini.' }}</p><Button v-if="filtered" label="Tampilkan semua status" severity="secondary" @click="reset" /></div>
    <template v-else>
      <DataTable class="journal-desktop" :value="rows" data-key="id" table-style="min-width: 700px"><Column header="Bukti dan keterangan"><template #body="{data}"><strong class="journal-proof">{{ data.no_bukti }}</strong><span class="journal-secondary">{{ data.keterangan||'Tanpa keterangan' }}</span></template></Column><Column header="Tanggal dan sumber"><template #body="{data}"><span>{{ journalDate(data.tanggal) }}</span><small class="journal-secondary">{{ journalSource(data.tipe_sumber) }}</small></template></Column><Column header="Nominal jurnal" header-class="journal-numeric" body-class="journal-numeric"><template #body="{data}"><strong class="journal-amount">{{ amount(data) }}</strong></template></Column><Column header="Status"><template #body="{data}"><Tag :value="journalState(data).label" :severity="journalState(data).severity" /></template></Column><Column header="Rincian" body-class="journal-inspect"><template #body="{data}"><Button label="Periksa" severity="secondary" text :aria-label="`Periksa jurnal ${data.no_bukti}`" @click="emit('inspect',data)"><template #icon><Icon name="eye" /></template></Button></template></Column></DataTable>
      <ul class="journal-mobile"><li v-for="row in rows" :key="row.id"><div class="journal-mobile-top"><div><strong class="journal-proof">{{ row.no_bukti }}</strong><small class="journal-secondary">{{ journalDate(row.tanggal) }}</small></div><Tag :value="journalState(row).label" :severity="journalState(row).severity" /></div><p class="journal-description">{{ row.keterangan||'Tanpa keterangan' }}</p><span class="journal-secondary">{{ journalSource(row.tipe_sumber) }}</span><div class="journal-mobile-bottom"><div><small class="journal-secondary">Nominal jurnal</small><strong class="journal-amount">{{ amount(row) }}</strong></div><Button label="Periksa" severity="secondary" :aria-label="`Periksa jurnal ${row.no_bukti}`" @click="emit('inspect',row)" /></div></li></ul>
      <BeePaginator v-if="total>10" :first="(page-1)*10" :rows="10" :total-records="total" @page="emit('page',$event.page+1)" />
    </template>
    <p class="journal-footnote"><Icon name="info" /><span>Nominal jurnal adalah total debit yang seimbang dengan kredit, bukan jumlah kas masuk atau keluar. Rincian yang belum cocok tetap ditandai.</span></p>
  </section>
</template>
<style scoped>
.journal-directory{min-width:0;background:var(--app-surface);border:1px solid var(--app-border);border-radius:var(--bee-radius-panel);overflow:clip}.journal-heading{padding:var(--bee-space-5)}.journal-heading h2{font-size:var(--bee-type-section)}.journal-heading p{margin:var(--bee-space-1) 0 0;color:var(--app-text-muted)}.journal-toolbar{display:flex;flex-wrap:wrap;align-items:end;gap:var(--bee-space-3);padding:0 var(--bee-space-5) var(--bee-space-5)}.journal-field{display:grid;gap:var(--bee-space-2);flex:1 1 210px;min-width:0}.journal-search{flex:2 1 280px}.journal-field label{font-weight:500;font-size:var(--bee-type-caption)}.journal-search :deep(.bee-search-field){min-width:0}.journal-results{display:flex;align-items:center;justify-content:space-between;gap:var(--bee-space-3);min-height:52px;padding:0 var(--bee-space-5);border-top:1px solid var(--app-border);font-size:var(--bee-type-caption);color:var(--app-text-muted)}.journal-filter-note{padding:0 var(--bee-space-5) var(--bee-space-4);color:var(--app-text-muted);font-size:var(--bee-type-caption)}.journal-proof,.journal-amount{font-weight:500;overflow-wrap:anywhere}.journal-secondary{display:block;color:var(--app-text-muted);font-size:var(--bee-type-caption);margin-top:var(--bee-space-1);overflow-wrap:anywhere}.journal-amount{font-variant-numeric:tabular-nums;white-space:nowrap}.journal-directory :deep(.journal-numeric){text-align:right}.journal-directory :deep(th.journal-numeric .p-datatable-column-header-content){justify-content:flex-end}.journal-directory :deep(.p-datatable-tbody>tr>td){height:var(--bee-size-row-multiline);padding-block:var(--bee-space-3)}.journal-directory :deep(.journal-inspect){width:120px}.journal-notice{display:grid;justify-items:start;gap:var(--bee-space-3);padding:var(--bee-space-5)}.journal-empty{display:grid;justify-items:center;text-align:center;gap:var(--bee-space-3);padding:var(--bee-space-7) var(--bee-space-5)}.journal-empty p{color:var(--app-text-muted);max-width:48ch}.journal-footnote{display:flex;align-items:start;gap:var(--bee-space-2);margin:0;padding:var(--bee-space-4) var(--bee-space-5);border-top:1px solid var(--app-border);font-size:var(--bee-type-caption);color:var(--app-text-muted)}.journal-footnote .bee-icon{width:16px;height:16px;margin-top:2px}.journal-mobile{display:none}
@media(max-width:760px){.journal-heading{padding:var(--bee-space-4)}.journal-toolbar{padding-inline:var(--bee-space-4)}.journal-field{flex-basis:100%}.journal-toolbar>.p-button{width:100%}.journal-results{padding-inline:var(--bee-space-4)}.journal-desktop{display:none}.journal-mobile{display:block;list-style:none;padding:0;margin:0}.journal-mobile li{padding:var(--bee-space-4);border-top:1px solid var(--app-border)}.journal-mobile-top,.journal-mobile-bottom{display:flex;align-items:start;justify-content:space-between;gap:var(--bee-space-3)}.journal-mobile-top>div{min-width:0}.journal-mobile-top .p-tag{max-width:52%;flex-shrink:0}.journal-description{margin:var(--bee-space-4) 0 var(--bee-space-2);overflow-wrap:anywhere}.journal-mobile-bottom{align-items:center;flex-wrap:wrap;margin-top:var(--bee-space-4)}.journal-footnote{padding:var(--bee-space-4)}}
</style>
