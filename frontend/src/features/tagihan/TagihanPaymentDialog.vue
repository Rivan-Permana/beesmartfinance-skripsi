<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { calendarTextMatches, formatRp } from "@/core/format"
import type { Coa, Tagihan } from "@/types/api"
import { paymentTotal, paymentValid, type TagihanPaymentForm } from "./payment"
import { tagihanPeriod } from "./presentation"

const props = defineProps<{ target: Tagihan | null; studentName: string; accounts: Coa[]; saving?: boolean; error?: string }>()
const visible = defineModel<boolean>({default:false})
const form = defineModel<TagihanPaymentForm>("form", {required:true})
const emit = defineEmits<{ save: []; reloadAccounts: [] }>()
const attempted = ref(false)
const dateInputInvalid = ref(false)
const formElement = ref<HTMLFormElement | null>(null)
const errorElement = ref<HTMLElement | null>(null)
const total = computed(() => paymentTotal(form.value))
const allocationInvalid = computed(() => !Number.isFinite(total.value) || total.value <= 0 || form.value.alokasi.some(line => !Number.isFinite(line.nominal) || line.nominal < 0 || line.nominal > line.sisa))
const dateInvalid = computed(() => dateInputInvalid.value || !form.value.tanggal || !Number.isFinite(form.value.tanggal.getTime()))
watch(visible, open => { if (open) { attempted.value = false; dateInputInvalid.value = false } })
watch(() => props.error, async (message) => { if (message) { await nextTick(); errorElement.value?.focus() } })
async function submit() {
  if (props.saving) return
  attempted.value = true
  if (dateInvalid.value || !paymentValid(form.value)) {
    await nextTick()
    formElement.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
    return
  }
  emit("save")
}
function checkDateInput(event: Event) {
  if (event.target instanceof HTMLInputElement) dateInputInvalid.value = !calendarTextMatches(event.target.value, form.value.tanggal)
}
function fillRemaining() { form.value.alokasi.forEach(line => { line.nominal = line.sisa }) }
</script>

<template>
  <Dialog v-model:visible="visible" header="Catat pembayaran" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :style="{width:'680px'}" class="tagihan-payment-dialog" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form pembayaran'}">
    <template #closeicon><Icon name="x" /></template>
    <div v-if="target" class="payment-context"><div><strong>{{ studentName }}</strong><p>{{ tagihanPeriod(target) }}</p></div><div><span>Sisa tagihan</span><strong>{{ target.sisa_tagihan === null ? 'Belum diketahui' : formatRp(target.sisa_tagihan) }}</strong></div></div>
    <p class="payment-intro">Catat pembayaran penuh atau sebagian sesuai bukti penerimaan.</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="payment-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Input tetap ada; periksa sebelum mencoba ulang.</Message></div>
    <div v-if="!accounts.length" class="payment-notice"><Message severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>Akun Kas/Bank penerima belum tersedia. Muat ulang atau hubungi staf keuangan.</Message><Button label="Muat ulang akun" severity="secondary" @click="emit('reloadAccounts')" /></div>
    <form id="tagihan-payment-form" ref="formElement" :aria-busy="saving" novalidate @submit.prevent="submit">
      <fieldset :disabled="saving" class="payment-section"><legend>Bukti penerimaan</legend><div class="payment-fields">
        <div class="payment-field"><label for="tanggal-bayar">Tanggal pembayaran</label><DatePicker :key="saving ? 'locked' : 'editable'" :disabled="saving" input-id="tanggal-bayar" v-model="form.tanggal" @input="checkDateInput" @update:model-value="dateInputInvalid=false" date-format="dd/mm/yy" :invalid="attempted && dateInvalid" :input-props="{'aria-invalid':attempted && dateInvalid,'aria-describedby':attempted && dateInvalid ? 'tanggal-bayar-error' : undefined}" fluid ><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template><template #dropdownicon><Icon name="calendar-blank" /></template></DatePicker><small v-if="attempted && dateInvalid" id="tanggal-bayar-error" class="payment-field-error">Periksa atau pilih ulang tanggal pembayaran.</small></div>
        <div class="payment-field"><label for="bukti-bayar">Nomor bukti penerimaan</label><InputText id="bukti-bayar" v-model="form.no_bukti" autofocus maxlength="100" :invalid="attempted && !form.no_bukti.trim()" :aria-invalid="attempted && !form.no_bukti.trim()" :aria-describedby="attempted && !form.no_bukti.trim() ? 'bukti-bayar-error' : 'bukti-bayar-help'" fluid /><small v-if="attempted && !form.no_bukti.trim()" id="bukti-bayar-error" class="payment-field-error">Isi nomor bukti penerimaan.</small><small v-else id="bukti-bayar-help">Gunakan nomor pada bukti.</small></div>
        <div class="payment-field payment-field-full"><label for="kas-bayar">Kas/Bank penerima</label><Select :key="(saving || !accounts.length) ? 'locked' : 'editable'" input-id="kas-bayar" v-model="form.akun_kas" :options="accounts" option-label="nama_akun" option-value="kode_akun" placeholder="Pilih Kas/Bank penerima" :disabled="saving || !accounts.length" :invalid="attempted && !form.akun_kas" :aria-invalid="attempted && !form.akun_kas" :aria-describedby="attempted && !form.akun_kas ? 'kas-bayar-error' : undefined" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select><small v-if="attempted && !form.akun_kas" id="kas-bayar-error" class="payment-field-error">Pilih akun yang menerima pembayaran.</small></div>
      </div></fieldset>
      <fieldset :disabled="saving" class="payment-section"><legend>Alokasi pembayaran</legend><p class="payment-help">Isi nominal pada komponen yang dibayar. Nominal tidak boleh melebihi sisanya.</p><Button label="Isi seluruh sisa" severity="secondary" text :disabled="saving" @click="fillRemaining"><template #icon><Icon name="check" /></template></Button>
        <div class="payment-allocations"><div v-for="line in form.alokasi" :key="line.detail" class="payment-allocation"><div><label :for="`bayar-komponen-${line.detail}`">{{ line.label }}</label><small>Sisa {{ formatRp(line.sisa) }}</small></div><div class="payment-allocation-input"><InputNumber :input-id="`bayar-komponen-${line.detail}`" :model-value="line.nominal" @update:model-value="line.nominal = $event ?? 0" prefix="Rp " locale="id-ID" :min="0" :max="line.sisa" :max-fraction-digits="2" :invalid="attempted && allocationInvalid" :input-props="{'aria-invalid':attempted && allocationInvalid,'aria-describedby':attempted && allocationInvalid ? 'payment-allocation-error' : undefined}" fluid /></div></div></div>
        <p v-if="attempted && allocationInvalid" id="payment-allocation-error" class="payment-field-error" role="alert">Isi pembayaran lebih dari nol pada minimal satu komponen, tanpa melebihi sisanya.</p>
      </fieldset>
    </form>
    <template #footer><div class="payment-total"><span>Pembayaran ini</span><strong>{{ formatRp(total) }}</strong></div><div class="payment-footer-actions"><span v-if="saving" class="payment-saving" role="status">Menyimpan pembayaran…</span><Button label="Batal" severity="secondary" :disabled="saving" @click="visible = false" /><Button label="Simpan pembayaran" type="submit" form="tagihan-payment-form" :disabled="!accounts.length || !form.alokasi.length" :loading="saving" :aria-busy="saving"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div></template>
  </Dialog>
</template>

<style scoped>
.payment-context { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--bee-space-4); padding-bottom: var(--bee-space-5); border-bottom: 1px solid var(--app-border); }.payment-context strong { display: block; font-weight: 500; font-size: var(--bee-type-body); }.payment-context p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); }.payment-context > div:last-child { text-align: right; }.payment-context span { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.payment-context > div:last-child strong { font-variant-numeric: tabular-nums; }
.payment-intro { color: var(--app-text-muted); margin: var(--bee-space-4) 0 var(--bee-space-5); }.payment-notice { display: grid; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); }
.payment-section { border: 0; padding: 0; margin: 0 0 var(--bee-space-5); min-width: 0; }.payment-section legend { font-size: var(--bee-type-body); font-weight: 500; margin-bottom: var(--bee-space-4); }.payment-fields { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: var(--bee-space-5) var(--bee-space-4); }.payment-field { display: flex; flex-direction: column; gap: var(--bee-space-2); min-width: 0; }.payment-field-full { grid-column: 1/-1; }.payment-field label { font-weight: 500; }.payment-field small,.payment-help { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.payment-help { margin: 0 0 var(--bee-space-2); }
.payment-allocations { border-top: 1px solid var(--app-border); margin-top: var(--bee-space-2); }.payment-allocation { display: flex; justify-content: space-between; align-items: center; gap: var(--bee-space-4); padding-block: var(--bee-space-4); border-bottom: 1px solid var(--app-border); }.payment-allocation label { font-weight: 500; }.payment-allocation small { display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-top: var(--bee-space-1); }.payment-allocation-input { width: 200px; flex-shrink: 0; }.payment-allocation-input :deep(input) { text-align: right; font-variant-numeric: tabular-nums; }
.payment-footer-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--bee-space-2); margin-top: var(--bee-space-4); }
.payment-total { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: var(--bee-space-3); padding: var(--bee-space-4); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); }.payment-total strong { font-size: var(--bee-type-number-secondary); font-weight: 500; font-variant-numeric: tabular-nums; }
.payment-field-error,.payment-field small.payment-field-error { color: var(--bee-color-critical); font-size: var(--bee-type-caption); }.payment-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media(max-width:520px) { .payment-fields { grid-template-columns: minmax(0,1fr); }.payment-allocation { flex-wrap: wrap; gap: var(--bee-space-2); }.payment-allocation-input { width: 100%; }.payment-context > div:last-child { text-align: left; }.payment-total strong { font-size: var(--bee-type-subheading); } }
</style>

<style>
.tagihan-payment-dialog .p-dialog-footer { display: block; }
@media(max-width:520px) {
  .tagihan-payment-dialog .payment-footer-actions { display: grid; grid-template-columns: auto minmax(0,1fr); }
  .tagihan-payment-dialog .payment-footer-actions > .p-button { min-width: 0; }
  .tagihan-payment-dialog .payment-footer-actions .p-button-label { white-space: normal; }
  .tagihan-payment-dialog .payment-saving { grid-column: 1/-1; }
}
</style>
