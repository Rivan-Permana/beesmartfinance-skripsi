<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue"
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { calendarTextMatches, formatRp } from "@/core/format"
import type { Coa, Jurnal, JurnalInput } from "@/types/api"
import { journalFormValid, journalLineValid, journalPayload, journalTotals, type JournalForm } from "./presentation"
const props=defineProps<{journal:Jurnal|null;accounts:Coa[];saving?:boolean;error?:string;accountsLoading?:boolean;accountsError?:boolean}>()
const visible=defineModel<boolean>({default:false})
const emit=defineEmits<{save:[payload:JurnalInput];reloadAccounts:[]}>()
const attempted=ref(false), invalidDate=ref(false)
const element=ref<HTMLFormElement|null>(null), errorElement=ref<HTMLElement|null>(null)
const form=reactive<JournalForm>({no_bukti:"",tanggal:new Date(),keterangan:"",detail:[]})
const accounts=computed(()=>props.accounts.filter(account=>account.is_active||form.detail.some(line=>line.kode_akun===account.kode_akun)))
const totals=computed(()=>journalTotals(form.detail))
const dateInvalid=computed(()=>invalidDate.value||!form.tanggal||!Number.isFinite(form.tanggal.getTime()))
watch(visible,open=>{
  if(!open)return
  attempted.value=false;invalidDate.value=false
  const row=props.journal
  Object.assign(form,{no_bukti:row?.no_bukti??"",tanggal:row?new Date(row.tanggal+"T12:00:00"):new Date(),keterangan:row?.keterangan??"",detail:row?row.detail.map(line=>({kode_akun:line.kode_akun,debit:Number(line.debit),kredit:Number(line.kredit)})):[{kode_akun:null,debit:0,kredit:0},{kode_akun:null,debit:0,kredit:0}]})
  while(form.detail.length<2)form.detail.push({kode_akun:null,debit:0,kredit:0})
},{immediate:true})
watch(()=>props.error,async value=>{if(value){await nextTick();errorElement.value?.focus()}})
function checkDate(event:Event){if(event.target instanceof HTMLInputElement)invalidDate.value=!calendarTextMatches(event.target.value,form.tanggal)}
async function submit(){
  if(props.saving||props.accountsLoading||props.accountsError)return
  attempted.value=true
  if(dateInvalid.value||!journalFormValid(form,props.accounts)){
    await nextTick()
    const invalid=element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')
    if(invalid)invalid.focus();else element.value?.querySelector<HTMLElement>('.journal-balance')?.focus()
    return
  }
  emit("save",journalPayload(form))
}
</script>
<template>
  <Dialog v-model:visible="visible" class="journal-form-dialog" :header="journal?'Ubah draf jurnal':'Buat jurnal'" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :style="{width:'880px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form jurnal'}"><template #closeicon><Icon name="x" /></template>
    <p class="journal-form-intro">Draf belum masuk buku besar. Catat atau ajukan setelah rincian diperiksa.</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="journal-form-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Input tetap ada. Jika respons terputus, periksa daftar jurnal sebelum mengirim ulang.</Message></div>
    <div v-if="accountsError||(!accountsLoading&&!accounts.some(account=>account.is_active))" class="journal-form-notice"><Message severity="warn" :closable="false">Akun aktif belum tersedia. Muat ulang pilihan sebelum menyimpan.</Message><Button label="Muat ulang akun" severity="secondary" :disabled="saving" :loading="accountsLoading" @click="emit('reloadAccounts')" /></div>
    <form id="journal-form" ref="element" novalidate :aria-busy="saving" @submit.prevent="submit"><fieldset class="journal-form-fields" :disabled="saving">
      <div class="journal-meta"><div class="journal-field"><label for="journal-proof">Nomor bukti <span>(wajib)</span></label><InputText id="journal-proof" v-model="form.no_bukti" autofocus :invalid="attempted&&!form.no_bukti.trim()" :aria-invalid="attempted&&!form.no_bukti.trim()" :aria-describedby="attempted&&!form.no_bukti.trim()?'journal-proof-error':undefined" fluid /><small v-if="attempted&&!form.no_bukti.trim()" id="journal-proof-error" class="journal-field-error">Isi nomor bukti transaksi.</small></div><div class="journal-field"><label for="journal-date">Tanggal jurnal <span>(wajib)</span></label><DatePicker :key="saving ? 'locked' : 'editable'" input-id="journal-date" v-model="form.tanggal" date-format="dd/mm/yy" :disabled="saving" :invalid="attempted&&dateInvalid" :input-props="{'aria-invalid':attempted&&dateInvalid,'aria-describedby':attempted&&dateInvalid?'journal-date-error':undefined}" @input="checkDate" @update:model-value="invalidDate=false" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted&&dateInvalid" id="journal-date-error" class="journal-field-error">Periksa atau pilih ulang tanggal jurnal yang valid.</small></div><div class="journal-field journal-meta-description"><label for="journal-description">Keterangan transaksi</label><InputText id="journal-description" v-model="form.keterangan" fluid /></div></div>
      <div class="journal-lines-heading"><h3>Rincian akun</h3><p>Nominal dalam rupiah. Isi salah satu sisi pada tiap akun; total debit dan kredit harus sama.</p></div>
      <ol class="journal-lines"><li v-for="(line,index) in form.detail" :key="index"><div class="journal-line-number"><span>Baris {{ index+1 }}</span><Button :aria-label="`Hapus baris ${index+1}`" severity="danger" text :disabled="saving||form.detail.length<=2" @click="form.detail.splice(index,1)"><template #icon><Icon name="trash" /></template></Button></div><div class="journal-line-fields"><div class="journal-field journal-account"><label :for="`journal-account-${index}`">Akun <span>(wajib)</span></label><Select :key="(saving||accountsLoading) ? 'locked' : 'editable'" :input-id="`journal-account-${index}`" v-model="line.kode_akun" :options="accounts" option-label="nama_akun" option-value="kode_akun" :option-disabled="(account:Coa)=>!account.is_active" :disabled="saving||accountsLoading" :loading="accountsLoading" filter :filter-fields="['kode_akun','nama_akun']" placeholder="Pilih akun" :invalid="attempted&&!journalLineValid(line,props.accounts)" :aria-invalid="attempted&&!journalLineValid(line,props.accounts)" :aria-describedby="attempted&&!journalLineValid(line,props.accounts)?`journal-line-error-${index}`:undefined" fluid><template #value="{value,placeholder}"><span>{{ value ? `${value} — ${accounts.find(account=>account.kode_akun===value)?.nama_akun??'Akun belum dimuat'}`:placeholder }}</span></template><template #option="{option}"><span>{{ option.kode_akun }} — {{ option.nama_akun }}{{ option.is_active?'':' (nonaktif)' }}</span></template><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select></div><div class="journal-field"><label :for="`journal-debit-${index}`">Debit <span>(Rp)</span></label><InputNumber :input-id="`journal-debit-${index}`" :model-value="line.debit" @update:model-value="line.debit=$event??0" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="saving" :invalid="attempted&&!journalLineValid(line,props.accounts)" :input-props="{'aria-describedby':attempted&&!journalLineValid(line,props.accounts)?`journal-line-error-${index}`:undefined}" fluid /></div><div class="journal-field"><label :for="`journal-credit-${index}`">Kredit <span>(Rp)</span></label><InputNumber :input-id="`journal-credit-${index}`" :model-value="line.kredit" @update:model-value="line.kredit=$event??0" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="saving" :invalid="attempted&&!journalLineValid(line,props.accounts)" :input-props="{'aria-describedby':attempted&&!journalLineValid(line,props.accounts)?`journal-line-error-${index}`:undefined}" fluid /></div></div><small v-if="attempted&&!journalLineValid(line,props.accounts)" :id="`journal-line-error-${index}`" class="journal-field-error">Pilih akun aktif. Isi nominal valid pada salah satu sisi saja, maksimal dua desimal.</small></li></ol>
      <Button label="Tambah baris akun" severity="secondary" :disabled="saving" @click="form.detail.push({kode_akun:null,debit:0,kredit:0})"><template #icon><Icon name="plus" /></template></Button>
      <p v-if="attempted&&!totals?.balanced" class="journal-balance journal-field-error" tabindex="-1" role="alert">Samakan total debit dan kredit dengan nilai lebih dari nol sebelum menyimpan.</p>
    </fieldset></form>
    <template #footer><div class="journal-form-summary" aria-live="polite"><div><span>Total debit</span><strong>{{ totals?formatRp(totals.debit):'Periksa nominal' }}</strong></div><div><span>Total kredit</span><strong>{{ totals?formatRp(totals.kredit):'Periksa nominal' }}</strong></div><p :class="{'is-balanced':totals?.balanced}"><Icon :name="totals?.balanced?'check-circle':'warning-circle'" />{{ totals?.balanced?'Seimbang':totals&&totals.debit===0&&totals.kredit===0?'Belum ada nominal':totals?`Selisih ${formatRp(Math.abs(totals.debit-totals.kredit))}`:'Nominal belum valid' }}</p></div><div class="journal-form-buttons"><Button label="Batal" severity="secondary" :disabled="saving" @click="visible=false" /><Button label="Simpan draf" type="submit" form="journal-form" :loading="saving" :disabled="accountsLoading||accountsError"><template #icon><Icon name="floppy-disk" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div></template>
  </Dialog>
</template>
<style scoped>
.journal-form-intro{margin:0 0 var(--bee-space-5);color:var(--app-text-muted)}.journal-form-notice{display:grid;justify-items:start;gap:var(--bee-space-3);margin-bottom:var(--bee-space-5)}.journal-form-fields{border:0;padding:0;margin:0;min-width:0}.journal-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--bee-space-4)}.journal-meta-description{grid-column:1/-1}.journal-field{display:grid;align-content:start;gap:var(--bee-space-2);min-width:0}.journal-field label{font-weight:500}.journal-field label span{font-weight:400;color:var(--app-text-muted)}.journal-lines-heading{margin:var(--bee-space-6) 0 var(--bee-space-4)}.journal-lines-heading h3{font-size:var(--bee-type-section)}.journal-lines-heading p{color:var(--app-text-muted);font-size:var(--bee-type-caption);margin:var(--bee-space-1) 0 0}.journal-lines{list-style:none;padding:0;margin:0 0 var(--bee-space-4);display:grid;gap:var(--bee-space-5)}.journal-lines li{min-width:0}.journal-line-number{display:flex;justify-content:space-between;align-items:center;font-size:var(--bee-type-caption);color:var(--app-text-muted);margin-bottom:var(--bee-space-1)}.journal-line-fields{display:grid;grid-template-columns:minmax(0,2fr) repeat(2,minmax(0,1fr));gap:var(--bee-space-3)}.journal-account :deep(.p-select-label){white-space:normal;overflow-wrap:anywhere}.journal-field-error{color:var(--bee-color-critical);font-size:var(--bee-type-caption)}.journal-balance{margin-top:var(--bee-space-4)}
@media(max-width:600px){.journal-meta{grid-template-columns:minmax(0,1fr)}.journal-line-fields{grid-template-columns:repeat(2,minmax(0,1fr))}.journal-account{grid-column:1/-1}}
</style>
<style>
.journal-form-dialog .p-dialog-footer{display:block;border-top:1px solid var(--app-border)}.journal-form-summary{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:var(--bee-space-3);margin-bottom:var(--bee-space-4)}.journal-form-summary>div{display:grid;gap:var(--bee-space-1);min-width:0}.journal-form-summary span{font-size:var(--bee-type-caption);color:var(--app-text-muted)}.journal-form-summary strong{font-weight:500;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.journal-form-summary p{display:flex;align-items:center;gap:var(--bee-space-2);margin:0;font-size:var(--bee-type-caption);color:var(--bee-color-warning)}.journal-form-summary .is-balanced{color:var(--bee-color-positive)}.journal-form-buttons{display:flex;justify-content:flex-end;gap:var(--bee-space-3)}
@media(max-width:600px){.journal-form-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.journal-form-summary p{grid-column:1/-1}.journal-form-buttons{display:grid;grid-template-columns:1fr 1fr}}
</style>
