<script setup lang="ts">
import Chart from "primevue/chart"
import Message from "primevue/message"
import ProgressBar from "primevue/progressbar"
import Tag from "primevue/tag"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { dashboardApi } from "./api"
import { notifyError } from "@/core/errors"
import { jurnalApi } from "@/features/jurnal/api"
import { kegiatanApi } from "@/features/kegiatan/api"
import { laporanApi } from "@/features/laporan/api"
import { tagihanApi } from "@/features/tagihan/api"
import type {
  DashboardRingkasan,
  Jurnal,
  Kegiatan,
  LabaRugiBulananResult,
  LabaRugiResult,
  PrediksiKasRow,
  RealisasiAnggaranRow,
  Tagihan,
} from "@/types/api"

const toast = useToast()
const router = useRouter()

// Brand colors (selaras --bee-*)
const C = {
  navy: "#2e2a6e",
  magenta: "#e5197f",
  orange: "#f5a623",
  blue: "#4fb0db",
  green: "#2e9e5b",
  cream: "#f5edd6",
}
const palette = [C.magenta, C.navy, C.orange, C.blue, C.green, "#9c0d55", "#ec3f8f", "#7a0b43"]
const BULAN = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]

function rp(v: string | number | null | undefined) {
  return "Rp " + Number(v ?? 0).toLocaleString("id-ID")
}
function pct(num: number, denom: number) {
  return denom > 0 ? Math.round((num / denom) * 100) : 0
}

// ---------------- state ----------------
const ringkasan = ref<DashboardRingkasan | null>(null)
const labaRugi = ref<LabaRugiResult | null>(null)
const prediksi = ref<PrediksiKasRow[]>([])
const lrBulanan = ref<LabaRugiBulananResult | null>(null)
const realisasi = ref<RealisasiAnggaranRow[]>([])
const kegiatan = ref<Kegiatan[]>([])
const outstanding = ref<Tagihan[]>([])
const mutasi = ref<Jurnal[]>([])
const loading = ref(true)
const error = ref("")

// ---------------- KPI cards ----------------
const cards = computed(() => [
  { label: "Kas & Bank",        value: rp(ringkasan.value?.kas),              icon: "pi pi-wallet",          tone: "navy" },
  { label: "Total Pendapatan",  value: rp(ringkasan.value?.total_pendapatan), icon: "pi pi-arrow-down-left", tone: "green" },
  { label: "Total Beban",       value: rp(ringkasan.value?.total_beban),      icon: "pi pi-arrow-up-right",  tone: "magenta" },
  { label: "Surplus / Defisit", value: rp(ringkasan.value?.surplus_defisit),  icon: "pi pi-chart-line",      tone: "orange" },
])

// ---------------- charts ----------------
const arusKasData = computed(() => ({
  labels: prediksi.value.map((r) => r.periode),
  datasets: [
    {
      label: "Kas Masuk",
      data: prediksi.value.map((r) => Number(r.arus_kas_masuk)),
      borderColor: C.green, backgroundColor: C.green + "33",
      tension: 0.35, fill: true,
    },
    {
      label: "Kas Keluar",
      data: prediksi.value.map((r) => Number(r.arus_kas_keluar)),
      borderColor: C.magenta, backgroundColor: C.magenta + "33",
      tension: 0.35, fill: true,
    },
    {
      label: "Net Cash Flow",
      data: prediksi.value.map((r) => Number(r.net_cash_flow_bulanan)),
      borderColor: C.navy, backgroundColor: "transparent",
      borderDash: [6, 4], tension: 0.3, fill: false,
    },
  ],
}))

const lrBulananData = computed(() => ({
  labels: BULAN,
  datasets: [
    {
      label: "Pendapatan", backgroundColor: C.green, stack: "in",
      data: (lrBulanan.value?.data ?? []).map((r) => r.pendapatan),
    },
    {
      label: "Beban", backgroundColor: C.magenta, stack: "out",
      data: (lrBulanan.value?.data ?? []).map((r) => r.beban),
    },
  ],
}))

const donutPendapatan = computed(() => ({
  labels: (labaRugi.value?.pendapatan ?? []).map((r) => r.nama_akun),
  datasets: [{
    data: (labaRugi.value?.pendapatan ?? []).map((r) => Number(r.saldo_akhir)),
    backgroundColor: palette,
  }],
}))

const donutBeban = computed(() => ({
  labels: (labaRugi.value?.beban ?? []).map((r) => r.nama_akun),
  datasets: [{
    data: (labaRugi.value?.beban ?? []).map((r) => Number(r.saldo_akhir)),
    backgroundColor: palette,
  }],
}))

const realisasiTop = computed(() =>
  [...realisasi.value]
    .map((r) => ({ ...r, utilisasi: pct(Number(r.realisasi), Number(r.pagu)) }))
    .sort((a, b) => b.utilisasi - a.utilisasi)
    .slice(0, 5),
)
const realisasiBarData = computed(() => ({
  labels: realisasiTop.value.map((r) => `${r.kode_akun} · ${r.nama_akun}`),
  datasets: [{
    label: "% Utilisasi",
    data: realisasiTop.value.map((r) => r.utilisasi),
    backgroundColor: realisasiTop.value.map((r) =>
      r.utilisasi >= 100 ? C.magenta : r.utilisasi >= 80 ? C.orange : C.navy,
    ),
  }],
}))

const kegiatanTop = computed(() =>
  [...kegiatan.value]
    .map((k) => ({ ...k, pctU: Math.round(k.rasio_utilisasi * 100) }))
    .sort((a, b) => b.pctU - a.pctU)
    .slice(0, 5),
)
const kegiatanBarData = computed(() => ({
  labels: kegiatanTop.value.map((k) => k.nama),
  datasets: [{
    label: "% Utilisasi Pagu",
    data: kegiatanTop.value.map((k) => k.pctU),
    backgroundColor: kegiatanTop.value.map((k) =>
      k.pctU >= 100 ? C.magenta : k.pctU >= 80 ? C.orange : C.blue,
    ),
  }],
}))

// chart options
const lineOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
  scales: { y: { ticks: { callback: (v: number) => "Rp " + Number(v).toLocaleString("id-ID") } } },
}
const stackedOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
  scales: {
    x: { stacked: false },
    y: { ticks: { callback: (v: number) => "Rp " + Number(v).toLocaleString("id-ID") } },
  },
}
const donutOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
}
const hbarOpts = {
  indexAxis: "y" as const, responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { x: { max: 110, ticks: { callback: (v: number) => v + "%" } } },
}
const vbarOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { max: 110, ticks: { callback: (v: number) => v + "%" } } },
}

// gauge utilisasi total anggaran
const utilisasiTotal = computed(() => {
  const p = Number(ringkasan.value?.anggaran.pagu ?? 0)
  const r = Number(ringkasan.value?.anggaran.realisasi ?? 0)
  return p > 0 ? Math.round((r / p) * 100) : 0
})

// ---------------- load ----------------
onMounted(async () => {
  try {
    const [r, lr, pk, lrb, ra, k, t, j] = await Promise.all([
      dashboardApi.ringkasan(),
      laporanApi.labaRugi(),
      dashboardApi.prediksiKas(),
      dashboardApi.labaRugiBulanan(),
      laporanApi.realisasiAnggaran(new Date().getFullYear()),
      kegiatanApi.list(),
      tagihanApi.list({ status: "BELUM" }),
      jurnalApi.list({ status: "POSTED", ordering: "-tanggal" }),
    ])
    ringkasan.value = r
    labaRugi.value = lr
    prediksi.value = pk
    lrBulanan.value = lrb
    realisasi.value = ra
    kegiatan.value = k.results
    outstanding.value = t.results.slice(0, 5)
    mutasi.value = j.results.slice(0, 5)
  } catch (e) {
    error.value = "Sebagian data dashboard gagal dimuat (butuh akses Finance/Principal)."
    notifyError(toast, e, "Gagal memuat data dashboard.")
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <h1>Dashboard</h1>

    <Message v-if="error" severity="warn" :closable="false">{{ error }}</Message>

    <!-- KPI cards -->
    <div class="kpi-grid">
      <div v-for="c in cards" :key="c.label" class="kpi" :class="c.tone">
        <i :class="c.icon" />
        <div>
          <div class="kpi-label">{{ c.label }}</div>
          <div class="kpi-value">{{ loading ? "…" : c.value }}</div>
        </div>
      </div>
    </div>

    <!-- Row: Arus Kas + Gauge Utilisasi -->
    <div class="grid">
      <section class="panel span-8">
        <header><h3>Arus Kas Bulanan</h3><span class="muted">dari jurnal posted</span></header>
        <div class="chart-wrap"><Chart type="line" :data="arusKasData" :options="lineOpts" /></div>
      </section>
      <section class="panel span-4">
        <header><h3>Utilisasi Anggaran Total</h3><span class="muted">pagu vs realisasi</span></header>
        <div class="gauge">
          <div class="gauge-num" :class="{ over: utilisasiTotal >= 100 }">{{ utilisasiTotal }}%</div>
          <ProgressBar :value="Math.min(utilisasiTotal, 100)" />
          <div class="gauge-meta">
            <span>Pagu</span><strong>{{ rp(ringkasan?.anggaran.pagu) }}</strong>
          </div>
          <div class="gauge-meta">
            <span>Realisasi</span><strong>{{ rp(ringkasan?.anggaran.realisasi) }}</strong>
          </div>
        </div>
      </section>
    </div>

    <!-- Row: Donut Pendapatan + Donut Beban + Realisasi vs Pagu -->
    <div class="grid">
      <section class="panel span-4">
        <header><h3>Komposisi Pendapatan</h3></header>
        <div class="chart-wrap"><Chart type="doughnut" :data="donutPendapatan" :options="donutOpts" /></div>
      </section>
      <section class="panel span-4">
        <header><h3>Komposisi Beban</h3></header>
        <div class="chart-wrap"><Chart type="doughnut" :data="donutBeban" :options="donutOpts" /></div>
      </section>
      <section class="panel span-4">
        <header><h3>Realisasi vs Pagu — Top 5</h3><span class="muted">% terpakai</span></header>
        <div class="chart-wrap"><Chart type="bar" :data="realisasiBarData" :options="hbarOpts" /></div>
      </section>
    </div>

    <!-- Row: Laba Rugi Bulanan + Utilisasi Kegiatan -->
    <div class="grid">
      <section class="panel span-8">
        <header><h3>Laba Rugi per Bulan</h3><span class="muted">tahun {{ lrBulanan?.tahun ?? "" }}</span></header>
        <div class="chart-wrap"><Chart type="bar" :data="lrBulananData" :options="stackedOpts" /></div>
      </section>
      <section class="panel span-4">
        <header><h3>Utilisasi Kegiatan — Top 5</h3></header>
        <div class="chart-wrap"><Chart type="bar" :data="kegiatanBarData" :options="vbarOpts" /></div>
      </section>
    </div>

    <!-- Row: tabel butuh perhatian -->
    <div class="grid">
      <section class="panel span-6">
        <header>
          <h3>Tagihan Belum Lunas</h3>
          <a class="link" @click.prevent="router.push('/tagihan')">Lihat semua</a>
        </header>
        <table class="mini">
          <thead><tr><th>Siswa</th><th>Periode</th><th class="num">Total</th></tr></thead>
          <tbody>
            <tr v-for="t in outstanding" :key="t.id">
              <td>#{{ t.siswa }}</td>
              <td>{{ BULAN[t.periode_bulan - 1] }} {{ t.periode_tahun }}</td>
              <td class="num">{{ rp(t.total) }}</td>
            </tr>
            <tr v-if="outstanding.length === 0">
              <td colspan="3" class="muted center">Tidak ada tagihan menunggak. 🎉</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel span-6">
        <header>
          <h3>Mutasi Jurnal Terbaru</h3>
          <a class="link" @click.prevent="router.push('/jurnal')">Lihat semua</a>
        </header>
        <table class="mini">
          <thead><tr><th>No. Bukti</th><th>Tanggal</th><th>Tipe</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="j in mutasi" :key="j.id">
              <td>{{ j.no_bukti }}</td>
              <td>{{ j.tanggal }}</td>
              <td class="muted">{{ j.tipe_sumber }}</td>
              <td><Tag :value="j.status" severity="success" /></td>
            </tr>
            <tr v-if="mutasi.length === 0">
              <td colspan="4" class="muted center">Belum ada jurnal posted.</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 1rem 0 1.25rem;
}
.kpi {
  background: var(--app-surface); border: 1px solid var(--app-border);
  border-radius: 14px; padding: 1.1rem 1.25rem;
  display: flex; align-items: center; gap: 1rem;
}
.kpi i {
  font-size: 1.4rem; width: 46px; height: 46px;
  border-radius: 12px; display: grid; place-items: center; color: #fff;
}
.kpi.navy i { background: var(--bee-navy); }
.kpi.magenta i { background: var(--bee-magenta); }
.kpi.orange i { background: var(--bee-orange); }
.kpi.green i { background: #2e9e5b; }
.kpi-label { font-size: 0.8rem; color: var(--app-text-muted); }
.kpi-value { font-size: 1.25rem; font-weight: 800; color: var(--bee-navy); }

.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}
.span-4 { grid-column: span 4; }
.span-6 { grid-column: span 6; }
.span-8 { grid-column: span 8; }
@media (max-width: 980px) {
  .span-4, .span-6, .span-8 { grid-column: 1 / -1; }
}

.panel {
  background: var(--app-surface); border: 1px solid var(--app-border);
  border-radius: 14px; padding: 1rem 1.1rem;
  display: flex; flex-direction: column; min-width: 0;
}
.panel header {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 0.6rem;
}
.panel header h3 { margin: 0; }
.chart-wrap { position: relative; height: 280px; }
.muted { color: var(--app-text-muted); font-size: 0.8rem; }
.center { text-align: center; }
.link { color: var(--bee-magenta); cursor: pointer; font-weight: 600; font-size: 0.85rem; }

.gauge { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.5rem 0; }
.gauge-num {
  font-family: "Baloo 2", sans-serif; font-size: 2.6rem; font-weight: 800;
  color: var(--bee-navy); text-align: center; line-height: 1;
}
.gauge-num.over { color: var(--bee-magenta); }
.gauge-meta { display: flex; justify-content: space-between; font-size: 0.85rem; }

.mini { width: 100%; border-collapse: collapse; }
.mini th, .mini td {
  padding: 0.4rem 0.3rem; text-align: left;
  border-bottom: 1px solid var(--app-border); font-size: 0.9rem;
}
.mini .num { text-align: right; }
</style>
