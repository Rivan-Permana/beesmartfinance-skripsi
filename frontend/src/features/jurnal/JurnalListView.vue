<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { useRoute } from "vue-router"
import Button from "primevue/button"
import Message from "primevue/message"
import { useToast } from "primevue/usetoast"
import { friendlyError, jurnalActionSuccessMessage, notifySuccess } from "@/core/errors"
import Icon from "@/shared/components/PhosphorIcon.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Coa, Jurnal, JurnalInput, JurnalStatus } from "@/types/api"
import { coaApi, jurnalApi } from "./api"
import JurnalDirectory from "./JurnalDirectory.vue"
import JurnalFormDialog from "./JurnalFormDialog.vue"
import JurnalDetailDialog from "./JurnalDetailDialog.vue"
import JurnalActionDialog from "./JurnalActionDialog.vue"
import { journalActions, type JournalAction } from "./presentation"

const route=useRoute(), auth=useAuthStore(), toast=useToast()
const rows=ref<Jurnal[]>([]), accounts=ref<Coa[]>([])
const loading=ref(false), loadingAccounts=ref(false), accountsError=ref(false)
const error=ref(""), page=ref(1), total=ref(0)
const filters=ref<{search:string;status:JurnalStatus|null}>({search:"",status:null})
let loadSequence=0
const access=computed(()=>({finance:auth.hasRole(["Finance"]),principal:auth.hasRole(["SchoolPrincipal"]),userId:auth.user?.id}))
const kind=computed(()=>route.query.jenis==='masuk'||route.query.jenis==='keluar'?route.query.jenis:null)
const title=computed(()=>kind.value==='masuk'?'Pemasukan':kind.value==='keluar'?'Pengeluaran':'Jurnal')
const subtitle=computed(()=>kind.value==='masuk'?'Jurnal dengan akun pendapatan. Periksa bukti sebelum mencatat.':kind.value==='keluar'?'Jurnal dengan akun beban. Periksa bukti sebelum mencatat.':'Bukti transaksi, rincian akun, dan pencatatan ke buku besar.')
function errorText(value:unknown,fallback:string){const result=friendlyError(value,fallback);return [result.summary,result.detail].filter(Boolean).join(". ")}
async function loadAccounts(){
  if(loadingAccounts.value)return
  loadingAccounts.value=true;accountsError.value=false
  try{accounts.value=await coaApi.list()}catch{accountsError.value=true}finally{loadingAccounts.value=false}
}
async function load(){
  const sequence=++loadSequence
  loading.value=true;error.value=""
  try{
    const data=await jurnalApi.list({page:page.value,page_size:10,...(kind.value?{jenis:kind.value}:{}),...(filters.value.status?{status:filters.value.status}:{}),...(filters.value.search?{search:filters.value.search}:{})})
    if(sequence!==loadSequence)return
    rows.value=data.results;total.value=data.count
  }catch(e){
    if(sequence!==loadSequence)return
    if((e as {response?:{status?:number}}).response?.status===404&&page.value>1){page.value=1;await load();return}
    rows.value=[];total.value=0;error.value=errorText(e,"Gagal memuat jurnal")
  }finally{if(sequence===loadSequence)loading.value=false}
}
function apply(value:{search:string;status:JurnalStatus|null}){filters.value=value;page.value=1;void load()}
function changePage(value:number){page.value=value;void load()}
watch(kind,()=>{page.value=1;void load()})

const detail=ref<Jurnal|null>(null), editing=ref<Jurnal|null>(null)
const formVisible=ref(false), saving=ref(false), formError=ref("")
const actionTarget=ref<Jurnal|null>(null), action=ref<Exclude<JournalAction,"edit">|null>(null)
const pending=ref(false), actionError=ref("")
function create(){
  if(!access.value.finance||saving.value||loadingAccounts.value||accountsError.value||!accounts.value.some(account=>account.is_active))return
  editing.value=null;formError.value="";formVisible.value=true
}
function choose(value:JournalAction,row:Jurnal){
  if(pending.value||saving.value||!journalActions(row,access.value).includes(value))return
  if(value==='edit'){editing.value=row;formError.value="";formVisible.value=true;return}
  actionTarget.value=row;action.value=value;actionError.value=""
}
async function save(payload:JurnalInput){
  if(saving.value||!access.value.finance)return
  if(editing.value&&!journalActions(editing.value,access.value).includes('edit')){formError.value="Jurnal ini tidak lagi dapat diubah sebagai draf.";return}
  saving.value=true;formError.value=""
  try{
    const result=editing.value?await jurnalApi.update(editing.value.id,payload):await jurnalApi.create(payload)
    notifySuccess(toast,editing.value?"Draf jurnal diperbarui":"Draf jurnal dibuat",{detail:"Belum masuk buku besar."})
    if(detail.value?.id===result.id)detail.value=result
    formVisible.value=false
    await load()
  }catch(e){formError.value=errorText(e,"Draf jurnal belum berhasil disimpan")}finally{saving.value=false}
}
function closeAction(){if(!pending.value){actionTarget.value=null;action.value=null;actionError.value=""}}
async function confirmAction(reason:string){
  const current=actionTarget.value, currentAction=action.value
  if(!current||!currentAction||pending.value)return
  if(!journalActions(current,access.value).includes(currentAction)){actionError.value="Status atau kewenangan tidak lagi sesuai. Periksa ulang daftar.";return}
  if((currentAction==='cancel'||currentAction==='cancelDraft'||currentAction==='reject')&&!reason.trim())return
  pending.value=true;actionError.value=""
  try{
    const result=await (currentAction==='remove'?jurnalApi.remove(current.id):currentAction==='cancel'||currentAction==='cancelDraft'?jurnalApi.batalPenerimaan(current.id,reason):currentAction==='reject'?jurnalApi.tolak(current.id,reason):jurnalApi[currentAction](current.id))
    if(currentAction==='remove'||currentAction==='cancel')notifySuccess(toast,currentAction==='remove'?"Draf jurnal dihapus":"Penerimaan dibatalkan")
    else if(currentAction==='cancelDraft')notifySuccess(toast,"Draf jurnal dibatalkan",{detail:`${current.no_bukti} batal; slip gaji atau kasbon sumbernya dapat diperbaiki dan diposting ulang.`})
    else if(currentAction==='reject')notifySuccess(toast,"Pengajuan ditolak",{detail:`${current.no_bukti} dikembalikan ke Draf untuk diperbaiki Staff Keuangan.`})
    else{const message=jurnalActionSuccessMessage(currentAction,result);notifySuccess(toast,message.summary,{detail:message.detail})}
    detail.value=null;actionTarget.value=null;action.value=null
    await load()
  }catch(e){actionError.value=errorText(e,"Tindakan belum berhasil diproses")}finally{pending.value=false}
}
async function refreshAction(){
  if(!actionTarget.value||pending.value)return
  pending.value=true
  try{
    const current=await jurnalApi.get(actionTarget.value.id)
    actionTarget.value=current
    if(detail.value?.id===current.id)detail.value=current
    if(action.value&&!journalActions(current,access.value).includes(action.value)){
      actionTarget.value=null;action.value=null;actionError.value=""
      notifySuccess(toast,"Status jurnal diperbarui",{detail:"Periksa rincian untuk tindakan yang masih tersedia."})
    }else{actionError.value="";notifySuccess(toast,"Status jurnal diperbarui",{detail:"Periksa rincian sebelum mencoba tindakan kembali."})}
    await load()
  }catch(e){actionError.value=errorText(e,"Status jurnal belum berhasil diperiksa")}finally{pending.value=false}
}
onMounted(()=>{void load();void loadAccounts()})
</script>
<template>
  <PageLayout :title="title" :subtitle="subtitle" :surface="false"><template #actions><Button v-if="access.finance" label="Buat jurnal" :disabled="loadingAccounts||accountsError||!accounts.some(account=>account.is_active)" @click="create"><template #icon><Icon name="plus" /></template></Button></template>
    <div v-if="accountsError||(!loadingAccounts&&!accounts.some(account=>account.is_active))" class="journal-account-notice"><Message severity="warn" :closable="false">{{ accountsError?'Daftar akun belum berhasil dimuat.':'Belum ada akun aktif untuk membuat jurnal.' }} Daftar jurnal tetap dapat dibaca.</Message><Button label="Muat ulang akun" severity="secondary" :loading="loadingAccounts" @click="loadAccounts" /></div>
    <p class="journal-role-note"><Icon name="info" /><span>{{ access.finance?'Finance mencatat jurnal harian yang memenuhi syarat. Penggajian, kegiatan, dan jurnal khusus diajukan sesuai alur persetujuan.':'Periksa jurnal yang menunggu persetujuan. Jurnal buatan sendiri dan penerimaan yang perlu dicocokkan tidak dapat disetujui di sini.' }}</span></p>
    <JurnalDirectory :rows="rows" :total="total" :page="page" :loading="loading" :error="error" :search="filters.search" :status="filters.status" @filter="apply" @page="changePage" @retry="load" @inspect="detail=$event" />
    <JurnalDetailDialog v-model:target="detail" :accounts="accounts" :access="access" :accounts-loading="loadingAccounts" :accounts-error="accountsError" @action="choose" @reload-accounts="loadAccounts" />
    <JurnalFormDialog v-model="formVisible" :journal="editing" :accounts="accounts" :saving="saving" :error="formError" :accounts-loading="loadingAccounts" :accounts-error="accountsError" @save="save" @reload-accounts="loadAccounts" />
    <JurnalActionDialog :target="actionTarget" :action="action" :pending="pending" :error="actionError" @close="closeAction" @confirm="confirmAction" @refresh="refreshAction" />
  </PageLayout>
</template>
<style scoped>
.journal-role-note{display:flex;align-items:start;gap:var(--bee-space-2);margin:0 0 var(--bee-space-5);color:var(--app-text-muted);font-size:var(--bee-type-ui);max-width:90ch}.journal-role-note .bee-icon{margin-top:2px;flex-shrink:0}.journal-account-notice{display:grid;justify-items:start;gap:var(--bee-space-3);margin-bottom:var(--bee-space-5)}
</style>
