<script setup lang="ts">
import Tag from "primevue/tag"
import { computed } from "vue"

import { formatRp } from "@/core/format"
import type { Gaji, Pegawai } from "@/types/api"

const props = defineProps<{
  slip: Gaji
  pegawai?: Pegawai | null
  bulanLabel: string
}>()

const lines = computed(() => [
  { label: "Gaji Pokok", value: props.slip.gaji_pokok },
  { label: "Tunjangan Jabatan", value: props.slip.tunjangan_jabatan },
  { label: "Tunjangan Pengabdian", value: props.slip.tunjangan_pengabdian },
  { label: "Tunjangan Asuransi", value: props.slip.tunjangan_asuransi },
  { label: "Uang Makan", value: props.slip.uang_makan, hint: props.slip.hari_hadir ? `${props.slip.hari_hadir} hr` : undefined },
  { label: "Transport", value: props.slip.transport },
  { label: "Bonus / Insentif", value: props.slip.bonus_insentif },
  { label: "Insentif Kehadiran (THR)", value: props.slip.thr },
].filter((l) => Number(l.value) > 0))

const potongan = computed(() => [
  { label: "Potongan Pinjaman (Kasbon)", value: props.slip.potongan_pinjaman },
  { label: "Potongan Asuransi", value: props.slip.potongan_asuransi },
].filter((l) => Number(l.value) > 0))
</script>

<template>
  <div class="slip">
    <header class="slip__head">
      <img src="/logo-lebah.svg" alt="" width="40" height="40" />
      <div>
        <h2>RA Lebah Madu</h2>
        <p>Slip Gaji — {{ bulanLabel }} {{ slip.periode_tahun }}</p>
      </div>
    </header>

    <div class="slip__meta">
      <div>
        <strong>{{ pegawai?.nama ?? `Pegawai #${slip.pegawai}` }}</strong>
        <div v-if="pegawai?.jabatan" class="muted">{{ pegawai.jabatan }}</div>
        <div v-if="pegawai?.nip" class="muted">NIP: {{ pegawai.nip }}</div>
      </div>
      <Tag :value="slip.jurnal ? 'Sudah dijurnal' : 'Draft'" :severity="slip.jurnal ? 'success' : 'warn'" />
    </div>

    <section>
      <h3>Pendapatan</h3>
      <table>
        <tbody>
          <tr v-for="(l, i) in lines" :key="i">
            <td>{{ l.label }}<span v-if="l.hint" class="muted"> ({{ l.hint }})</span></td>
            <td class="num">{{ formatRp(l.value) }}</td>
          </tr>
          <tr class="subtotal">
            <td>Total Bruto</td>
            <td class="num">{{ formatRp(slip.total_bruto) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="potongan.length">
      <h3>Potongan</h3>
      <table>
        <tbody>
          <tr v-for="(l, i) in potongan" :key="i">
            <td>{{ l.label }}</td>
            <td class="num">{{ formatRp(l.value) }}</td>
          </tr>
          <tr class="subtotal">
            <td>Total Potongan</td>
            <td class="num">{{ formatRp(slip.total_potongan) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <div class="slip__net">
      <span>Gaji Diterima (Netto)</span>
      <strong>{{ formatRp(slip.total_netto) }}</strong>
    </div>
  </div>
</template>

<style scoped>
.slip { font-size: 0.9rem; line-height: 1.45; }
.slip__head {
  display: flex; gap: 0.75rem; align-items: center;
  border-bottom: 2px solid var(--app-primary, #2e2a6e);
  padding-bottom: 0.75rem; margin-bottom: 0.85rem;
}
.slip__head h2 { margin: 0; font-size: 1.1rem; color: var(--app-primary, #2e2a6e); }
.slip__head p { margin: 0.15rem 0 0; font-size: 0.8rem; color: var(--app-text-muted); }
.slip__meta {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 0.85rem;
}
.muted { color: var(--app-text-muted); font-size: 0.8rem; }
section h3 {
  margin: 0 0 0.35rem; font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--app-text-muted);
}
table { width: 100%; border-collapse: collapse; margin-bottom: 0.75rem; }
td { padding: 0.3rem 0; border-bottom: 1px dashed var(--app-border); }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.subtotal td { font-weight: 700; border-bottom: none; }
.slip__net {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 0.75rem; border-top: 2px solid var(--app-border); font-size: 1rem;
}
.slip__net strong { color: #2e9e5b; font-size: 1.1rem; }
</style>
