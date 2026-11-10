<script setup lang="ts">
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Textarea from "primevue/textarea"
import { ref, watch } from "vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { PembayaranTagihan, Tagihan } from "@/types/api"
import { bisaBatalSaldoAwal, paymentCancelled, paymentState, perluDicocokkan, tagihanPeriod } from "./presentation"
const target = defineModel<Tagihan | null>("target", {default:null})
defineProps<{ studentName?: string; cancelling?: boolean; cancelError?: string }>()
const emit = defineEmits<{ receipt: [payment: PembayaranTagihan]; cancelOpening: [payment: PembayaranTagihan, alasan: string] }>()

// Form alasan pembatalan saldo awal, satu penerimaan pada satu waktu.
const batalId = ref<number | null>(null)
const alasan = ref("")
watch(() => target.value?.id, () => { batalId.value = null; alasan.value = "" })
watch(() => target.value?.pembayaran, (rows) => { if (rows?.some(p => p.id === batalId.value && p.dibatalkan)) batalId.value = null })
function mulaiBatal(payment: PembayaranTagihan) { batalId.value = payment.id; alasan.value = "" }
function kirimBatal(payment: PembayaranTagihan) { if (alasan.value.trim()) emit("cancelOpening", payment, alasan.value.trim()) }
</script>

<template>
  <Dialog :visible="!!target" @update:visible="value => { if (!value) target = null }" header="Riwayat pembayaran" modal :draggable="false" :style="{width:'680px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup riwayat pembayaran'}">
    <template #closeicon><Icon name="x" /></template>
    <template v-if="target">
      <div class="history-context"><strong>{{ studentName || target.siswa_nama || 'Siswa' }}</strong><p>{{ tagihanPeriod(target) }}</p></div>
      <Message v-if="perluDicocokkan(target)" severity="warn" :closable="false" class="history-notice"><template #icon><Icon name="warning-circle" /></template>Pembayaran lama perlu dicocokkan dengan bukti penerimaan. Daftar ini belum mewakili nominal pembayaran lama tersebut.</Message>
      <div v-if="!target.pembayaran.length" class="history-empty"><Icon name="clock" /><h3>Belum ada pembayaran tercatat di daftar ini</h3><p>Periksa bukti penerimaan jika pembayaran sebelumnya belum dicocokkan.</p></div>
      <ol v-else class="history-records">
        <li v-for="payment in target.pembayaran" :key="payment.id">
          <div class="history-heading"><div><strong>{{ payment.no_bukti }}</strong><small>{{ payment.tanggal.split('-').reverse().join('/') }}</small></div><strong class="tabular-nums">{{ formatRp(payment.nominal) }}</strong></div>
          <Tag :value="paymentState(payment).label" :severity="paymentState(payment).severity" />
          <Button v-if="!paymentCancelled(payment) && !payment.saldo_awal" label="Kwitansi" severity="secondary" size="small" class="history-receipt" :aria-label="`Lihat kwitansi ${payment.no_bukti}`" @click="emit('receipt', payment)"><template #icon><Icon name="file-text" /></template></Button>
          <Button v-if="bisaBatalSaldoAwal(payment) && batalId !== payment.id" label="Batalkan saldo awal" severity="danger" text size="small" class="history-receipt" :aria-label="`Batalkan saldo awal ${payment.no_bukti}`" @click="mulaiBatal(payment)" />
          <p v-if="payment.dibatalkan" class="history-reason">Alasan pembatalan: {{ payment.alasan_batal }}</p>
          <form v-if="batalId === payment.id" class="history-cancel" @submit.prevent="kirimBatal(payment)">
            <label :for="`batal-alasan-${payment.id}`">Alasan pembatalan (wajib)</label>
            <Textarea :id="`batal-alasan-${payment.id}`" v-model="alasan" rows="2" auto-resize :disabled="cancelling" :aria-describedby="`batal-bantu-${payment.id}`" fluid />
            <small :id="`batal-bantu-${payment.id}`">Untuk penerimaan saldo awal yang salah impor. Tidak ada jurnal yang berubah; sisa tagihan kembali bertambah dan tagihan bisa dibayar ulang.</small>
            <Message v-if="cancelError" severity="error" :closable="false">{{ cancelError }}</Message>
            <div class="history-cancel-actions"><Button type="button" label="Kembali" severity="secondary" text :disabled="cancelling" @click="batalId = null" /><Button type="submit" label="Batalkan penerimaan" severity="danger" :loading="cancelling" :disabled="!alasan.trim()" /></div>
          </form>
          <dl><div v-for="line in payment.alokasi" :key="line.detail"><dt>{{ target.detail.find(item => item.id === line.detail)?.keterangan || target.detail.find(item => item.id === line.detail)?.komponen || 'Komponen tagihan' }}</dt><dd>{{ formatRp(line.nominal) }}</dd></div></dl>
        </li>
      </ol>
    </template>
    <template #footer><Button label="Tutup" severity="secondary" @click="target = null" /></template>
  </Dialog>
</template>

<style scoped>
.history-context strong { font-weight: 500; font-size: var(--bee-type-body); }.history-context p { margin: var(--bee-space-1) 0 var(--bee-space-5); color: var(--app-text-muted); }.history-notice { margin-bottom: var(--bee-space-5); }
.history-records { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--bee-space-5); }.history-records li { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-5); }.history-heading { display: flex; justify-content: space-between; align-items: baseline; gap: var(--bee-space-4); margin-bottom: var(--bee-space-3); overflow-wrap: anywhere; }.history-heading > div { min-width: 0; }.history-heading strong { font-weight: 500; }.history-heading small { display: block; margin-top: var(--bee-space-1); color: var(--app-text-muted); }.history-records dl { margin: var(--bee-space-4) 0 0; display: grid; gap: var(--bee-space-2); }.history-records dl > div { display: flex; gap: var(--bee-space-4); justify-content: space-between; }.history-records dt { color: var(--app-text-muted); }.history-records dd { margin: 0; font-variant-numeric: tabular-nums; text-align: right; }.history-receipt { margin-left: var(--bee-space-3); }.history-reason { color: var(--bee-color-critical); font-size: var(--bee-type-caption); }
.history-cancel { display: grid; gap: var(--bee-space-2); margin-top: var(--bee-space-4); padding: var(--bee-space-4); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }.history-cancel label { font-size: var(--bee-type-caption); font-weight: 600; }.history-cancel small { color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.5; }.history-cancel-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--bee-space-2); }
.history-empty { display: grid; justify-items: center; text-align: center; padding: var(--bee-space-6) 0; }.history-empty > .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); margin-bottom: var(--bee-space-4); }.history-empty h3 { font-size: var(--bee-type-section); font-weight: 500; }.history-empty p { color: var(--app-text-muted); max-width: 42ch; margin-bottom: 0; }
@media(max-width:520px) { .history-heading { flex-direction: column; gap: var(--bee-space-2); } }
</style>
