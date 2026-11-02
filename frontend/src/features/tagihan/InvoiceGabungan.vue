<script setup lang="ts">
import { formatRp } from "@/core/format"
import type { InvoiceGabungan } from "@/types/api"
import { formatTanggalPanjang, invoiceLineLabel } from "./invoiceGabungan"

defineProps<{ invoice: InvoiceGabungan }>()
</script>

<template>
  <div class="invoice">
    <header class="invoice__head">
      <img src="/logo-lebah.svg" alt="" class="invoice__logo" width="48" height="48" />
      <div>
        <h2 class="invoice__school">{{ invoice.sekolah }}</h2>
        <p class="invoice__tagline">Rincian tagihan siswa</p>
      </div>
    </header>

    <div class="invoice__meta">
      <div>
        <strong>{{ invoice.siswa }}</strong>
        <div class="muted">NIS: {{ invoice.nis ?? "-" }}</div>
        <div v-if="invoice.kelompok" class="muted">{{ invoice.kelompok }}</div>
      </div>
      <div class="invoice__meta-right">Per {{ formatTanggalPanjang(invoice.tanggal) }}</div>
    </div>

    <p v-if="!invoice.sections.length" class="invoice__empty">Tidak ada tagihan yang belum dibayar.</p>
    <div v-for="sec in invoice.sections" :key="sec.kategori" class="invoice__section">
      <h3 class="invoice__section-title">{{ sec.label }}</h3>
      <table class="invoice__table">
        <tbody>
          <tr v-for="(line, i) in sec.lines" :key="`${sec.kategori}-${i}`">
            <td>{{ invoiceLineLabel(line, sec.kategori) }}</td>
            <td class="num">{{ formatRp(line.nominal) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="invoice__total">
      <span>Total yang perlu dibayar</span>
      <strong>{{ formatRp(invoice.total) }}</strong>
    </div>
    <p v-if="invoice.catatan" class="invoice__note">{{ invoice.catatan }}</p>

    <section v-if="invoice.rekening || invoice.kontak" class="invoice__pay" aria-label="Cara pembayaran">
      <div v-if="invoice.rekening"><span class="muted">Transfer ke</span><strong>{{ [invoice.rekening.bank, invoice.rekening.nomor].filter(Boolean).join(" ") }}</strong><span v-if="invoice.rekening.atas_nama">a.n. {{ invoice.rekening.atas_nama }}</span></div>
      <div v-if="invoice.kontak"><span class="muted">Konfirmasi pembayaran</span><strong>{{ invoice.kontak.nama || "-" }}</strong><span v-if="invoice.kontak.wa">{{ invoice.kontak.wa }}</span></div>
    </section>
  </div>
</template>

<style scoped>
.invoice { font-size: 0.9rem; line-height: 1.45; color: var(--app-text); }
.invoice__head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 2px solid var(--app-primary, #2e2a6e); }
.invoice__logo { flex-shrink: 0; }
.invoice__school { margin: 0; font-family: var(--app-font-display, inherit); font-size: 1.15rem; color: var(--app-primary, #2e2a6e); }
.invoice__tagline { margin: 0.15rem 0 0; font-size: 0.8rem; color: var(--app-text-muted); }
.invoice__meta { display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.invoice__meta-right { text-align: right; font-size: 0.85rem; }
.muted { color: var(--app-text-muted); font-size: 0.8rem; }
.invoice__empty { color: var(--app-text-muted); }
.invoice__section { margin-bottom: 0.75rem; }
.invoice__section-title { margin: 0 0 0.35rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--app-text-muted); }
.invoice__table { width: 100%; border-collapse: collapse; }
.invoice__table td { padding: 0.3rem 0; border-bottom: 1px dashed var(--app-border); overflow-wrap: anywhere; }
.invoice__table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; padding-left: 0.75rem; }
.invoice__total { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 2px solid var(--app-border); font-size: 1rem; }
.invoice__total strong { font-variant-numeric: tabular-nums; white-space: nowrap; }
.invoice__note { margin: 0.5rem 0 0; font-size: 0.85rem; }
.invoice__pay { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 1rem; padding: 0.75rem; border: 1px solid var(--app-border); border-radius: 8px; }
.invoice__pay > div { display: grid; gap: 0.1rem; min-width: 0; overflow-wrap: anywhere; }
@media print {
  .invoice__head, .invoice__meta, .invoice__table tr, .invoice__total, .invoice__pay { break-inside: avoid; }
}
</style>
