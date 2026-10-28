<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Message from 'primevue/message'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { calendarTextMatches, formatLocalDate } from '@/core/format'
import type { Pegawai, Pinjaman } from '@/types/api'
import { cents, money } from './payroll'
import { payrollEligible } from './staff'
const props=defineProps<{row:Pinjaman|null;staff:Pegawai[];optionsLoading:boolean;optionsError:string;saving:boolean;uncertain:boolean;error:string}>()
const visible=defineModel<boolean>({default:false})
const emit=defineEmits<{save:[payload:Partial<Pinjaman>];reloadOptions:[];review:[]}>()
const form=reactive({pegawai:null as number|null,tanggal:new Date() as Date|null,jumlah:null as number|null,tenor:1 as number|null,angsuran:null as number|null})
const attempted=ref(false),badDate=ref(false),element=ref<HTMLFormElement|null>(null),errorElement=ref<HTMLElement|null>(null)
const locked=computed(()=>props.saving||props.uncertain)
const employees=computed(()=>props.staff.filter(row=>payrollEligible(row)||row.id===props.row?.pegawai))
const dateInvalid=computed(()=>badDate.value||!form.tanggal||!Number.isFinite(form.tanggal.getTime()))
const invalid=computed(()=>!form.pegawai||!employees.value.some(row=>row.id===form.pegawai)||dateInvalid.value||cents(form.jumlah)==null||(form.jumlah??0)<=0||cents(form.angsuran)==null||!Number.isInteger(form.tenor)||!form.tenor||form.tenor<1)
watch(visible,open=>{if(!open)return;const row=props.row;attempted.value=false;badDate.value=false;Object.assign(form,{pegawai:row?.pegawai??null,tanggal:row?new Date(row.tanggal_pinjaman+'T12:00:00'):new Date(),jumlah:row?Number(row.jumlah_pinjaman):null,tenor:row?.tenor_bulan??1,angsuran:row?Number(row.angsuran_per_bulan):null})},{immediate:true})
watch(()=>props.error,async error=>{if(error){await nextTick();errorElement.value?.focus()}})
function checkDate(event:Event){badDate.value=!calendarTextMatches((event.target as HTMLInputElement).value,form.tanggal)}
async function save(){if(locked.value||props.optionsLoading||props.optionsError)return;attempted.value=true;if(invalid.value){await nextTick();element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();return}emit('save',{pegawai:form.pegawai!,tanggal_pinjaman:formatLocalDate(form.tanggal!),jumlah_pinjaman:form.jumlah!.toFixed(2),tenor_bulan:form.tenor!,angsuran_per_bulan:form.angsuran!.toFixed(2)})}
</script>
<template>
  <Dialog v-model:visible="visible" :header="row?'Ubah pengajuan kasbon':'Ajukan kasbon'" class="employee-form-dialog employee-loan-dialog" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form kasbon'}"><template #closeicon><Icon name="x" /></template>
    <p class="employee-intro">Catat kesepakatan pinjaman pegawai. Menyimpan pengajuan belum membuat jurnal pencairan.</p>
    <div v-if="optionsError" class="employee-notice"><Message severity="warn" :closable="false">{{ optionsError }}</Message><Button label="Muat ulang pegawai" severity="secondary" :disabled="locked" :loading="optionsLoading" @click="emit('reloadOptions')" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div>
    <form id="loan-form" ref="element" novalidate @submit.prevent="save" :aria-busy="saving"><fieldset :disabled="locked" class="employee-form-section"><legend>Rincian pengajuan</legend><div class="employee-fields">
      <div class="employee-field employee-full"><label for="loan-employee">Pegawai (wajib)</label><Select :key="locked||optionsLoading?'locked':'editable'" input-id="loan-employee" v-model="form.pegawai" :options="employees" option-label="nama" option-value="id" filter placeholder="Pilih pegawai" :disabled="locked||!!row||optionsLoading" :invalid="attempted&&!form.pegawai" :aria-invalid="attempted&&!form.pegawai" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select></div>
      <div class="employee-field"><label for="loan-date">Tanggal pinjaman</label><DatePicker :key="locked?'locked':'editable'" input-id="loan-date" v-model="form.tanggal" date-format="dd/mm/yy" :disabled="locked" @input="checkDate" @update:model-value="badDate=false" :invalid="attempted&&dateInvalid" :input-props="{'aria-invalid':attempted&&dateInvalid,'aria-describedby':attempted&&dateInvalid?'loan-date-error':undefined}" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted&&dateInvalid" id="loan-date-error" class="employee-field-error">Periksa atau pilih ulang tanggal pinjaman.</small></div>
      <div class="employee-field"><label for="loan-amount">Jumlah pinjaman (Rp)</label><InputNumber input-id="loan-amount" v-model="form.jumlah" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="locked" :invalid="attempted&&(cents(form.jumlah)==null||(form.jumlah??0)<=0)" :input-props="{'aria-invalid':attempted&&(cents(form.jumlah)==null||(form.jumlah??0)<=0)}" fluid /></div>
      <div class="employee-field"><label for="loan-term">Tenor (bulan)</label><InputNumber input-id="loan-term" v-model="form.tenor" :min="1" :use-grouping="false" :disabled="locked" :input-props="{'aria-invalid':attempted&&(!Number.isInteger(form.tenor)||!form.tenor||form.tenor<1)}" fluid /></div>
      <div class="employee-field"><label for="loan-installment">Angsuran per bulan (Rp)</label><InputNumber input-id="loan-installment" v-model="form.angsuran" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="locked" :invalid="attempted&&cents(form.angsuran)==null" :input-props="{'aria-invalid':attempted&&cents(form.angsuran)==null,'aria-describedby':'loan-installment-help'}" fluid /><small id="loan-installment-help">Isi sesuai kesepakatan. Angka 0 membuat server memakai seluruh sisa pinjaman sebagai potongan pada gaji berikutnya.</small></div>
    </div></fieldset>
    <div class="employee-preview"><div><span>Pinjaman diajukan</span><strong>{{ money(form.jumlah) }}</strong></div><div><span>Angsuran tercatat</span><strong>{{ money(form.angsuran) }}</strong></div></div>
    <p class="employee-small-note">Tenor dan angsuran dicatat terpisah. Sistem tidak membagi otomatis jumlah pinjaman berdasarkan tenor.</p>
    <Message v-if="attempted&&invalid" severity="error" :closable="false">Pilih pegawai, tanggal yang valid, jumlah lebih dari nol, tenor minimal 1 bulan, dan angsuran nol atau lebih.</Message>
    <div v-if="error" ref="errorElement" tabindex="-1"><Message severity="error" :closable="false">{{ error }} Input tetap ada.</Message></div>
    <Message v-if="uncertain" severity="warn" :closable="false">Hasil penyimpanan belum terkonfirmasi. Periksa daftar kasbon sebelum membuat atau mengubah pengajuan kembali.</Message>
    </form>
    <template #footer><div class="employee-footer-total"><span>Pinjaman diajukan</span><strong>{{ money(form.jumlah) }}</strong></div><Button label="Kembali" severity="secondary" :disabled="saving" @click="visible=false" /><Button v-if="uncertain" label="Periksa daftar kasbon" severity="secondary" @click="emit('review')" /><Button v-else :label="row?'Simpan perubahan':'Simpan pengajuan'" type="submit" form="loan-form" :loading="saving" :disabled="saving||optionsLoading||!!optionsError"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template><template #icon><Icon name="check" /></template></Button></template>
  </Dialog>
</template>
