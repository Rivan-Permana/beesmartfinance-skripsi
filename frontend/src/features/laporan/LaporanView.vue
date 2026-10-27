<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue"
import Button from "primevue/button"
import Message from "primevue/message"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import { friendlyError } from "@/core/errors"
import { downloadCsv } from "@/core/export"
import { coaApi } from "@/features/jurnal/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import type { Coa } from "@/types/api"
import { laporanApi } from "./api"
import LaporanContent from "./LaporanContent.vue"
import { REPORTS, reportFiltersChanged, reportMonths, reportPeriod, type ReportFilters, type ReportKind, type ReportSnapshot } from "./presentation"

const tab=ref<ReportKind>('neraca')
const currentYear=new Date().getFullYear()
const years=Array.from({length:currentYear+2-2024},(_,index)=>currentYear+1-index)
const months=reportMonths.map((label,index)=>({label,value:index+1}))
const draftYear=ref(currentYear),draftMonth=ref(new Date().getMonth()+1),draftAccount=ref<string|null>(null)
const applied=ref<ReportFilters>({tahun:draftYear.value,bulan:draftMonth.value,account:null})
const snapshot=ref<ReportSnapshot|null>(null)
const loading=ref(false),error=ref(''),formError=ref('')
const accounts=ref<Coa[]>([]),accountsLoading=ref(false),accountsError=ref(false)
let sequence=0
const draft=computed<ReportFilters>(()=>({tahun:draftYear.value,bulan:draftMonth.value,account:accounts.value.find(account=>account.kode_akun===draftAccount.value)??null}))
const dirty=computed(()=>reportFiltersChanged(tab.value,draft.value,applied.value))
const ready=computed(()=>snapshot.value?.kind===tab.value&&!loading.value&&!error.value)
const info=computed(()=>REPORTS.find(report=>report.id===tab.value)!)
const resultScope=computed(()=>snapshot.value?.kind===tab.value?snapshot.value.scope:null)
const periodLabel=computed(()=>reportPeriod(tab.value,resultScope.value??applied.value))
const headingPeriod=computed(()=>resultScope.value?periodLabel.value:`${loading.value?'Menyiapkan hasil':'Belum ada hasil'} · ${periodLabel.value}`)
function errorText(value:unknown,fallback:string){const message=friendlyError(value,fallback);return [message.summary,message.detail].filter(Boolean).join('. ')}
async function loadAccounts(){
  if(accountsLoading.value)return
  accountsLoading.value=true;accountsError.value=false
  try{accounts.value=await coaApi.list()}catch{accountsError.value=true}finally{accountsLoading.value=false}
}
async function fetchReport(kind:ReportKind,scope:ReportFilters):Promise<ReportSnapshot>{
  const year={tahun:scope.tahun}
  switch(kind){
    case 'neraca':return {kind,scope,data:await laporanApi.neracaSaldo(year)}
    case 'lr':return {kind,scope,data:await laporanApi.labaRugi(year)}
    case 'pk':return {kind,scope,data:await laporanApi.posisiKeuangan(year)}
    case 'ra':return {kind,scope,data:await laporanApi.realisasiAnggaran(scope.tahun)}
    case 'bb':return {kind,scope,data:await laporanApi.bukuBesar(scope.account!.kode_akun,{...year,bulan:scope.bulan})}
  }
}
async function loadReport(){
  const request=++sequence,kind=tab.value
  const scope:ReportFilters={...applied.value,account:applied.value.account?{...applied.value.account}:null}
  snapshot.value=null;error.value=''
  if(kind==='bb'&&!scope.account){loading.value=false;return}
  loading.value=true
  try{const result=await fetchReport(kind,scope);if(request===sequence)snapshot.value=result}
  catch(e){if(request===sequence)error.value=errorText(e,'Laporan belum berhasil dimuat')}
  finally{if(request===sequence)loading.value=false}
}
function changeReport(value:string|number){
  if(!REPORTS.some(report=>report.id===value)||value===tab.value)return
  tab.value=value as ReportKind;formError.value=''
  if(tab.value==='bb'&&!accounts.value.length)void loadAccounts()
  void loadReport()
}
function apply(){
  if(loading.value)return
  if(!years.includes(draftYear.value)){formError.value='Pilih tahun laporan yang tersedia.';return}
  if(tab.value==='bb'&&(!draft.value.account||!['D','K'].includes(draft.value.account.posisi_normal))){formError.value='Pilih akun buku besar sebelum menerapkan periode.';return}
  formError.value=''
  const account=draft.value.account
  applied.value={tahun:draftYear.value,bulan:draftMonth.value,account:account?{kode_akun:account.kode_akun,nama_akun:account.nama_akun,posisi_normal:account.posisi_normal}:null}
  void loadReport()
}
function printReport(){if(ready.value)window.print()}
function exportCsv(){
  const current=snapshot.value
  if(!ready.value||current?.kind!=='neraca')return
  downloadCsv(`neraca-saldo-${current.scope.tahun}.csv`,['Kode','Nama','Posisi normal','Debit kumulatif (Rp)','Kredit kumulatif (Rp)','Saldo akhir (Rp)'],current.data.map(row=>[row.kode_akun,row.nama_akun,row.posisi_normal,row.total_debit,row.total_kredit,row.saldo_akhir]))
}
void loadReport()
onBeforeUnmount(()=>{sequence+=1})
</script>
<template>
  <PageLayout class="reports-page" title="Laporan keuangan" subtitle="Periksa saldo, pendapatan, beban, anggaran, dan mutasi dari jurnal tercatat." :surface="false">
    <template #actions><Button label="Cetak laporan" severity="secondary" :disabled="!ready" @click="printReport"><template #icon><Icon name="printer" /></template></Button><Button v-if="tab==='neraca'" label="Unduh CSV" severity="secondary" :disabled="!ready" @click="exportCsv"><template #icon><Icon name="download" /></template></Button></template>
    <div class="report-workspace"><div class="report-mobile-navigation"><label for="report-kind">Jenis laporan</label><Select input-id="report-kind" :model-value="tab" :options="[...REPORTS]" option-label="title" option-value="id" @update:model-value="changeReport"><template #dropdownicon><Icon name="caret-down" /></template></Select></div><Tabs :value="tab" scrollable @update:value="changeReport"><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template><TabList :pt="{tabList:{'aria-label':'Jenis laporan keuangan'},prevButton:{'aria-label':'Lihat jenis laporan sebelumnya'},nextButton:{'aria-label':'Lihat jenis laporan berikutnya'}}"><Tab v-for="report in REPORTS" :key="report.id" :value="report.id">{{ report.title }}</Tab></TabList>
      <TabPanels><TabPanel v-for="report in REPORTS" :key="report.id" :value="report.id"><template v-if="tab===report.id">
        <form class="report-controls" aria-label="Filter laporan" @submit.prevent="apply"><div class="report-control"><label for="report-year">Tahun laporan</label><Select input-id="report-year" v-model="draftYear" :options="years" :invalid="!!formError&&!years.includes(draftYear)" :aria-invalid="!!formError&&!years.includes(draftYear)"><template #dropdownicon><Icon name="caret-down" /></template></Select></div><div v-if="tab==='bb'" class="report-control"><label for="report-month">Bulan buku besar</label><Select input-id="report-month" v-model="draftMonth" :options="months" option-label="label" option-value="value"><template #dropdownicon><Icon name="caret-down" /></template></Select></div><div v-if="tab==='bb'" class="report-control report-account-control"><label for="report-account">Akun buku besar (wajib)</label><Select input-id="report-account" v-model="draftAccount" :options="accounts" option-label="nama_akun" option-value="kode_akun" :filter-fields="['kode_akun','nama_akun']" filter :loading="accountsLoading" :disabled="accountsLoading" :invalid="!!formError&&!draft.account" :aria-invalid="!!formError&&!draft.account" :aria-describedby="formError?'report-filter-error':undefined" placeholder="Pilih akun"><template #value="{value,placeholder}"><span>{{ value?`${value} — ${accounts.find(account=>account.kode_akun===value)?.nama_akun??'Nama akun belum dimuat'}`:placeholder }}</span></template><template #option="{option}"><span>{{ option.kode_akun }} — {{ option.nama_akun }}{{ option.is_active?'':' (nonaktif)' }}</span></template><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select></div><Button label="Terapkan" type="submit" :loading="loading" :disabled="tab==='bb'&&accountsLoading"><template #icon><Icon name="funnel" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></form>
        <div class="report-filter-feedback"><p v-if="dirty" role="status"><Icon name="info" />Pilihan belum diterapkan. Jika ada hasil, angka dan unduhan tetap mengikuti filter yang terakhir diterapkan.</p><p v-else>{{ tab==='bb'?'Bulan hanya digunakan pada Buku besar.':'Laporan ini memakai tahun; pilihan bulan tersedia pada Buku besar.' }}</p><p v-if="formError" id="report-filter-error" class="report-negative" role="alert">{{ formError }}</p><div v-if="tab==='bb'&&accountsError" class="report-inline-error"><Message severity="warn" :closable="false">Daftar akun belum berhasil dimuat. Pilihan dan periode yang sudah diterapkan tetap dipertahankan.</Message><Button label="Muat ulang akun" severity="secondary" :loading="accountsLoading" @click="loadAccounts" /></div></div>
        <article class="report-document" :aria-busy="loading"><header class="report-document-heading"><div class="report-print-brand"><img src="/logo-lebah.svg" alt="" width="40" height="40"><div><strong>Sekolah Lebah Madu</strong><p>BeeSmart Finance</p></div></div><div class="report-heading-row"><div><h2>{{ info.title }}</h2><p class="report-applied-period">{{ headingPeriod }}</p><p v-if="tab==='bb'&&resultScope?.account" class="report-applied-account">{{ resultScope.account.kode_akun }} — {{ resultScope.account.nama_akun }}</p></div><span v-if="ready" class="report-posted-note"><Icon name="check-circle" />{{ tab==='ra'?'Realisasi dari jurnal tercatat':'Jurnal tercatat' }}</span></div><p class="report-description">{{ info.description }}</p></header>
          <div v-if="loading" class="report-state" role="status"><Icon name="arrows-clockwise" /><h3>Memuat {{ info.title.toLowerCase() }}…</h3><p>Menyiapkan angka untuk {{ periodLabel.toLowerCase() }}.</p></div>
          <div v-else-if="error" class="report-state report-error"><Icon name="warning-circle" /><h3>Laporan belum dapat ditampilkan</h3><p role="alert">{{ error }}</p><Button label="Muat ulang laporan" severity="secondary" @click="loadReport" /></div>
          <div v-else-if="tab==='bb'&&!snapshot" class="report-state"><Icon name="book-open" /><h3>Pilih akun untuk membuka buku besar</h3><p>Pilih akun, bulan, dan tahun, lalu tekan Terapkan. Saldo awal periode ikut ditampilkan bila tersedia.</p></div>
          <div v-else-if="snapshot&&snapshot.kind===tab" class="report-data"><p class="report-scroll-hint"><Icon name="arrow-right" />Geser tabel bila kolom belum terlihat seluruhnya. Semua nominal dalam rupiah.</p><LaporanContent :snapshot="snapshot" /></div>
        </article>
      </template></TabPanel></TabPanels>
    </Tabs></div>
  </PageLayout>
</template>
<style src="./reports.css"></style>
