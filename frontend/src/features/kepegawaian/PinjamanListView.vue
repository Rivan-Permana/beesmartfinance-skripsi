<script setup lang="ts">
import BeePaginator from '@/shared/components/BeePaginator.vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import PageLayout from '@/shared/components/PageLayout.vue'
import SearchField from '@/shared/components/SearchField.vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { useTableSearch } from '@/shared/composables/useTableSearch'
import { useAuthStore } from '@/stores/auth'
import { notifySuccess } from '@/core/errors'
import type { Pegawai, Pinjaman } from '@/types/api'
import { pegawaiApi, pinjamanApi } from './api'
import { ambiguous, dateLabel, errorText, loanDisbursed, loanStatus, money } from './payroll'
import KasbonFormDialog from './KasbonFormDialog.vue'
import EmployeeActionDialog from './EmployeeActionDialog.vue'
import './employee-finance.css'
const auth=useAuthStore(), toast=useToast()
const canWrite=computed(()=>auth.hasRole(['Finance']))
const rows=ref<Pinjaman[]>([]),staff=ref<Pegawai[]>([]),loading=ref(false),error=ref(''),optionsLoading=ref(false),optionsError=ref('')
const names=computed(()=>new Map(staff.value.map(row=>[row.id,row.nama])))
const name=(id:number)=>names.value.get(id)??`Pegawai #${id}`
const status=ref<boolean|null>(null),first=ref(0)
const scoped=computed(()=>rows.value.filter(row=>status.value==null||loanDisbursed(row)===status.value))
const {query,filtered}=useTableSearch(scoped,row=>[name(row.pegawai),dateLabel(row.tanggal_pinjaman),loanStatus(row).label])
const pageRows=computed(()=>filtered.value.slice(first.value,first.value+15))
const hasFilter=computed(()=>!!query.value.trim()||status.value!=null)
watch([query,status,rows],()=>{first.value=0;menu.value?.hide()})
function reset(){query.value='';status.value=null}
async function load(){if(loading.value)return;loading.value=true;error.value='';try{rows.value=await pinjamanApi.listAll()}catch(e){rows.value=[];error.value=errorText(e,'Daftar kasbon belum berhasil dimuat')}finally{loading.value=false}}
async function loadOptions(){if(optionsLoading.value)return;optionsLoading.value=true;optionsError.value='';try{staff.value=await pegawaiApi.listAll()}catch(e){optionsError.value=errorText(e,'Daftar pegawai belum berhasil dimuat')}finally{optionsLoading.value=false}}
const formOpen=ref(false),editing=ref<Pinjaman|null>(null),saving=ref(false),formError=ref(''),uncertainSave=ref(false)
const detail=ref<Pinjaman|null>(null),opening=ref(false),detailError=ref('')
const action=ref<'disburse'|'delete'|null>(null),target=ref<Pinjaman|null>(null),pending=ref(false),checking=ref(false),actionError=ref(''),uncertainAction=ref(false),actionReady=ref(false)
const busy=computed(()=>saving.value||pending.value||checking.value||opening.value)
const menu=ref<InstanceType<typeof Menu>|null>(null),menuTarget=ref<Pinjaman|null>(null),menuOpen=ref(false)
const items=computed(()=>{const row=menuTarget.value;if(!row||!canWrite.value||loanDisbursed(row))return [];return [{label:'Ubah kasbon',icon:'pencil-simple',command:()=>edit(row)},{separator:true},{label:'Hapus pengajuan',icon:'trash',class:'employee-action-danger',command:()=>startAction('delete',row)}]})
function openMenu(event:Event,row:Pinjaman){menuTarget.value=row;menu.value?.toggle(event)}
function create(){if(!canWrite.value||busy.value)return;editing.value=null;formError.value='';uncertainSave.value=false;formOpen.value=true}
async function edit(row:Pinjaman){
  if(!canWrite.value||busy.value||loanDisbursed(row))return
  opening.value=true;detailError.value=''
  try{const fresh=await pinjamanApi.get(row.id);if(fresh.jurnal){await load();detailError.value='Jurnal pencairan sudah dibuat. Pengajuan tidak dapat diubah.';return}editing.value=fresh;formError.value='';uncertainSave.value=false;formOpen.value=true}
  catch(e){detailError.value=errorText(e,'Pengajuan terbaru belum berhasil diperiksa. Coba buka kembali.')}
  finally{opening.value=false}
}
async function save(payload:Partial<Pinjaman>){
  if(!canWrite.value||saving.value||uncertainSave.value||editing.value?.jurnal)return
  saving.value=true;formError.value=''
  try{const result=editing.value?await pinjamanApi.update(editing.value.id,payload):await pinjamanApi.create(payload);formOpen.value=false;detail.value=result;notifySuccess(toast,'Pengajuan kasbon disimpan',{detail:'Pencairan dilakukan terpisah setelah rincian diperiksa.'});await load()}
  catch(e){formError.value=errorText(e,'Pengajuan belum berhasil disimpan');uncertainSave.value=ambiguous(e)}finally{saving.value=false}
}
async function reviewSave(){formOpen.value=false;await load()}
async function showDetail(row:Pinjaman){if(busy.value)return;opening.value=true;detailError.value='';try{detail.value=await pinjamanApi.get(row.id)}catch(e){detailError.value=errorText(e,'Rincian kasbon belum berhasil dimuat. Coba buka kembali.')}finally{opening.value=false}}
function closeAction(){if(!pending.value&&!checking.value){target.value=null;action.value=null}}
async function startAction(value:'disburse'|'delete',row:Pinjaman){if(!canWrite.value||busy.value||loanDisbursed(row))return;target.value=row;action.value=value;actionReady.value=false;uncertainAction.value=false;await refreshAction()}
async function refreshAction(){
  if(!target.value||pending.value||checking.value)return
  checking.value=true;actionError.value='';actionReady.value=false
  try{const fresh=await pinjamanApi.get(target.value.id);if(fresh.jurnal){target.value=null;action.value=null;notifySuccess(toast,'Status kasbon diperbarui',{detail:'Jurnal pencairan sudah tertaut; tindakan tidak dikirim ulang.'})}else{target.value=fresh;actionReady.value=true;uncertainAction.value=false}await load()}
  catch(e){if((e as {response?:{status?:number}}).response?.status===404){target.value=null;action.value=null;await load()}else actionError.value=errorText(e,'Status kasbon belum berhasil diperiksa')}
  finally{checking.value=false}
}
async function confirmAction(){
  if(!target.value||!action.value||!canWrite.value||busy.value||!actionReady.value||uncertainAction.value||target.value.jurnal)return
  const row=target.value,value=action.value
  pending.value=true;actionError.value=''
  try{if(value==='disburse'){const result=await pinjamanApi.cairkan(row.id);notifySuccess(toast,'Jurnal pencairan dibuat',result)}else{await pinjamanApi.remove(row.id);notifySuccess(toast,'Pengajuan kasbon dihapus')}target.value=null;action.value=null;await load()}
  catch(e){actionError.value=errorText(e,'Tindakan belum terkonfirmasi');uncertainAction.value=ambiguous(e)}finally{pending.value=false}
}
function beforeUnload(event:BeforeUnloadEvent){if(saving.value||pending.value){event.preventDefault();event.returnValue=''}}
onBeforeRouteLeave(()=>!saving.value&&!pending.value)
onMounted(()=>{void load();void loadOptions();window.addEventListener('beforeunload',beforeUnload)})
onBeforeUnmount(()=>window.removeEventListener('beforeunload',beforeUnload))
</script>
<template>
  <PageLayout title="Kasbon pegawai" subtitle="Catat pengajuan, periksa angsuran, dan buat jurnal pencairan." :surface="false"><template #actions><Button v-if="canWrite" label="Ajukan kasbon" :disabled="busy" @click="create"><template #icon><Icon name="plus" /></template></Button></template>
    <section class="employee-panel" aria-label="Daftar kasbon pegawai" :aria-busy="loading || (optionsLoading && !staff.length)">
      <header class="employee-heading"><div><h2>Pengajuan dan saldo</h2><p>Buka nama pegawai untuk melihat rincian kasbon tersimpan.</p></div><Button label="Muat ulang daftar" severity="secondary" :loading="loading" :disabled="busy" @click="load"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template><template #icon><Icon name="arrows-clockwise" /></template></Button></header>
      <div class="employee-toolbar"><div class="employee-field employee-search"><label for="loan-search">Cari kasbon</label><SearchField input-id="loan-search" v-model="query" placeholder="Nama pegawai atau tanggal" hint="Pencarian mencakup seluruh pengajuan yang dimuat" /></div><div class="employee-field"><label for="loan-status">Status pencairan</label><Select input-id="loan-status" v-model="status" :options="[{label:'Semua status',value:null},{label:'Menunggu pencairan',value:false},{label:'Sudah dicairkan',value:true}]" option-label="label" option-value="value" placeholder="Semua status"><template #dropdownicon><Icon name="caret-down" /></template></Select></div></div>
      <div v-if="optionsError" class="employee-notice"><Message severity="warn" :closable="false">{{ optionsError }} Pengajuan tetap dapat dibaca.</Message><Button label="Muat ulang pegawai" severity="secondary" :loading="optionsLoading" :disabled="busy" @click="loadOptions" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div>
      <div v-if="detailError" class="employee-notice"><Message severity="error" :closable="false">{{ detailError }}</Message></div>
      <div class="employee-results"><p role="status">{{ loading || (optionsLoading && !staff.length)?'Memuat kasbon…':error?'Daftar belum tersedia':`${filtered.length?first+1:0}–${Math.min(first+15,filtered.length)} dari ${filtered.length} pengajuan` }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" text @click="reset" /></div>
      <div v-if="error" class="employee-empty"><Icon name="warning-circle" /><h3>Daftar kasbon belum dapat ditampilkan</h3><p>{{ error }}</p><Button label="Coba muat ulang kasbon" severity="secondary" @click="load" /></div>
      <div v-else-if="loading || (optionsLoading && !staff.length)" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan pengajuan kasbon</p></div>
      <div v-else-if="!filtered.length" class="employee-empty"><Icon :name="hasFilter?'magnifying-glass':'wallet'" /><h3>{{ hasFilter?'Tidak ada pengajuan yang cocok':'Belum ada pengajuan kasbon' }}</h3><p>{{ hasFilter?'Coba nama, tanggal, atau status lain.':'Catat jumlah pinjaman dan angsuran sesuai kesepakatan.' }}</p><Button v-if="hasFilter||canWrite" :label="hasFilter?'Hapus filter':'Ajukan kasbon'" severity="secondary" @click="hasFilter?reset():create()" /></div>
      <template v-else>
        <table class="employee-table"><caption class="employee-sr-only">Pengajuan kasbon, 15 pengajuan per halaman</caption><thead><tr><th>Pegawai dan tanggal</th><th class="employee-number">Pinjaman</th><th class="employee-number">Angsuran / bulan</th><th class="employee-number">Sisa</th><th>Status</th><th class="employee-action-column">Tindakan</th></tr></thead><tbody><tr v-for="row in pageRows" :key="row.id"><td><button class="employee-record-link" :aria-label="`Rincian kasbon ${name(row.pegawai)} ${dateLabel(row.tanggal_pinjaman)}`" :disabled="busy" @click="showDetail(row)"><span>{{ name(row.pegawai) }}</span><small>{{ dateLabel(row.tanggal_pinjaman) }} · {{ row.tenor_bulan }} bulan</small></button></td><td class="employee-number">{{ money(row.jumlah_pinjaman) }}</td><td class="employee-number">{{ money(row.angsuran_per_bulan) }}</td><td class="employee-number"><strong>{{ money(row.sisa_pinjaman) }}</strong></td><td><Tag :value="loanStatus(row).label" :severity="loanStatus(row).severity" /></td><td class="employee-action-column"><div class="employee-row-actions"><Button :label="loanDisbursed(row)||!canWrite?'Rincian':'Cairkan'" severity="secondary" :aria-label="`${loanDisbursed(row)||!canWrite?'Rincian':'Cairkan'} kasbon ${name(row.pegawai)}`" :disabled="busy" @click="loanDisbursed(row)||!canWrite?showDetail(row):startAction('disburse',row)" /><Button v-if="canWrite&&!loanDisbursed(row)" severity="secondary" text :aria-label="`Tindakan kasbon ${name(row.pegawai)} ${dateLabel(row.tanggal_pinjaman)}`" title="Tindakan lainnya" aria-controls="loan-actions" aria-haspopup="menu" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="openMenu($event,row)"><template #icon><Icon name="caret-down" /></template></Button></div></td></tr></tbody></table>
        <ul class="employee-cards" aria-label="Pengajuan kasbon"><li v-for="row in pageRows" :key="row.id"><header><div><button class="employee-record-link" :aria-label="`Rincian kasbon ${name(row.pegawai)} ${dateLabel(row.tanggal_pinjaman)}`" :disabled="busy" @click="showDetail(row)"><span>{{ name(row.pegawai) }}</span><small>{{ dateLabel(row.tanggal_pinjaman) }} · {{ row.tenor_bulan }} bulan</small></button></div><Tag :value="loanStatus(row).label" :severity="loanStatus(row).severity" /></header><dl><div><dt>Pinjaman</dt><dd>{{ money(row.jumlah_pinjaman) }}</dd></div><div><dt>Angsuran / bulan</dt><dd>{{ money(row.angsuran_per_bulan) }}</dd></div><div><dt>Sisa</dt><dd><strong>{{ money(row.sisa_pinjaman) }}</strong></dd></div></dl><div class="employee-card-actions"><Button :label="loanDisbursed(row)||!canWrite?'Rincian':'Cairkan'" severity="secondary" :aria-label="`${loanDisbursed(row)||!canWrite?'Rincian':'Cairkan'} kasbon ${name(row.pegawai)}`" :disabled="busy" @click="loanDisbursed(row)||!canWrite?showDetail(row):startAction('disburse',row)" /><Button v-if="canWrite&&!loanDisbursed(row)" label="Tindakan" severity="secondary" text :aria-label="`Tindakan kasbon ${name(row.pegawai)} ${dateLabel(row.tanggal_pinjaman)}`" aria-controls="loan-actions" aria-haspopup="menu" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="openMenu($event,row)"><template #icon><Icon name="caret-down" /></template></Button></div></li></ul>
        <BeePaginator v-if="filtered.length>15" v-model:first="first" :rows="15" :total-records="filtered.length" />
      </template>
      <p class="employee-footnote"><Icon name="info" /><span>Saldo mengikuti pengurangan kasbon saat gaji diposting. Jurnal pencairan dibuat tidak menyatakan jurnal sudah masuk buku besar.</span></p>
    </section>
    <Menu id="loan-actions" ref="menu" :model="items" class="employee-action-menu" popup @show="menuOpen=true" @hide="menuOpen=false"><template #item="{item,props:itemProps}"><a v-bind="itemProps.action"><Icon v-if="item.icon" :name="item.icon" /><span>{{ item.label }}</span></a></template></Menu>
    <KasbonFormDialog v-model="formOpen" :row="editing" :staff="staff" :options-loading="optionsLoading" :options-error="optionsError" :saving="saving" :uncertain="uncertainSave" :error="formError" @save="save" @reload-options="loadOptions" @review="reviewSave" />
    <EmployeeActionDialog :visible="!!target" :title="action==='delete'?'Hapus pengajuan kasbon?':'Cairkan kasbon?'" :label="target?name(target.pegawai):''" :amount="target?money(target.jumlah_pinjaman):''" :description="action==='delete'?'Pengajuan kasbon ini akan dihapus. Pengajuan yang sudah memiliki jurnal pencairan tidak ditawarkan untuk dihapus.':'Sistem membuat jurnal pencairan berstatus Draf menggunakan tanggal dan nominal pada pengajuan. Jurnal belum masuk buku besar. Periksa rincian sebelum melanjutkan.'" :confirm-label="action==='delete'?'Hapus pengajuan':'Buat jurnal pencairan'" :danger="action==='delete'" :pending="pending" :checking="checking" :ready="actionReady" :error="actionError" :uncertain="uncertainAction" @close="closeAction" @confirm="confirmAction" @refresh="refreshAction" />
    <Dialog :visible="!!detail" @update:visible="value=>{if(!value)detail=null}" header="Rincian kasbon" class="employee-form-dialog" modal :draggable="false" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup rincian kasbon'}"><template #closeicon><Icon name="x" /></template><template v-if="detail"><div class="employee-detail-heading"><h3>{{ name(detail.pegawai) }}</h3><p>{{ dateLabel(detail.tanggal_pinjaman) }}</p><Tag :value="loanStatus(detail).label" :severity="loanStatus(detail).severity" /></div><dl class="employee-detail-list"><div><dt>Jumlah pinjaman</dt><dd>{{ money(detail.jumlah_pinjaman) }}</dd></div><div><dt>Tenor</dt><dd>{{ detail.tenor_bulan }} bulan</dd></div><div><dt>Angsuran per bulan</dt><dd>{{ money(detail.angsuran_per_bulan) }}</dd></div><div><dt>Sudah dikurangkan</dt><dd>{{ money(detail.sudah_terbayar) }}</dd></div><div><dt>Sisa pinjaman</dt><dd><strong>{{ money(detail.sisa_pinjaman) }}</strong></dd></div></dl><p class="employee-small-note">Saldo berkurang saat jurnal gaji disetujui Kepala Sekolah dan kembali bila jurnal itu dibatalkan. Detail cicilan per transaksi belum tersedia pada modul ini.</p></template><template #footer><Button label="Tutup rincian" severity="secondary" @click="detail=null" /></template></Dialog>
  </PageLayout>
</template>
