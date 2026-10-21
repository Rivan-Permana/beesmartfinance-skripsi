<script setup lang="ts">
import Tag from "primevue/tag"
import { computed } from "vue"

import { TAGIHAN_STATUS, perluDicocokkan } from "./presentation"
import { formatRp } from "@/core/format"
import type { StrukTagihan, TagihanKategori } from "@/types/api"

const props = defineProps<{
  invoice: StrukTagihan
  printable?: boolean
}>()

const sections = computed(() => {
  if (props.invoice.sections?.length) return props.invoice.sections
  const grouped = new Map<TagihanKategori, typeof props.invoice.rincian>()
  for (const line of props.invoice.rincian) {
    const kat: TagihanKategori =
      line.komponen === "SPP" || line.komponen === "KATERING" || line.komponen === "JEMPUTAN"
        ? "BULANAN"
        : "LAIN"
    if (!grouped.has(kat)) grouped.set(kat, [])
    grouped.get(kat)!.push(line)
  }
  const labels: Record<TagihanKategori, string> = {
    BULANAN: "Biaya Bulanan",
    TAHUNAN: "Biaya Tahunan",
    LAIN: "Lain-lain",
  }
  return (["TAHUNAN", "BULANAN", "LAIN"] as TagihanKategori[])
    .filter((k) => grouped.has(k))
    .map((k) => ({
      kategori: k,
      label: labels[k],
      lines: grouped.get(k)!,
    }))
})
</script>

<template>
  <div class="invoice" :class="{ 'invoice--print': printable }">
    <header class="invoice__head">
      <img src="/logo-lebah.svg" alt="" class="invoice__logo" width="48" height="48" />
      <div>
        <h2 class="invoice__school">{{ invoice.sekolah ?? "RA Lebah Madu" }}</h2>
        <p class="invoice__tagline">Faktur tagihan siswa</p>
      </div>
    </header>

    <div class="invoice__meta">
      <div>
        <strong>{{ invoice.siswa }}</strong>
        <div class="muted">NIS: {{ invoice.nis ?? "-" }}</div>
        <div v-if="invoice.kelompok" class="muted">{{ invoice.kelompok }}</div>
      </div>
      <div class="invoice__meta-right">
        <div>No. {{ invoice.no_tagihan }}</div>
        <div>Periode {{ invoice.periode }}</div>
      </div>
    </div>

    <div v-for="sec in sections" :key="sec.kategori" class="invoice__section">
      <h3 class="invoice__section-title">{{ sec.label }}</h3>
      <table class="invoice__table">
        <tbody>
          <tr v-for="(line, i) in sec.lines" :key="`${sec.kategori}-${i}`">
            <td>{{ line.label ?? line.komponen }}</td>
            <td class="num">{{ formatRp(line.nominal) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="invoice__total">
      <span>Total tagihan</span>
      <strong>{{ formatRp(invoice.total) }}</strong>
    </div>

    <footer class="invoice__foot">
      <Tag :value="perluDicocokkan(invoice) ? 'Perlu dicocokkan' : TAGIHAN_STATUS[invoice.status].label" :severity="perluDicocokkan(invoice) ? 'warn' : TAGIHAN_STATUS[invoice.status].severity" />
      <span v-if="invoice.no_jurnal" class="muted">
        Jurnal: {{ invoice.no_jurnal.slice(0, 8) }}…
      </span>
    </footer>
    <p v-if="perluDicocokkan(invoice)" class="muted">Nominal pembayaran lama perlu dicocokkan dengan bukti penerimaan.</p>
    <div v-else class="invoice__total">
      <span>Dibayar: {{ formatRp(invoice.total_terbayar ?? 0) }}</span>
      <strong>Sisa: {{ formatRp(invoice.sisa_tagihan ?? invoice.total) }}</strong>
    </div>
  </div>
</template>

<style scoped>
.invoice {
  font-size: 0.9rem;
  line-height: 1.45;
  color: var(--app-text);
}
.invoice__head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid var(--app-primary, #2e2a6e);
}
.invoice__logo {
  flex-shrink: 0;
}
.invoice__school {
  margin: 0;
  font-family: var(--app-font-display, inherit);
  font-size: 1.15rem;
  color: var(--app-primary, #2e2a6e);
}
.invoice__tagline {
  margin: 0.15rem 0 0;
  font-size: 0.8rem;
  color: var(--app-text-muted);
}
.invoice__meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.invoice__meta-right {
  text-align: right;
  font-size: 0.85rem;
}
.muted {
  color: var(--app-text-muted);
  font-size: 0.8rem;
}
.invoice__section {
  margin-bottom: 0.75rem;
}
.invoice__section-title {
  margin: 0 0 0.35rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--app-text-muted);
}
.invoice__table {
  width: 100%;
  border-collapse: collapse;
}
.invoice__table td {
  padding: 0.3rem 0;
  border-bottom: 1px dashed var(--app-border);
}
.invoice__table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.invoice__total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 2px solid var(--app-border);
  font-size: 1rem;
}
.invoice__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

@media print {
  .invoice--print {
    padding: 0;
  }
  .invoice__head,
  .invoice__meta,
  .invoice__table tr,
  .invoice__total,
  .invoice__foot {
    break-inside: avoid;
  }
}
</style>
