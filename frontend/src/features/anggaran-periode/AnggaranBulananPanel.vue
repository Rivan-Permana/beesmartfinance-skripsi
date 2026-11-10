<script setup lang="ts">
import Button from "primevue/button"
import Message from "primevue/message"
import Select from "primevue/select"
import { computed, ref, watch } from "vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { friendlyError } from "@/core/errors"
import { formatRp } from "@/core/format"
import type { AnggaranBulanan, PeriodeAkuntansi } from "@/types/api"
import { anggaranApi } from "./api"
import { bulanLabel, pemakaianBulan, statusRealisasi } from "./presentation"

const props = defineProps<{ periodeList: PeriodeAkuntansi[]; reloadKey?: number }>()

const periode = ref<number | null>(null)
const bulanIndex = ref(0)
const data = ref<AnggaranBulanan | null>(null)
const loading = ref(false)
const error = ref("")

const periodeOptions = computed(() => props.periodeList.map((p) => ({ label: `TP ${p.kode}`, value: p.id })))
const bulanOptions = computed(() => (data.value?.bulan ?? []).map((b, i) => ({ label: bulanLabel(b.bulan, b.tahun), value: i })))
const rows = computed(() => (data.value?.akun ?? []).map((akun) => ({ ...akun, ...pemakaianBulan(akun, bulanIndex.value) })))

watch(() => props.periodeList, (list) => {
  if (periode.value != null || !list.length) return
  const today = new Date().toISOString().slice(0, 10)
  periode.value = (list.find((p) => p.tgl_mulai <= today && today <= p.tgl_selesai) ?? list[0]).id
}, { immediate: true })
watch([periode, () => props.reloadKey], load)

async function load() {
  if (periode.value == null) return
  loading.value = true
  error.value = ""
  try {
    data.value = await anggaranApi.bulanan(periode.value)
    const now = new Date()
    const idx = data.value.bulan.findIndex((b) => b.tahun === now.getFullYear() && b.bulan === now.getMonth() + 1)
    bulanIndex.value = idx >= 0 ? idx : 0
  } catch (cause) {
    data.value = null
    const message = friendlyError(cause, "Rencana anggaran belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="plan-panel" aria-labelledby="plan-title" :aria-busy="loading">
    <div class="plan-head">
      <div><h2 id="plan-title">Anggaran bulanan dan realisasi</h2><p>Realisasi dari jurnal yang sudah dicatat ke buku besar. Sisa plafon = plafon tahunan dikurangi realisasi setahun pelajaran.</p></div>
      <div class="plan-filters">
        <div class="plan-field"><label for="plan-periode">Tahun pelajaran</label><Select input-id="plan-periode" v-model="periode" :options="periodeOptions" option-label="label" option-value="value" placeholder="Pilih" :disabled="loading" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div class="plan-field"><label for="plan-bulan">Bulan</label><Select input-id="plan-bulan" v-model="bulanIndex" :options="bulanOptions" option-label="label" option-value="value" :disabled="loading || !data" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
      </div>
    </div>
    <div v-if="error" class="plan-notice"><Message severity="error" :closable="false">{{ error }}</Message><Button label="Coba lagi" severity="secondary" @click="load" /></div>
    <p v-else-if="!periodeList.length" class="plan-empty">Belum ada tahun pelajaran. Keuangan membuatnya di menu Periode.</p>
    <p v-else-if="loading" class="plan-empty" role="status">Memuat rencana anggaran…</p>
    <p v-else-if="data && !rows.length" class="plan-empty">Belum ada anggaran atau realisasi beban di tahun pelajaran ini.</p>
    <template v-else-if="data">
      <div class="plan-scroll" role="region" tabindex="0" aria-label="Tabel anggaran bulanan">
        <table class="plan-table">
          <caption class="sr-only">Anggaran dan realisasi {{ bulanOptions[bulanIndex]?.label }} per akun beban</caption>
          <thead><tr><th scope="col">Akun</th><th scope="col" class="num">Anggaran bulan ini</th><th scope="col" class="num">Realisasi bulan ini</th><th scope="col" class="num">Plafon tahunan</th><th scope="col" class="num">Sisa plafon</th></tr></thead>
          <tbody>
            <tr v-for="row in rows" :key="row.kode_akun">
              <th scope="row"><span class="plan-name">{{ row.nama_akun }}</span><small>{{ row.kode_akun }}</small></th>
              <td class="num" data-label="Anggaran bulan ini">{{ row.anggaranBulan == null ? '—' : formatRp(row.anggaranBulan) }}</td>
              <td class="num" data-label="Realisasi bulan ini"><span :class="`plan-status-${statusRealisasi(row.anggaranBulan, row.realisasiBulan)}`">{{ formatRp(row.realisasiBulan) }}</span></td>
              <td class="num" data-label="Plafon tahunan">{{ row.plafon == null ? 'Belum ada' : formatRp(row.plafon) }}</td>
              <td class="num" data-label="Sisa plafon"><span :class="{ 'plan-status-lebih': row.sisa_plafon != null && Number(row.sisa_plafon) < 0 }">{{ row.sisa_plafon == null ? '—' : formatRp(row.sisa_plafon) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="plan-legend">Realisasi merah = melebihi anggaran bulan itu. Anggaran bulanan tidak bisa melebihi plafon tahunan akunnya.</p>
    </template>
  </section>
</template>

<style scoped>
.plan-panel { margin-bottom: var(--bee-space-5); background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: hidden; }
.plan-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: end; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.plan-head h2 { margin: 0 0 var(--bee-space-1); font-size: var(--bee-type-section); }
.plan-head p { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); max-width: 60ch; line-height: 1.5; }
.plan-filters { display: flex; flex-wrap: wrap; gap: var(--bee-space-3); }
.plan-field { display: grid; gap: var(--bee-space-2); min-width: 180px; }
.plan-field label { font-size: var(--bee-type-caption); font-weight: 600; }
.plan-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.plan-empty { margin: 0; padding: var(--bee-space-5); border-top: 1px solid var(--app-border); color: var(--app-text-muted); }
.plan-scroll { overflow-x: auto; border-top: 1px solid var(--app-border); }
.plan-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.plan-table th, .plan-table td { padding: var(--bee-space-3) var(--bee-space-5); border-bottom: 1px solid var(--app-border); text-align: left; vertical-align: top; }
.plan-table thead th { font-size: var(--bee-type-caption); color: var(--app-text-muted); font-weight: 600; white-space: nowrap; }
.plan-table .num { text-align: right; white-space: nowrap; }
.plan-table tbody th { font-weight: 400; }
.plan-name { display: block; }
.plan-table small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.plan-status-lebih { color: var(--bee-color-critical); font-weight: 600; }
.plan-legend { margin: 0; padding: var(--bee-space-3) var(--bee-space-5); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
@media (max-width: 640px) {
  .plan-field { min-width: 0; flex: 1 1 100%; }
  .plan-filters { width: 100%; }
  .plan-table thead { display: none; }
  .plan-table, .plan-table tbody, .plan-table tr, .plan-table th, .plan-table td { display: block; width: 100%; }
  .plan-table tr { padding: var(--bee-space-3) var(--bee-space-4); border-bottom: 1px solid var(--app-border); }
  .plan-table th, .plan-table td { padding: var(--bee-space-1) 0; border: 0; }
  .plan-table td { display: flex; justify-content: space-between; gap: var(--bee-space-3); }
  .plan-table td::before { content: attr(data-label); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
}
</style>
