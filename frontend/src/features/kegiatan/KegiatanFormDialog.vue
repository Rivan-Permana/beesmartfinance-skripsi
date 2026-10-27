<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, nextTick, reactive, ref, watch } from "vue"
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { calendarTextMatches, formatLocalDate } from "@/core/format"
import type { Coa, Kegiatan, KegiatanStatus, Pegawai, PeriodeAkuntansi } from "@/types/api"
import { kegiatanStatusOptions } from "./presentation"
const props=defineProps<{activity:Kegiatan|null;accounts:Coa[];staff:Pegawai[];periods:PeriodeAkuntansi[];saving?:boolean;error?:string}>()
const visible=defineModel<boolean>({default:false})
const emit=defineEmits<{save:[payload:Partial<Kegiatan>];reloadOptions:[]}>()
const form=reactive({nama:"",akun_beban:"",pagu:0,penanggung_jawab:null as number|null,periode:null as number|null,tanggal_mulai:null as Date|null,tanggal_selesai:null as Date|null,status:"RENCANA" as KegiatanStatus})
const attempted=ref(false)
const invalidDateInput=reactive({start:false,end:false})
const element=ref<HTMLFormElement|null>(null)
const errorElement=ref<HTMLElement|null>(null)
const nameInvalid=computed(()=>!form.nama.trim())
const amountInvalid=computed(()=>!Number.isFinite(form.pagu)||form.pagu<=0)
const dateError=computed(()=>{
  if(invalidDateInput.start||invalidDateInput.end) return "Tanggal yang diketik tidak valid. Periksa atau pilih ulang tanggal kegiatan."
  if(form.tanggal_mulai && !Number.isFinite(form.tanggal_mulai.getTime())) return "Pilih tanggal mulai yang valid."
  if(form.tanggal_selesai && !Number.isFinite(form.tanggal_selesai.getTime())) return "Pilih tanggal selesai yang valid."
  if(form.tanggal_mulai && form.tanggal_selesai && form.tanggal_selesai<form.tanggal_mulai) return "Tanggal selesai tidak boleh sebelum tanggal mulai."
  return ""
})
watch(visible,open=>{
  if(!open) return
  attempted.value=false
  invalidDateInput.start=false;invalidDateInput.end=false
  const row=props.activity
  Object.assign(form,{nama:row?.nama??"",akun_beban:row?.akun_beban??"",pagu:Number(row?.pagu??0),penanggung_jawab:row?.penanggung_jawab??null,periode:row?.periode??props.periods.find(item=>item.status==="OPEN")?.id??null,tanggal_mulai:row?.tanggal_mulai?new Date(row.tanggal_mulai+"T12:00:00"):null,tanggal_selesai:row?.tanggal_selesai?new Date(row.tanggal_selesai+"T12:00:00"):null,status:row?.status??"RENCANA"})
},{immediate:true})
watch(()=>props.error,async value=>{if(value){await nextTick();errorElement.value?.focus()}})
async function submit(){
  if(props.saving) return
  attempted.value=true
  if(nameInvalid.value||!form.akun_beban||amountInvalid.value||dateError.value){await nextTick();element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();return}
  emit("save",{nama:form.nama.trim(),akun_beban:form.akun_beban,pagu:form.pagu.toFixed(2),penanggung_jawab:form.penanggung_jawab,periode:form.periode,tanggal_mulai:form.tanggal_mulai?formatLocalDate(form.tanggal_mulai):null,tanggal_selesai:form.tanggal_selesai?formatLocalDate(form.tanggal_selesai):null,status:form.status})
}
function checkDateInput(event:Event,field:"start"|"end"){
  if(event.target instanceof HTMLInputElement)invalidDateInput[field]=!calendarTextMatches(event.target.value,field==="start"?form.tanggal_mulai:form.tanggal_selesai)
}
</script>
<template>
  <Dialog v-model:visible="visible" :header="activity?'Ubah kegiatan':'Buat kegiatan'" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :style="{width:'640px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form kegiatan'}"><template #closeicon><Icon name="x" /></template>
    <p class="activity-intro">Tetapkan pagu, tahun pelajaran, dan penanggung jawab sebelum mencatat realisasi.</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="activity-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Input tetap ada di form.</Message></div>
    <div v-if="!accounts.length" class="activity-notice"><Message severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>Pilihan akun beban belum tersedia. Muat ulang sebelum menyimpan kegiatan baru.</Message><Button label="Muat ulang pilihan" severity="secondary" @click="emit('reloadOptions')" /></div>
    <form id="activity-form" ref="element" novalidate :aria-busy="saving" @submit.prevent="submit"><fieldset :disabled="saving" class="activity-fields">
      <div class="activity-field activity-full"><label for="activity-name">Nama kegiatan <span>(wajib)</span></label><InputText id="activity-name" v-model="form.nama" autofocus required :invalid="attempted&&nameInvalid" :aria-invalid="attempted&&nameInvalid" :aria-describedby="attempted&&nameInvalid?'activity-name-error':undefined" fluid /><small v-if="attempted&&nameInvalid" id="activity-name-error" class="activity-field-error">Isi nama kegiatan.</small></div>
      <div class="activity-field activity-full"><label for="activity-account">Akun beban <span>(wajib)</span></label><Select :key="(saving) ? 'locked' : 'editable'" input-id="activity-account" v-model="form.akun_beban" :options="accounts" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih akun beban" :disabled="saving" :invalid="attempted&&!form.akun_beban" :aria-invalid="attempted&&!form.akun_beban" :aria-describedby="attempted&&!form.akun_beban?'activity-account-error':undefined" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select><small v-if="attempted&&!form.akun_beban" id="activity-account-error" class="activity-field-error">Pilih akun beban kegiatan.</small></div>
      <div class="activity-field"><label for="activity-budget">Pagu anggaran <span>(Rp, wajib)</span></label><InputNumber input-id="activity-budget" :model-value="form.pagu" @update:model-value="form.pagu=$event??0" :min="0" :max-fraction-digits="2" locale="id-ID" :invalid="attempted&&amountInvalid" :input-props="{'aria-invalid':attempted&&amountInvalid,'aria-describedby':attempted&&amountInvalid?'activity-budget-error':undefined}" fluid /><small v-if="attempted&&amountInvalid" id="activity-budget-error" class="activity-field-error">Isi pagu lebih dari nol.</small></div>
      <div class="activity-field"><label for="activity-pic">Guru penanggung jawab (PJ)</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="activity-pic" v-model="form.penanggung_jawab" :options="staff" option-label="nama" option-value="id" filter show-clear placeholder="Pilih penanggung jawab" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
      <div class="activity-field activity-full"><label for="activity-period">Tahun pelajaran</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="activity-period" v-model="form.periode" :options="periods" option-label="kode" option-value="id" filter show-clear placeholder="Pilih tahun pelajaran" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
      <div class="activity-field"><label for="activity-start">Tanggal mulai</label><DatePicker :key="saving ? 'locked' : 'editable'" input-id="activity-start" v-model="form.tanggal_mulai" @input="checkDateInput($event,'start')" @update:model-value="invalidDateInput.start=false" date-format="dd/mm/yy" show-button-bar :disabled="saving" :invalid="attempted&&!!dateError" :input-props="{'aria-invalid':attempted&&!!dateError,'aria-describedby':attempted&&dateError?'activity-date-error':undefined}" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker></div>
      <div class="activity-field"><label for="activity-end">Tanggal selesai</label><DatePicker :key="saving ? 'locked' : 'editable'" input-id="activity-end" v-model="form.tanggal_selesai" @input="checkDateInput($event,'end')" @update:model-value="invalidDateInput.end=false" date-format="dd/mm/yy" show-button-bar :disabled="saving" :invalid="attempted&&!!dateError" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker></div>
      <small v-if="attempted&&dateError" id="activity-date-error" class="activity-field-error activity-full">{{ dateError }}</small>
      <div class="activity-field activity-full"><label for="activity-state">Status kegiatan</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="activity-state" v-model="form.status" :options="kegiatanStatusOptions" option-label="label" option-value="value" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
    </fieldset></form>
    <template #footer><Button label="Batal" severity="secondary" :disabled="saving" @click="visible=false" /><Button :label="activity?'Simpan perubahan':'Buat kegiatan'" type="submit" form="activity-form" :loading="saving"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
<style scoped>
.activity-intro { margin: 0 0 var(--bee-space-5); color: var(--app-text-muted); }.activity-notice { display: grid; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); }.activity-fields { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: var(--bee-space-5) var(--bee-space-4); border: 0; margin: 0; padding: 0; min-width: 0; }.activity-field { display: flex; flex-direction: column; gap: var(--bee-space-2); min-width: 0; }.activity-full { grid-column: 1/-1; }.activity-field label { font-weight: 500; }.activity-field label span { font-weight: 400; color: var(--app-text-muted); }.activity-field-error { color: var(--bee-color-critical); font-size: var(--bee-type-caption); }
@media(max-width:520px) { .activity-fields { grid-template-columns: minmax(0,1fr); } }
</style>
