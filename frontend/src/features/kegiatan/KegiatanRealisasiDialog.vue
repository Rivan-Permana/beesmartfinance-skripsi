<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Message from "primevue/message"
import Textarea from "primevue/textarea"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { calendarTextMatches, formatRp } from "@/core/format"
import type { Kegiatan } from "@/types/api"
import { realisasiValid, type RealisasiForm } from "./presentation"
const props=defineProps<{target:Kegiatan|null;saving?:boolean;error?:string}>()
const visible=defineModel<boolean>({default:false})
const form=defineModel<RealisasiForm>("form",{required:true})
const emit=defineEmits<{save:[];report:[]}>()
const attempted=ref(false)
const dateInputInvalid=ref(false)
const element=ref<HTMLFormElement|null>(null)
const errorElement=ref<HTMLElement|null>(null)
const invalidAmount=computed(()=>!Number.isFinite(form.value.nominal)||form.value.nominal<=0||form.value.nominal>Number(props.target?.sisa_pagu??0))
const invalidDate=computed(()=>dateInputInvalid.value||!form.value.tanggal||!Number.isFinite(form.value.tanggal.getTime()))
watch(visible,open=>{if(open){attempted.value=false;dateInputInvalid.value=false}})
watch(()=>props.error,async value=>{if(value){await nextTick();errorElement.value?.focus()}})
async function submit(){if(props.saving)return;attempted.value=true;if(invalidDate.value||!realisasiValid(form.value,props.target)){await nextTick();element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();return}emit("save")}
function checkDateInput(event:Event){if(event.target instanceof HTMLInputElement)dateInputInvalid.value=!calendarTextMatches(event.target.value,form.value.tanggal)}
</script>
<template>
  <Dialog v-model:visible="visible" header="Catat realisasi" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :style="{width:'540px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form realisasi'}"><template #closeicon><Icon name="x" /></template>
    <div v-if="target" class="realisasi-context"><strong>{{ target.nama }}</strong><span>Sisa pagu <strong>{{ formatRp(target.sisa_pagu) }}</strong></span></div><p class="realisasi-intro">Catat penggunaan anggaran sesuai pengeluaran kegiatan. Nominal maksimal mengikuti sisa pagu.</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="realisasi-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Periksa laporan sebelum mengirim ulang.</Message><Button label="Periksa laporan kegiatan" severity="secondary" @click="emit('report')" /></div>
    <form id="realisasi-form" ref="element" novalidate :aria-busy="saving" @submit.prevent="submit"><fieldset :disabled="saving" class="realisasi-fields">
      <div class="realisasi-field"><label for="realisasi-date">Tanggal pengeluaran</label><DatePicker :key="saving ? 'locked' : 'editable'" input-id="realisasi-date" v-model="form.tanggal" @input="checkDateInput" @update:model-value="dateInputInvalid=false" date-format="dd/mm/yy" :disabled="saving" :invalid="attempted&&invalidDate" :input-props="{'aria-invalid':attempted&&invalidDate,'aria-describedby':attempted&&invalidDate?'realisasi-date-error':undefined}" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted&&invalidDate" id="realisasi-date-error" class="realisasi-error">Periksa atau pilih ulang tanggal pengeluaran.</small></div>
      <div class="realisasi-field"><label for="realisasi-amount">Nominal realisasi <span>(Rp)</span></label><InputNumber input-id="realisasi-amount" :model-value="form.nominal" @update:model-value="form.nominal=$event??0" :min="0" :max-fraction-digits="2" locale="id-ID" :invalid="attempted&&invalidAmount" :input-props="{autofocus:true,'aria-invalid':attempted&&invalidAmount,'aria-describedby':attempted&&invalidAmount?'realisasi-amount-error':undefined}" fluid /><small v-if="attempted&&invalidAmount" id="realisasi-amount-error" class="realisasi-error">Isi nominal lebih dari nol, maksimal {{ formatRp(target?.sisa_pagu) }}.</small></div>
      <div class="realisasi-field"><label for="realisasi-description">Keterangan <span>(opsional)</span></label><Textarea id="realisasi-description" v-model="form.deskripsi" rows="3" auto-resize placeholder="Contoh: Pembelian buku untuk pekan membaca" fluid /></div>
    </fieldset></form>
    <template #footer><Button label="Batal" severity="secondary" :disabled="saving" @click="visible=false" /><Button label="Catat realisasi" type="submit" form="realisasi-form" :loading="saving"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
<style scoped>
.realisasi-context { display: grid; gap: var(--bee-space-2); padding-bottom: var(--bee-space-4); border-bottom: 1px solid var(--app-border); }.realisasi-context > strong { font-weight: 500; font-size: var(--bee-type-body); }.realisasi-context span { display: flex; justify-content: space-between; gap: var(--bee-space-3); color: var(--app-text-muted); }.realisasi-context span strong { color: var(--app-text); font-weight: 500; font-variant-numeric: tabular-nums; }.realisasi-intro { color: var(--app-text-muted); margin: var(--bee-space-4) 0 var(--bee-space-5); }.realisasi-notice { display: grid; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); }.realisasi-fields { border: 0; margin: 0; padding: 0; min-width: 0; display: grid; gap: var(--bee-space-5); }.realisasi-field { display: flex; flex-direction: column; gap: var(--bee-space-2); min-width: 0; }.realisasi-field label { font-weight: 500; }.realisasi-field label span { color: var(--app-text-muted); font-weight: 400; }.realisasi-error { color: var(--bee-color-critical); font-size: var(--bee-type-caption); }
</style>
