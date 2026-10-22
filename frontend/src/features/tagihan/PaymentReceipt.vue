<script setup lang="ts">
import { computed } from "vue"
import { formatRp } from "@/core/format"
import type { PembayaranTagihan, StrukTagihan, Tagihan } from "@/types/api"
import { paymentCancelled, receiptLines } from "./presentation"

const props = defineProps<{ invoice: StrukTagihan; tagihan: Tagihan; payment: PembayaranTagihan; cashAccount?: string }>()
const lines = computed(() => receiptLines(props.tagihan, props.payment))
const cancelled = computed(() => paymentCancelled(props.payment))
</script>

<template>
  <div class="receipt">
    <header class="receipt__head">
      <img src="/logo-lebah.svg" alt="" width="48" height="48" />
      <div><h2>{{ invoice.sekolah ?? "RA Lebah Madu" }}</h2><p>Kwitansi pembayaran</p></div>
    </header>
    <p v-if="cancelled" class="receipt__void" role="note">Dibatalkan — kwitansi ini tidak berlaku. {{ payment.alasan_batal }}</p>
    <div class="receipt__meta">
      <div><strong>{{ invoice.siswa }}</strong><div class="muted">NIS: {{ invoice.nis ?? "-" }}</div><div v-if="invoice.kelompok" class="muted">{{ invoice.kelompok }}</div></div>
      <dl>
        <div><dt>No. kwitansi</dt><dd>{{ payment.no_bukti }}</dd></div>
        <div><dt>Tanggal</dt><dd>{{ payment.tanggal.split("-").reverse().join("/") }}</dd></div>
        <div><dt>Tagihan</dt><dd>No. {{ invoice.no_tagihan }} · {{ invoice.periode }}</dd></div>
        <div><dt>Diterima di</dt><dd>{{ cashAccount || `Akun ${payment.akun_kas}` }}</dd></div>
      </dl>
    </div>
    <table class="receipt__table">
      <caption class="muted">Untuk pembayaran</caption>
      <tbody><tr v-for="line in lines" :key="line.detail"><td>{{ line.label }}</td><td class="num">{{ formatRp(line.nominal) }}</td></tr></tbody>
    </table>
    <div class="receipt__total"><span>Jumlah diterima</span><strong>{{ formatRp(payment.nominal) }}</strong></div>
    <p v-if="!tagihan.perlu_rekonsiliasi" class="muted">Sisa tagihan saat kwitansi dicetak: {{ formatRp(tagihan.sisa_tagihan ?? tagihan.total) }}</p>
    <footer class="receipt__sign"><span>Penerima,</span><span class="receipt__line" aria-hidden="true"></span><span class="muted">Tata Usaha</span></footer>
  </div>
</template>

<style scoped>
.receipt { font-size: 0.9rem; line-height: 1.45; color: var(--app-text); }
.receipt__head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 2px solid var(--app-primary, #2e2a6e); }
.receipt__head img { flex-shrink: 0; }
.receipt__head h2 { margin: 0; font-family: var(--app-font-display, inherit); font-size: 1.15rem; color: var(--app-primary, #2e2a6e); }
.receipt__head p { margin: 0.15rem 0 0; font-size: 0.8rem; color: var(--app-text-muted); }
.receipt__void { margin: 0 0 1rem; padding: 0.5rem 0.75rem; border: 1px solid var(--bee-color-critical); color: var(--bee-color-critical); font-weight: 600; }
.receipt__meta { display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.receipt__meta dl { margin: 0; display: grid; gap: 0.15rem; font-size: 0.85rem; text-align: right; }
.receipt__meta dl > div { display: flex; justify-content: flex-end; gap: 0.5rem; }
.receipt__meta dt { color: var(--app-text-muted); }
.receipt__meta dd { margin: 0; overflow-wrap: anywhere; }
.muted { color: var(--app-text-muted); font-size: 0.8rem; }
.receipt__table { width: 100%; border-collapse: collapse; }
.receipt__table caption { text-align: left; text-transform: uppercase; letter-spacing: 0.04em; font-size: 0.75rem; margin-bottom: 0.35rem; }
.receipt__table td { padding: 0.3rem 0; border-bottom: 1px dashed var(--app-border); }
.receipt__table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.receipt__total { display: flex; justify-content: space-between; align-items: center; margin: 0.75rem 0; padding-top: 0.75rem; border-top: 2px solid var(--app-border); font-size: 1rem; font-variant-numeric: tabular-nums; }
.receipt__sign { display: grid; justify-items: end; gap: 0.25rem; margin-top: 2rem; }
.receipt__line { width: 12rem; height: 3rem; border-bottom: 1px solid var(--app-text); }
@media (max-width: 520px) { .receipt__meta { flex-direction: column; } .receipt__meta dl { text-align: left; } .receipt__meta dl > div { justify-content: flex-start; } }
@media print { .receipt__head, .receipt__meta, .receipt__table tr, .receipt__total, .receipt__sign { break-inside: avoid; } }
</style>
