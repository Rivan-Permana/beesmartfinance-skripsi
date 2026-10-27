<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Message from 'primevue/message'
import Icon from '@/shared/components/PhosphorIcon.vue'
import type { Gaji, Pegawai, Pinjaman } from '@/types/api'
import { cents, earnings, loanDeduction, money, months, sumMoney, type EarningKey } from './payroll'
import { payrollEligible } from './staff'

const props = defineProps<{row:Gaji|null;staff:Pegawai[];loans:Pinjaman[];optionsLoading:boolean;optionsError:string;saving:boolean;uncertain:boolean;error:string}>()
const visible = defineModel<boolean>({default:false})
const emit = defineEmits<{save:[payload:Partial<Gaji>];reloadOptions:[];review:[]}>()
const initial = Object.fromEntries(earnings.map(field=>[field.key,0])) as Record<EarningKey,number|null>
const form = reactive({...initial,pegawai:null as number|null,periode_bulan:1,periode_tahun:2026,hari_hadir:0 as number|null,potongan_asuransi:0 as number|null})
const attempted = ref(false), element = ref<HTMLFormElement|null>(null), errorElement = ref<HTMLElement|null>(null)
const locked = computed(()=>props.saving||props.uncertain)
const employees = computed(()=>props.staff.filter(row=>payrollEligible(row)||row.id===props.row?.pegawai))
const position = computed(()=>props.staff.find(row=>row.id===form.pegawai)?.jabatan?.trim()||'')
const deduction = computed(()=>props.optionsLoading||props.optionsError?null:loanDeduction(props.loans,form.pegawai))
const gross = computed(()=>sumMoney(earnings.map(field=>form[field.key])))
const deductions = computed(()=>sumMoney([deduction.value,form.potongan_asuransi]))
const net = computed(()=>gross.value==null||deductions.value==null?null:Math.round(gross.value*100-deductions.value*100)/100)
const unpaidApplications = computed(()=>props.loans.some(row=>row.pegawai===form.pegawai&&!row.ikut_potongan&&Number(row.sisa_pinjaman)>0))
watch(visible,open=>{
  if(!open)return
  attempted.value=false
  const row=props.row, now=new Date()
  for(const field of earnings)form[field.key]=row?Number(row[field.key]):0
  Object.assign(form,{pegawai:row?.pegawai??null,periode_bulan:row?.periode_bulan??now.getMonth()+1,periode_tahun:row?.periode_tahun??now.getFullYear(),hari_hadir:row?.hari_hadir??0,potongan_asuransi:row?Number(row.potongan_asuransi):0})
},{immediate:true})
watch(()=>props.error,async error=>{if(error){await nextTick();errorElement.value?.focus()}})
const invalid = computed(()=>!form.pegawai||!employees.value.some(row=>row.id===form.pegawai)||!Number.isInteger(form.periode_tahun)||form.periode_tahun<2020||form.periode_tahun>2100||!Number.isInteger(form.hari_hadir)||form.hari_hadir==null||form.hari_hadir<0||gross.value==null||deductions.value==null)
async function save(){
  if(locked.value||props.optionsLoading||props.optionsError)return
  attempted.value=true
  if(invalid.value){await nextTick();element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();return}
  const values=Object.fromEntries(earnings.map(field=>[field.key,form[field.key]!.toFixed(2)]))
  emit('save',{...values,pegawai:form.pegawai!,periode_bulan:form.periode_bulan,periode_tahun:form.periode_tahun,hari_hadir:form.hari_hadir!,potongan_asuransi:form.potongan_asuransi!.toFixed(2)})
}
</script>

<template>
  <Dialog v-model:visible="visible" :header="row?'Ubah slip gaji':'Buat slip gaji'" class="employee-form-dialog employee-salary-dialog" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form gaji'}"><template #closeicon><Icon name="x" /></template>
    <p class="employee-intro">Lengkapi pendapatan dan potongan. Menyimpan slip belum membuat jurnal atau mencatat pengeluaran ke buku besar.</p>
    <div v-if="optionsError" class="employee-notice"><Message severity="warn" :closable="false">{{ optionsError }} Perkiraan potongan belum tersedia.</Message><Button label="Muat ulang data pendukung" severity="secondary" :disabled="locked" :loading="optionsLoading" @click="emit('reloadOptions')" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div>
    <form id="salary-form" ref="element" novalidate @submit.prevent="save" :aria-busy="saving">
      <fieldset :disabled="locked" class="employee-form-section"><legend>Pegawai dan periode</legend><div class="employee-fields">
        <div class="employee-field employee-full"><label for="salary-employee">Pegawai (wajib)</label><Select :key="locked||optionsLoading?'locked':'editable'" input-id="salary-employee" v-model="form.pegawai" :options="employees" option-label="nama" option-value="id" filter placeholder="Pilih pegawai" :disabled="locked||!!row||optionsLoading" :invalid="attempted&&!form.pegawai" :aria-invalid="attempted&&!form.pegawai" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select><small v-if="form.pegawai" class="salary-position">Jabatan: <strong>{{ position||'Belum diisi di Data Pegawai' }}</strong> · diambil otomatis dari Data Pegawai</small><small v-if="row">Pegawai pada slip tersimpan tetap dipertahankan.</small><small v-if="attempted&&!form.pegawai" class="employee-field-error">Pilih pegawai.</small></div>
        <div class="employee-field"><label for="salary-month">Bulan gaji</label><Select :key="locked?'locked':'editable'" input-id="salary-month" v-model="form.periode_bulan" :options="months.map((label,index)=>({label,value:index+1}))" option-label="label" option-value="value" :disabled="locked" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div class="employee-field"><label for="salary-year">Tahun gaji</label><InputNumber input-id="salary-year" v-model="form.periode_tahun" :use-grouping="false" :min="2020" :max="2100" :disabled="locked" :input-props="{'aria-invalid':attempted&&(!Number.isInteger(form.periode_tahun)||form.periode_tahun<2020||form.periode_tahun>2100)}" fluid /></div>
      </div></fieldset>
      <fieldset :disabled="locked" class="employee-form-section"><legend>Pendapatan <span>Rupiah</span></legend><div class="employee-fields">
        <div v-for="field in earnings" :key="field.key" class="employee-field"><label :for="`salary-${field.key}`">{{ field.label }}</label><InputNumber :input-id="`salary-${field.key}`" v-model="form[field.key]" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="locked" :invalid="attempted&&cents(form[field.key])==null" :input-props="{'aria-invalid':attempted&&cents(form[field.key])==null}" fluid /><small v-if="attempted&&cents(form[field.key])==null" class="employee-field-error">Isi nol atau nominal yang valid.</small></div>
        <div class="employee-field"><label for="salary-attendance">Hari hadir tercatat</label><InputNumber input-id="salary-attendance" v-model="form.hari_hadir" :min="0" :use-grouping="false" :disabled="locked" :input-props="{'aria-invalid':attempted&&(form.hari_hadir==null||!Number.isInteger(form.hari_hadir)||form.hari_hadir<0)}" fluid /><small>Catatan hari pada slip. Tidak menghitung ulang uang makan.</small></div>
      </div></fieldset>
      <fieldset :disabled="locked" class="employee-form-section"><legend>Potongan <span>Rupiah</span></legend><div class="employee-fields">
        <div class="employee-field"><label for="salary-insurance">Potongan asuransi</label><InputNumber input-id="salary-insurance" v-model="form.potongan_asuransi" locale="id-ID" :min="0" :max-fraction-digits="2" :disabled="locked" :invalid="attempted&&cents(form.potongan_asuransi)==null" :input-props="{'aria-invalid':attempted&&cents(form.potongan_asuransi)==null}" fluid /></div>
        <div class="employee-field"><span class="employee-field-label">Perkiraan potongan kasbon</span><output class="employee-readonly">{{ money(deduction) }}</output><small>Server menghitung ulang saat slip disimpan, termasuk saat mengubah slip.</small><small v-if="row">Potongan pada slip tersimpan: {{ money(row.potongan_pinjaman) }}.</small></div>
      </div><Message v-if="unpaidApplications" severity="info" :closable="false" class="employee-inline-message">Pegawai ini punya pengajuan kasbon yang belum dicairkan atau belum disetujui. Pengajuan itu tidak ikut dipotong pada slip ini.</Message></fieldset>
      <div class="employee-preview"><div><span>Bruto</span><strong>{{ money(gross) }}</strong></div><div><span>Potongan</span><strong>{{ money(deductions) }}</strong></div><div><span>Perkiraan netto</span><strong>{{ money(net) }}</strong></div></div>
      <Message v-if="net!=null&&net<0" severity="warn" :closable="false">Netto negatif. Periksa pendapatan dan potongan sebelum melanjutkan.</Message>
      <Message v-if="attempted&&invalid" severity="error" :closable="false">Periksa pegawai, periode, hari hadir, dan nominal. Gunakan angka nol untuk komponen yang tidak dikenakan.</Message>
      <div v-if="error" ref="errorElement" tabindex="-1"><Message severity="error" :closable="false">{{ error }} Input tetap ada.</Message></div>
      <Message v-if="uncertain" severity="warn" :closable="false">Hasil penyimpanan belum terkonfirmasi. Periksa daftar sebelum mencoba membuat atau mengubah slip kembali.</Message>
    </form>
    <template #footer><div class="employee-footer-total"><span>Perkiraan netto</span><strong>{{ money(net) }}</strong></div><Button label="Kembali" severity="secondary" :disabled="saving" @click="visible=false" /><Button v-if="uncertain" label="Periksa daftar gaji" severity="secondary" @click="emit('review')" /><Button v-else :label="row?'Simpan perubahan':'Simpan slip'" type="submit" form="salary-form" :loading="saving" :disabled="saving||optionsLoading||!!optionsError"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template><template #icon><Icon name="check" /></template></Button></template>
  </Dialog>
</template>
