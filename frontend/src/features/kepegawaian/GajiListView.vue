<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import PageLayout from '@/shared/components/PageLayout.vue'
import SearchField from '@/shared/components/SearchField.vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { useTableSearch } from '@/shared/composables/useTableSearch'
import { useAuthStore } from '@/stores/auth'
import { notifySuccess } from '@/core/errors'
import type { Gaji, Pegawai, Pinjaman } from '@/types/api'
import { gajiApi, pegawaiApi, pinjamanApi } from './api'
import { ambiguous, errorText, money, salaryPeriod } from './payroll'
import GajiFormDialog from './GajiFormDialog.vue'
import GajiSlipPreview from './GajiSlipPreview.vue'
import EmployeeActionDialog from './EmployeeActionDialog.vue'
import './employee-finance.css'

const auth=useAuthStore(), toast=useToast()
const canWrite=computed(()=>auth.hasRole(['Finance']))
const rows=ref<Gaji[]>([]), staff=ref<Pegawai[]>([]), loans=ref<Pinjaman[]>([])
const loading=ref(false), error=ref(''), optionsLoading=ref(false), optionsError=ref('')
const names=computed(()=>new Map(staff.value.map(row=>[row.id,row.nama])))
const name=(id:number)=>names.value.get(id)??`Pegawai #${id}`
const status=ref<boolean|null>(null), first=ref(0)
const scoped=computed(()=>rows.value.filter(row=>status.value==null||!!row.jurnal===status.value))
const {query,filtered}=useTableSearch(scoped,row=>[name(row.pegawai),salaryPeriod(row),row.jurnal?'Jurnal dibuat':'Belum dijurnal'])
const pageRows=computed(()=>filtered.value.slice(first.value,first.value+15))
const hasFilter=computed(()=>!!query.value.trim()||status.value!=null)
watch([query,status,rows],()=>{first.value=0;menu.value?.hide()})
function reset(){query.value='';status.value=null}
async function load(){
  if(loading.value)return
  loading.value=true;error.value=''
  try{rows.value=await gajiApi.listAll()}catch(e){rows.value=[];error.value=errorText(e,'Daftar gaji belum berhasil dimuat')}finally{loading.value=false}
}
async function loadOptions(){
  if(optionsLoading.value)return
  optionsLoading.value=true;optionsError.value=''
  const [people,debts]=await Promise.allSettled([pegawaiApi.listAll(),pinjamanApi.listAll()])
  if(people.status==='fulfilled')staff.value=people.value
  if(debts.status==='fulfilled')loans.value=debts.value
  optionsError.value=[people.status==='rejected'?'Daftar pegawai belum berhasil dimuat.':'',debts.status==='rejected'?'Data potongan kasbon belum berhasil dimuat.':''].filter(Boolean).join(' ')
  optionsLoading.value=false
}
const formOpen=ref(false), editing=ref<Gaji|null>(null), saving=ref(false), formError=ref(''), uncertainSave=ref(false)
const slip=ref<Gaji|null>(null), opening=ref(false), slipError=ref('')
const action=ref<'post'|'delete'|null>(null), target=ref<Gaji|null>(null), pending=ref(false), checking=ref(false), actionError=ref(''), uncertainAction=ref(false), actionReady=ref(false)
const busy=computed(()=>saving.value||pending.value||checking.value||opening.value)
const menu=ref<InstanceType<typeof Menu>|null>(null), menuTarget=ref<Gaji|null>(null), menuOpen=ref(false)
const items=computed(()=>{
  const row=menuTarget.value
  if(!row||!canWrite.value||row.jurnal)return []
  return [{label:'Ubah slip',icon:'pencil-simple',command:()=>edit(row)},{label:'Posting ke jurnal',icon:'file-arrow-up',command:()=>startAction('post',row)},{separator:true},{label:'Hapus slip',icon:'trash',class:'employee-action-danger',command:()=>startAction('delete',row)}]
})
function openMenu(event:Event,row:Gaji){menuTarget.value=row;menu.value?.toggle(event)}
function create(){if(!canWrite.value||busy.value)return;editing.value=null;formError.value='';uncertainSave.value=false;formOpen.value=true}
async function edit(row:Gaji){
  if(!canWrite.value||busy.value||row.jurnal)return
  opening.value=true;slipError.value=''
  try{const fresh=await gajiApi.get(row.id);if(fresh.jurnal){await load();slipError.value='Slip sudah memiliki jurnal. Perubahan tidak tersedia.';return}editing.value=fresh;formError.value='';uncertainSave.value=false;formOpen.value=true}
  catch(e){slipError.value=errorText(e,'Slip terbaru belum berhasil diperiksa. Coba buka kembali.')}
  finally{opening.value=false}
}
async function save(payload:Partial<Gaji>){
  if(!canWrite.value||saving.value||uncertainSave.value||editing.value?.jurnal)return
  saving.value=true;formError.value=''
  try{
    const result=editing.value?await gajiApi.update(editing.value.id,payload):await gajiApi.create(payload)
    formOpen.value=false;slip.value=result
    notifySuccess(toast,'Slip gaji disimpan',{detail:'Rincian menampilkan nilai yang ditetapkan server. Jurnal belum dibuat.'})
    await load()
  }catch(e){formError.value=errorText(e,'Slip belum berhasil disimpan');uncertainSave.value=ambiguous(e)}finally{saving.value=false}
}
async function reviewSave(){formOpen.value=false;await Promise.all([load(),loadOptions()])}
async function showSlip(row:Gaji){if(busy.value)return;opening.value=true;slipError.value='';try{slip.value=await gajiApi.get(row.id)}catch(e){slipError.value=errorText(e,'Rincian slip belum berhasil dimuat. Coba buka kembali.')}finally{opening.value=false}}
function closeAction(){if(!pending.value&&!checking.value){target.value=null;action.value=null}}
async function startAction(value:'post'|'delete',row:Gaji){if(!canWrite.value||busy.value||row.jurnal)return;target.value=row;action.value=value;actionReady.value=false;uncertainAction.value=false;await refreshAction()}
async function refreshAction(){
  if(!target.value||pending.value||checking.value)return
  checking.value=true;actionError.value='';actionReady.value=false
  try{
    const fresh=await gajiApi.get(target.value.id)
    if(fresh.jurnal){target.value=null;action.value=null;notifySuccess(toast,'Status slip diperbarui',{detail:'Jurnal sudah tertaut; tindakan tidak dikirim ulang.'});await loadOptions()}
    else{target.value=fresh;actionReady.value=true;uncertainAction.value=false}
    await load()
  }catch(e){
    if((e as {response?:{status?:number}}).response?.status===404){target.value=null;action.value=null;await load()}
    else actionError.value=errorText(e,'Status slip belum berhasil diperiksa')
  }finally{checking.value=false}
}
async function confirmAction(){
  if(!target.value||!action.value||!canWrite.value||busy.value||!actionReady.value||uncertainAction.value||target.value.jurnal)return
  const row=target.value, value=action.value
  pending.value=true;actionError.value=''
  try{
    if(value==='post'){const result=await gajiApi.posting(row.id);notifySuccess(toast,'Jurnal gaji dibuat',result)}
    else{await gajiApi.remove(row.id);notifySuccess(toast,'Slip gaji dihapus')}
    target.value=null;action.value=null;await Promise.all([load(),loadOptions()])
  }catch(e){actionError.value=errorText(e,'Tindakan belum terkonfirmasi');uncertainAction.value=ambiguous(e)}finally{pending.value=false}
}
function beforeUnload(event:BeforeUnloadEvent){if(saving.value||pending.value){event.preventDefault();event.returnValue=''}}
function beforePrint(){if(slip.value)document.body.classList.add('bee-print-payroll')}
function afterPrint(){document.body.classList.remove('bee-print-payroll')}
function print(){beforePrint();try{window.print()}catch(e){afterPrint();slipError.value=errorText(e,'Dialog cetak belum berhasil dibuka. Coba lagi.')}}
onBeforeRouteLeave(()=>!saving.value&&!pending.value)
onMounted(()=>{void load();void loadOptions();window.addEventListener('beforeunload',beforeUnload);window.addEventListener('beforeprint',beforePrint);window.addEventListener('afterprint',afterPrint)})
onBeforeUnmount(()=>{window.removeEventListener('beforeunload',beforeUnload);window.removeEventListener('beforeprint',beforePrint);window.removeEventListener('afterprint',afterPrint);afterPrint()})
</script>

<template>
  <PageLayout title="Penggajian" subtitle="Kelola slip per pegawai, periksa potongan, lalu buat jurnal gaji." :surface="false"><template #actions><Button v-if="canWrite" label="Buat slip gaji" :disabled="busy" @click="create"><template #icon><Icon name="plus" /></template></Button></template>
    <section class="employee-panel" aria-label="Daftar slip gaji" :aria-busy="loading || (optionsLoading && !staff.length)">
      <header class="employee-heading"><div><h2>Slip gaji</h2><p>Nilai netto mengikuti rincian slip tersimpan.</p></div><Button label="Muat ulang daftar" severity="secondary" :loading="loading" :disabled="busy" @click="load"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template><template #icon><Icon name="arrows-clockwise" /></template></Button></header>
      <div class="employee-toolbar"><div class="employee-field employee-search"><label for="salary-search">Cari slip</label><SearchField input-id="salary-search" v-model="query" placeholder="Nama pegawai atau periode" hint="Pencarian mencakup seluruh slip yang dimuat" /></div><div class="employee-field"><label for="salary-status">Status pencatatan</label><Select input-id="salary-status" v-model="status" :options="[{label:'Semua status',value:null},{label:'Belum dijurnal',value:false},{label:'Jurnal dibuat',value:true}]" option-label="label" option-value="value" placeholder="Semua status"><template #dropdownicon><Icon name="caret-down" /></template></Select></div></div>
      <div v-if="optionsError" class="employee-notice"><Message severity="warn" :closable="false">{{ optionsError }} Slip tetap dapat dibaca.</Message><Button label="Muat ulang data pendukung" severity="secondary" :loading="optionsLoading" :disabled="busy" @click="loadOptions" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div>
      <div v-if="slipError" class="employee-notice"><Message severity="error" :closable="false">{{ slipError }}</Message></div>
      <div class="employee-results"><p role="status">{{ loading || (optionsLoading && !staff.length)?'Memuat slip…':error?'Daftar belum tersedia':`${filtered.length?first+1:0}–${Math.min(first+15,filtered.length)} dari ${filtered.length} slip` }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" text @click="reset" /></div>
      <div v-if="error" class="employee-empty"><Icon name="warning-circle" /><h3>Daftar gaji belum dapat ditampilkan</h3><p>{{ error }}</p><Button label="Coba muat ulang gaji" severity="secondary" @click="load" /></div>
      <div v-else-if="loading || (optionsLoading && !staff.length)" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan slip gaji</p></div>
      <div v-else-if="!filtered.length" class="employee-empty"><Icon :name="hasFilter?'magnifying-glass':'file-text'" /><h3>{{ hasFilter?'Tidak ada slip yang cocok':'Belum ada slip gaji' }}</h3><p>{{ hasFilter?'Coba nama, periode, atau status lain.':'Buat slip untuk mencatat komponen gaji pegawai.' }}</p><Button v-if="hasFilter||canWrite" :label="hasFilter?'Hapus filter':'Buat slip gaji'" severity="secondary" @click="hasFilter?reset():create()" /></div>
      <template v-else>
        <table class="employee-table"><caption class="employee-sr-only">Slip gaji seluruh hasil pencarian, 15 slip per halaman</caption><thead><tr><th>Pegawai dan periode</th><th class="employee-number">Bruto</th><th class="employee-number">Potongan</th><th class="employee-number">Netto</th><th>Status</th><th class="employee-action-column">Tindakan</th></tr></thead><tbody><tr v-for="row in pageRows" :key="row.id"><td><strong>{{ name(row.pegawai) }}</strong><small>{{ salaryPeriod(row) }}</small></td><td class="employee-number">{{ money(row.total_bruto) }}</td><td class="employee-number">{{ money(row.total_potongan) }}</td><td class="employee-number"><strong>{{ money(row.total_netto) }}</strong></td><td><Tag :value="row.jurnal?'Jurnal dibuat':'Belum dijurnal'" :severity="row.jurnal?'info':'warn'" /></td><td class="employee-action-column"><div class="employee-row-actions"><Button label="Lihat slip" severity="secondary" :aria-label="`Lihat slip ${name(row.pegawai)} ${salaryPeriod(row)}`" :disabled="busy" @click="showSlip(row)" /><Button v-if="canWrite&&!row.jurnal" severity="secondary" text :aria-label="`Tindakan slip ${name(row.pegawai)} ${salaryPeriod(row)}`" title="Tindakan lainnya" aria-controls="salary-actions" aria-haspopup="menu" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="openMenu($event,row)"><template #icon><Icon name="caret-down" /></template></Button></div></td></tr></tbody></table>
        <ul class="employee-cards" aria-label="Slip gaji"><li v-for="row in pageRows" :key="row.id"><header><div><strong>{{ name(row.pegawai) }}</strong><small>{{ salaryPeriod(row) }}</small></div><Tag :value="row.jurnal?'Jurnal dibuat':'Belum dijurnal'" :severity="row.jurnal?'info':'warn'" /></header><dl><div><dt>Bruto</dt><dd>{{ money(row.total_bruto) }}</dd></div><div><dt>Potongan</dt><dd>{{ money(row.total_potongan) }}</dd></div><div><dt>Netto</dt><dd><strong>{{ money(row.total_netto) }}</strong></dd></div></dl><div class="employee-card-actions"><Button label="Lihat slip" severity="secondary" :aria-label="`Lihat slip ${name(row.pegawai)} ${salaryPeriod(row)}`" :disabled="busy" @click="showSlip(row)" /><Button v-if="canWrite&&!row.jurnal" label="Tindakan" severity="secondary" text :aria-label="`Tindakan slip ${name(row.pegawai)} ${salaryPeriod(row)}`" aria-controls="salary-actions" aria-haspopup="menu" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="openMenu($event,row)"><template #icon><Icon name="caret-down" /></template></Button></div></li></ul>
        <Paginator v-if="filtered.length>15" v-model:first="first" :rows="15" :total-records="filtered.length" :page-link-size="3" template="PrevPageLink PageLinks NextPageLink"><template #prevpagelinkicon><Icon name="caret-left" /></template><template #nextpagelinkicon><Icon name="caret-right" /></template></Paginator>
      </template>
      <p class="employee-footnote"><Icon name="info" /><span>Jurnal dibuat berarti jurnal tertaut pada slip. Persetujuan dan pencatatan ke buku besar dilanjutkan pada modul Jurnal.</span></p>
    </section>
    <Menu id="salary-actions" ref="menu" :model="items" class="employee-action-menu" popup @show="menuOpen=true" @hide="menuOpen=false"><template #item="{item,props:itemProps}"><a v-bind="itemProps.action"><Icon v-if="item.icon" :name="item.icon" /><span>{{ item.label }}</span></a></template></Menu>
    <GajiFormDialog v-model="formOpen" :row="editing" :staff="staff" :loans="loans" :options-loading="optionsLoading" :options-error="optionsError" :saving="saving" :uncertain="uncertainSave" :error="formError" @save="save" @reload-options="loadOptions" @review="reviewSave" />
    <EmployeeActionDialog :visible="!!target" :title="action==='delete'?'Hapus slip gaji?':'Posting gaji ke jurnal?'" :label="target?`${name(target.pegawai)} — ${salaryPeriod(target)}`:''" :amount="target?money(target.total_netto):''" :description="action==='delete'?'Slip dan komponennya akan dihapus. Tindakan hanya tersedia jika jurnal belum dibuat.':'Sistem membuat jurnal gaji berstatus Draf dan mengurangi saldo kasbon sesuai potongan pada slip tersimpan. Jurnal belum masuk buku besar. Periksa potongan dan netto sebelum melanjutkan.'" :confirm-label="action==='delete'?'Hapus slip':'Buat jurnal gaji'" :danger="action==='delete'" :pending="pending" :checking="checking" :ready="actionReady" :error="actionError" :uncertain="uncertainAction" @close="closeAction" @confirm="confirmAction" @refresh="refreshAction" />
    <Dialog :visible="!!slip" @update:visible="value=>{if(!value){slip=null;afterPrint()}}" header="Rincian slip gaji" class="payroll-slip-dialog" :pt="{mask:{class:'payroll-print-mask'}}" modal :draggable="false" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup rincian slip'}"><template #closeicon><Icon name="x" /></template><GajiSlipPreview v-if="slip" :slip="slip" :pegawai="staff.find(row=>row.id===slip?.pegawai)??null" :bulan-label="salaryPeriod(slip)" /><template #footer><Button label="Tutup rincian" severity="secondary" @click="slip=null;afterPrint()" /><Button label="Cetak slip" @click="print"><template #icon><Icon name="printer" /></template></Button></template></Dialog>
  </PageLayout>
</template>
