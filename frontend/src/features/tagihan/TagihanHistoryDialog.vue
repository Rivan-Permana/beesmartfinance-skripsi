<script setup lang="ts">
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { PembayaranTagihan, Tagihan } from "@/types/api"
import { paymentCancelled, perluDicocokkan, tagihanPeriod } from "./presentation"
const target = defineModel<Tagihan | null>("target", {default:null})
defineProps<{ studentName?: string }>()
const emit = defineEmits<{ receipt: [payment: PembayaranTagihan] }>()
</script>

<template>
  <Dialog :visible="!!target" @update:visible="value => { if (!value) target = null }" header="Riwayat pembayaran" modal :draggable="false" :style="{width:'680px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup riwayat pembayaran'}">
    <template #closeicon><Icon name="x" /></template>
    <template v-if="target">
      <div class="history-context"><strong>{{ studentName || target.siswa_nama || 'Siswa' }}</strong><p>{{ tagihanPeriod(target) }}</p></div>
      <Message v-if="perluDicocokkan(target)" severity="warn" :closable="false" class="history-notice"><template #icon><Icon name="warning-circle" /></template>Pembayaran lama perlu dicocokkan dengan bukti penerimaan. Daftar ini belum mewakili nominal pembayaran lama tersebut.</Message>
      <div v-if="!target.pembayaran.length" class="history-empty"><Icon name="clock" /><h3>Belum ada pembayaran tercatat di daftar ini</h3><p>Periksa bukti penerimaan jika pembayaran sebelumnya belum dicocokkan.</p></div>
      <ol v-else class="history-records"><li v-for="payment in target.pembayaran" :key="payment.id"><div class="history-heading"><div><strong>{{ payment.no_bukti }}</strong><small>{{ payment.tanggal.split('-').reverse().join('/') }}</small></div><strong class="tabular-nums">{{ formatRp(payment.nominal) }}</strong></div><Tag :value="payment.dibatalkan || payment.jurnal_status === 'VOID' ? 'Dibatalkan' : payment.jurnal_status === 'POSTED' ? 'Sudah dicatat' : 'Menunggu pencatatan keuangan'" :severity="payment.dibatalkan || payment.jurnal_status === 'VOID' ? 'danger' : payment.jurnal_status === 'POSTED' ? 'success' : 'info'" /><Button v-if="!paymentCancelled(payment)" label="Kwitansi" severity="secondary" size="small" class="history-receipt" :aria-label="`Lihat kwitansi ${payment.no_bukti}`" @click="emit('receipt', payment)"><template #icon><Icon name="file-text" /></template></Button><p v-if="payment.dibatalkan" class="history-reason">Alasan pembatalan: {{ payment.alasan_batal }}</p><dl><div v-for="line in payment.alokasi" :key="line.detail"><dt>{{ target.detail.find(item => item.id === line.detail)?.keterangan || target.detail.find(item => item.id === line.detail)?.komponen || 'Komponen tagihan' }}</dt><dd>{{ formatRp(line.nominal) }}</dd></div></dl></li></ol>
    </template>
    <template #footer><Button label="Tutup" severity="secondary" @click="target = null" /></template>
  </Dialog>
</template>

<style scoped>
.history-context strong { font-weight: 500; font-size: var(--bee-type-body); }.history-context p { margin: var(--bee-space-1) 0 var(--bee-space-5); color: var(--app-text-muted); }.history-notice { margin-bottom: var(--bee-space-5); }
.history-records { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--bee-space-5); }.history-records li { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-5); }.history-heading { display: flex; justify-content: space-between; align-items: baseline; gap: var(--bee-space-4); margin-bottom: var(--bee-space-3); overflow-wrap: anywhere; }.history-heading > div { min-width: 0; }.history-heading strong { font-weight: 500; }.history-heading small { display: block; margin-top: var(--bee-space-1); color: var(--app-text-muted); }.history-records dl { margin: var(--bee-space-4) 0 0; display: grid; gap: var(--bee-space-2); }.history-records dl > div { display: flex; gap: var(--bee-space-4); justify-content: space-between; }.history-records dt { color: var(--app-text-muted); }.history-records dd { margin: 0; font-variant-numeric: tabular-nums; text-align: right; }.history-receipt { margin-left: var(--bee-space-3); }.history-reason { color: var(--bee-color-critical); font-size: var(--bee-type-caption); }
.history-empty { display: grid; justify-items: center; text-align: center; padding: var(--bee-space-6) 0; }.history-empty > .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); margin-bottom: var(--bee-space-4); }.history-empty h3 { font-size: var(--bee-type-section); font-weight: 500; }.history-empty p { color: var(--app-text-muted); max-width: 42ch; margin-bottom: 0; }
@media(max-width:520px) { .history-heading { flex-direction: column; gap: var(--bee-space-2); } }
</style>
