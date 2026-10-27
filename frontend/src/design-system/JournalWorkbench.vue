<script setup lang="ts">
import { computed, ref } from "vue"
import Button from "primevue/button"
import Select from "primevue/select"
import { useToast } from "primevue/usetoast"
import JurnalDirectory from "@/features/jurnal/JurnalDirectory.vue"
import JurnalDetailDialog from "@/features/jurnal/JurnalDetailDialog.vue"
import JurnalFormDialog from "@/features/jurnal/JurnalFormDialog.vue"
import JurnalActionDialog from "@/features/jurnal/JurnalActionDialog.vue"
import { journalActions, type JournalAction } from "@/features/jurnal/presentation"
import type { Jurnal, JurnalInput, JurnalStatus } from "@/types/api"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { journalAccounts, journalSamples } from "./journal-fixtures"
const toast=useToast()
const rows=ref(structuredClone(journalSamples))
const role=ref("Finance"),kind=ref<string|null>(null)
const access=computed(()=>({finance:role.value==='Finance',principal:role.value==='SchoolPrincipal',userId:role.value==='Finance'?1:2}))
const filters=ref<{search:string;status:JurnalStatus|null}>({search:"",status:null}),page=ref(1)
const filtered=computed(()=>rows.value.filter(row=>(!filters.value.search||`${row.no_bukti} ${row.keterangan??''}`.toLocaleLowerCase('id').includes(filters.value.search.toLocaleLowerCase('id')))&&(!filters.value.status||row.status===filters.value.status)&&(!kind.value||row.detail.some(line=>line.kode_akun.startsWith(kind.value==='masuk'?'4':'5')))))
const detail=ref<Jurnal|null>(null),editing=ref<Jurnal|null>(null),formVisible=ref(false)
const target=ref<Jurnal|null>(null),action=ref<Exclude<JournalAction,'edit'>|null>(null),actionError=ref("")
function apply(value:{search:string;status:JurnalStatus|null}){filters.value=value;page.value=1}
function create(){editing.value=null;formVisible.value=true}
function choose(value:JournalAction,row:Jurnal){if(!journalActions(row,access.value).includes(value))return;if(value==='edit'){editing.value=row;formVisible.value=true}else{target.value=row;action.value=value;actionError.value=""}}
function message(summary:string){toast.add({severity:'success',summary,detail:'Hanya mengubah contoh di halaman ini. Tidak mengirim transaksi sekolah.',life:4000})}
function save(payload:JurnalInput){
  const id=editing.value?.id??`CONTOH-${crypto.randomUUID()}`
  const result:Jurnal={...journalSamples[0]!,...payload,id,detail:payload.detail,status:'DRAFT',tipe_sumber:'MANUAL',created_by:1,can_finance_post:payload.detail.some(line=>/^[45]/.test(line.kode_akun))}
  rows.value=editing.value?rows.value.map(row=>row.id===id?result:row):[result,...rows.value]
  if(detail.value?.id===id)detail.value=result
  formVisible.value=false;message('Draf contoh disimpan')
}
function confirm(reason:string){
  const row=target.value,value=action.value
  if(!row||!value||!journalActions(row,access.value).includes(value))return
  if(value==='cancel'&&!reason.trim())return
  if(value==='void'){
    if(rows.value.some(item=>item.no_bukti===`REV-${row.no_bukti}`)){actionError.value='Jurnal contoh ini sudah memiliki jurnal pembalik.';return}
    rows.value=[{...row,id:crypto.randomUUID(),no_bukti:`REV-${row.no_bukti}`,keterangan:`Pembalik atas ${row.no_bukti}`,tipe_sumber:'REVERSAL',can_finance_post:false,created_by:2,approved_by:2,detail:row.detail.map(line=>({...line,debit:line.kredit,kredit:line.debit}))},...rows.value]
  }else if(value==='remove')rows.value=rows.value.filter(item=>item.id!==row.id)
  else rows.value=rows.value.map(item=>item.id!==row.id?item:{...item,status:value==='submit'?'PENDING':value==='cancel'?'VOID':'POSTED'})
  target.value=null;action.value=null;detail.value=null;message(value==='void'?'Jurnal pembalik contoh dicatat':'Status jurnal contoh diperbarui')
}
function reset(){rows.value=structuredClone(journalSamples);page.value=1;detail.value=null;target.value=null;action.value=null;formVisible.value=false}
function changeRole(){detail.value=null;target.value=null;action.value=null;formVisible.value=false}
</script>
<template>
  <section id="layar-jurnal" class="system-section"><header class="system-section-heading"><h2>Dari bukti ke buku besar.</h2><p>Komponen yang sama dengan layar Jurnal aplikasi. Periksa draf manual, penerimaan otomatis, serta persetujuan Kepsek. Semua data fiktif; tidak ada request API.</p></header>
    <div class="journal-demo-controls"><div><label for="journal-demo-role">Peran contoh</label><Select input-id="journal-demo-role" v-model="role" :options="[{label:'Finance',value:'Finance'},{label:'Kepala sekolah',value:'SchoolPrincipal'}]" option-label="label" option-value="value" @change="changeRole"><template #dropdownicon><Icon name="caret-down" /></template></Select></div><div><label for="journal-demo-kind">Jenis jurnal contoh</label><Select input-id="journal-demo-kind" v-model="kind" placeholder="Semua jurnal" :options="[{label:'Semua jurnal',value:null},{label:'Pemasukan',value:'masuk'},{label:'Pengeluaran',value:'keluar'}]" option-label="label" option-value="value" @change="page=1"><template #dropdownicon><Icon name="caret-down" /></template></Select></div><Button v-if="access.finance" label="Buat jurnal contoh" @click="create"><template #icon><Icon name="plus" /></template></Button></div>
    <JurnalDirectory :rows="filtered.slice((page-1)*10,page*10)" :total="filtered.length" :page="page" :search="filters.search" :status="filters.status" @filter="apply" @page="page=$event" @inspect="detail=$event" />
    <Button class="journal-demo-reset" label="Pulihkan jurnal contoh" severity="secondary" text @click="reset" />
    <JurnalDetailDialog v-model:target="detail" :accounts="journalAccounts" :access="access" @action="choose" />
    <JurnalFormDialog v-model="formVisible" :journal="editing" :accounts="journalAccounts" @save="save" />
    <JurnalActionDialog :target="target" :action="action" :error="actionError" @close="target=null;action=null" @confirm="confirm" @refresh="actionError='Status contoh sudah dimuat. Tidak ada koneksi ke server.'" />
  </section>
</template>
<style scoped>
.journal-demo-controls{display:flex;flex-wrap:wrap;gap:var(--bee-space-4);align-items:end;margin-bottom:var(--bee-space-5)}.journal-demo-controls>div{display:grid;gap:var(--bee-space-2);min-width:0;flex:1 1 200px}.journal-demo-controls label{font-weight:500;font-size:var(--bee-type-caption)}.journal-demo-reset{margin-top:var(--bee-space-3)}
</style>
