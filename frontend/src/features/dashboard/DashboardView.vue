<script setup lang="ts">
import Chart from "primevue/chart"
import DatePicker from "primevue/datepicker"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"

import { dashboardApi, type DashboardFilter } from "./api"
import {
  barChartOptions,
  barColorByThreshold,
  CHART,
  CHART_PALETTE,
  doughnutChartOptions,
  lineChartOptions,
  sparkBarOptions,
} from "./chartTheme"
import { formatRp } from "@/core/format"
import { notifyError } from "@/core/errors"
import ChartPanel from "@/shared/components/ChartPanel.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import RingGauge from "@/shared/components/RingGauge.vue"
import { useAuthStore } from "@/stores/auth"
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
  MenuKatering,
  PrediksiKasRow,
  RealisasiAnggaranRow,
  Tagihan,
} from "@/types/api"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"

const toast = useToast()
const router = useRouter()
const auth = useAuthStore()

const BULAN = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
const THRESH = { warn: 80, danger: 100 }
const UTIL_COLORS = { ok: CHART.navy, warn: CHART.orange, danger: CHART.magenta }

function rp(v: string | number | null | undefined) {
  return formatRp(v)
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
const pendingJurnal = ref<Jurnal[]>([])
const mutasi = ref<Jurnal[]>([])
const menuHariIni = ref<MenuKatering | null>(null)
const loading = ref(true)
const error = ref("")

type FilterMode = "month" | "year" | "day"
const filterMode = ref<FilterMode>("month")
const filterBulan = ref(new Date().getMonth() + 1)
const filterTahun = ref(new Date().getFullYear())
const filterTanggal = ref(new Date())

const FILTER_MODE_OPTS = [
  { label: "Per Bulan", value: "month" as FilterMode },
  { label: "Per Tahun", value: "year" as FilterMode },
  { label: "Per Hari", value: "day" as FilterMode },
]

const tahunOptions = computed(() => {
  const end = new Date().getFullYear() + 1
  const opts: { label: string; value: number }[] = []
  for (let y = end; y >= 2023; y -= 1) opts.push({ label: String(y), value: y })
  return opts
})

const filterParams = computed((): DashboardFilter => {
  if (filterMode.value === "day") {
    return { tanggal: filterTanggal.value.toISOString().slice(0, 10) }
  }
  if (filterMode.value === "year") return { tahun: filterTahun.value }
  return { tahun: filterTahun.value, bulan: filterBulan.value }
})

const periodeLabel = computed(
  () => ringkasan.value?.periode_filter?.label ?? "…",
)

// ---------------- KPI cards ----------------
const cards = computed(() => [
  { label: "Kas & Bank",        value: rp(ringkasan.value?.kas),              icon: "pi pi-wallet",          tone: "navy" },
  { label: "Total Pendapatan",  value: rp(ringkasan.value?.total_pendapatan), icon: "pi pi-arrow-down-left", tone: "green" },
  { label: "Total Beban",       value: rp(ringkasan.value?.total_beban),      icon: "pi pi-arrow-up-right",  tone: "magenta" },
  { label: "Surplus / Defisit", value: rp(ringkasan.value?.surplus_defisit),  icon: "pi pi-chart-line",      tone: "orange" },
])

const ops = computed(() => ringkasan.value?.operasional)
const opsCards = computed(() => {
  const o = ops.value
  if (!o) return []
  const hadirLabel = filterMode.value === "day" ? "Hadir (hari ini)" : `Hadir (${o.periode_ops_label})`
  return [
    { label: "Siswa Aktif", value: String(o.siswa_aktif), icon: "pi pi-users", tone: "navy" as const },
    { label: hadirLabel, value: String(o.hadir_bulan_ini), icon: "pi pi-check-circle", tone: "green" as const },
    { label: "Hari Katering", value: String(o.katering_bulan_ini), icon: "pi pi-calendar", tone: "orange" as const },
    { label: "Tunggakan Tagihan", value: String(o.tagihan_belum), icon: "pi pi-exclamation-circle", tone: "magenta" as const },
    { label: "Collection Rate", value: `${o.collection_rate_pct}%`, icon: "pi pi-percentage", tone: "navy" as const },
    { label: "Jurnal Draft", value: String(o.jurnal_menunggu_approve), icon: "pi pi-inbox", tone: "orange" as const },
  ]
})

const absensiSparkData = computed(() => ({
  labels: (ops.value?.absensi_sparkline ?? []).map((r) => r.label),
  datasets: [{
    label: "Kehadiran (hadir)",
    data: (ops.value?.absensi_sparkline ?? []).map((r) => r.hadir),
    backgroundColor: CHART.blue + "cc",
    hoverBackgroundColor: CHART.blue,
    borderRadius: 8,
    borderSkipped: false,
    maxBarThickness: 36,
  }],
}))

// ---------------- charts ----------------
const arusKasData = computed(() => ({
  labels: prediksi.value.map((r) => r.periode),
  datasets: [
    {
      label: "Kas Masuk",
      data: prediksi.value.map((r) => Number(r.arus_kas_masuk)),
      borderColor: CHART.green,
      backgroundColor: CHART.green + "28",
      fill: true,
    },
    {
      label: "Kas Keluar",
      data: prediksi.value.map((r) => Number(r.arus_kas_keluar)),
      borderColor: CHART.magenta,
      backgroundColor: CHART.magenta + "22",
      fill: true,
    },
    {
      label: "Net Cash Flow",
      data: prediksi.value.map((r) => Number(r.net_cash_flow_bulanan)),
      borderColor: CHART.navy,
      backgroundColor: "transparent",
      borderDash: [5, 4],
      fill: false,
    },
  ],
}))

const lrBulananData = computed(() => ({
  labels: BULAN,
  datasets: [
    {
      label: "Pendapatan",
      backgroundColor: CHART.green + "dd",
      hoverBackgroundColor: CHART.green,
      borderRadius: { topLeft: 6, topRight: 6 },
      borderSkipped: false,
      data: (lrBulanan.value?.data ?? []).map((r) => r.pendapatan),
    },
    {
      label: "Beban",
      backgroundColor: CHART.magenta + "cc",
      hoverBackgroundColor: CHART.magenta,
      borderRadius: { topLeft: 6, topRight: 6 },
      borderSkipped: false,
      data: (lrBulanan.value?.data ?? []).map((r) => r.beban),
    },
  ],
}))

const donutPendapatan = computed(() => ({
  labels: (labaRugi.value?.pendapatan ?? []).map((r) => r.nama_akun),
  datasets: [{
    data: (labaRugi.value?.pendapatan ?? []).map((r) => Number(r.saldo_akhir)),
    backgroundColor: CHART_PALETTE,
    borderWidth: 0,
    hoverOffset: 10,
  }],
}))

const donutBeban = computed(() => ({
  labels: (labaRugi.value?.beban ?? []).map((r) => r.nama_akun),
  datasets: [{
    data: (labaRugi.value?.beban ?? []).map((r) => Number(r.saldo_akhir)),
    backgroundColor: CHART_PALETTE,
    borderWidth: 0,
    hoverOffset: 10,
  }],
}))

const hasDonutPendapatan = computed(() => (labaRugi.value?.pendapatan?.length ?? 0) > 0)
const hasDonutBeban = computed(() => (labaRugi.value?.beban?.length ?? 0) > 0)
const hasArusKas = computed(() => prediksi.value.length > 0)
const hasLrBulanan = computed(() => (lrBulanan.value?.data?.length ?? 0) > 0)
const hasAbsensiSpark = computed(() => (ops.value?.absensi_sparkline?.length ?? 0) > 0)

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
      barColorByThreshold(r.utilisasi, THRESH, UTIL_COLORS),
    ),
    borderRadius: 8,
    borderSkipped: false,
    barThickness: 14,
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
      barColorByThreshold(k.pctU, THRESH, { ok: CHART.blue, warn: CHART.orange, danger: CHART.magenta }),
    ),
    borderRadius: 8,
    borderSkipped: false,
    maxBarThickness: 40,
  }],
}))

const lineOpts = lineChartOptions(true)
const stackedOpts = barChartOptions({ percent: false })
const donutOpts = doughnutChartOptions()
const hbarOpts = barChartOptions({ horizontal: true, percent: true })
const vbarOpts = barChartOptions({ percent: true })
const sparkOpts = sparkBarOptions()

const surplusTone = computed(() => {
  const v = Number(ringkasan.value?.surplus_defisit ?? 0)
  if (v > 0) return "positive"
  if (v < 0) return "negative"
  return "neutral"
})

// gauge utilisasi total anggaran
const utilisasiTotal = computed(() => {
  const p = Number(ringkasan.value?.anggaran.pagu ?? 0)
  const r = Number(ringkasan.value?.anggaran.realisasi ?? 0)
  return p > 0 ? Math.round((r / p) * 100) : 0
})

// ---------------- load ----------------
async function loadDashboard() {
  loading.value = true
  error.value = ""
  const fp = filterParams.value
  const tahunChart = fp.tahun ?? filterTahun.value

  const settled = await Promise.allSettled([
    dashboardApi.ringkasan(fp),
    laporanApi.labaRugi(
      filterMode.value === "month" ? { tahun: fp.tahun, bulan: fp.bulan } : { tahun: tahunChart },
    ),
    dashboardApi.prediksiKas(tahunChart),
    dashboardApi.labaRugiBulanan(tahunChart),
    laporanApi.realisasiAnggaran(tahunChart),
    auth.hasRole(["TeacherInCharge", "SchoolPrincipal", "Finance"])
      ? kegiatanApi.list()
      : Promise.resolve({ results: [] as Kegiatan[] }),
    tagihanApi.list({ status: "BELUM" }),
    jurnalApi.list({ status: "DRAFT", ordering: "-tanggal" }),
    jurnalApi.list({ status: "POSTED", ordering: "-tanggal" }),
    dashboardApi.menuHariIni(
      filterMode.value === "day" && fp.tanggal ? fp.tanggal : undefined,
    ),
  ])

  const pick = <T,>(i: number) =>
    settled[i].status === "fulfilled" ? (settled[i] as PromiseFulfilledResult<T>).value : null

  const r = pick<DashboardRingkasan>(0)
  const lr = pick<LabaRugiResult>(1)
  const pk = pick<PrediksiKasRow[]>(2)
  const lrb = pick<LabaRugiBulananResult>(3)
  const ra = pick<RealisasiAnggaranRow[]>(4)
  const k = pick<{ results: Kegiatan[] }>(5)
  const t = pick<{ results: Tagihan[] }>(6)
  const pj = pick<{ results: Jurnal[] }>(7)
  const j = pick<{ results: Jurnal[] }>(8)
  const menu = pick<{ tanggal: string; menu: MenuKatering | null }>(9)

  if (r) ringkasan.value = r
  if (lr) labaRugi.value = lr
  if (pk) prediksi.value = pk
  if (lrb) lrBulanan.value = lrb
  if (ra) realisasi.value = ra
  if (k) kegiatan.value = k.results
  if (t) outstanding.value = t.results.slice(0, 5)
  if (pj) pendingJurnal.value = pj.results.slice(0, 5)
  if (j) mutasi.value = j.results.slice(0, 5)
  menuHariIni.value = menu?.menu ?? null

  if (!r) {
    error.value = "Ringkasan keuangan belum dapat dimuat. Coba muat ulang halaman."
    const failed = settled[0]
    if (failed.status === "rejected") notifyError(toast, failed.reason, "Gagal memuat dashboard.")
  }

  loading.value = false
}

watch([filterMode, filterBulan, filterTahun, filterTanggal], loadDashboard)
onMounted(loadDashboard)
</script>

<template>
  <PageLayout title="Dashboard" subtitle="Ringkasan keuangan & operasional sekolah">
    <template #filters>
      <Select
        v-model="filterMode"
        :options="FILTER_MODE_OPTS"
        option-label="label"
        option-value="value"
        placeholder="Mode filter"
      />
      <PeriodPicker
        v-if="filterMode === 'month'"
        v-model:bulan="filterBulan"
        v-model:tahun="filterTahun"
      />
      <Select
        v-else-if="filterMode === 'year'"
        v-model="filterTahun"
        :options="tahunOptions"
        option-label="label"
        option-value="value"
        placeholder="Tahun"
      />
      <DatePicker
        v-else
        v-model="filterTanggal"
        date-format="yy-mm-dd"
        show-button-bar
      />
    </template>

    <div class="dash-toolbar">
      <span class="periode-badge">
        <i class="pi pi-calendar" />
        Periode aktif: <strong>{{ periodeLabel }}</strong>
      </span>
    </div>

    <Message v-if="error" severity="warn" :closable="false">{{ error }}</Message>

    <div v-if="ringkasan && !loading" class="hero-strip" :class="surplusTone">
      <div class="hero-strip__main">
        <span class="hero-strip__label">Surplus / Defisit</span>
        <span class="hero-strip__value tabular-nums">{{ rp(ringkasan.surplus_defisit) }}</span>
      </div>
      <div class="hero-strip__meta">
        <div><span>Kas & Bank</span><strong class="tabular-nums">{{ rp(ringkasan.kas) }}</strong></div>
        <div><span>Pendapatan</span><strong class="tabular-nums">{{ rp(ringkasan.total_pendapatan) }}</strong></div>
        <div><span>Beban</span><strong class="tabular-nums">{{ rp(ringkasan.total_beban) }}</strong></div>
      </div>
    </div>

    <h3 class="section-title"><i class="pi pi-wallet" /> Keuangan</h3>
    <div class="kpi-grid">
      <KpiCard
        v-for="c in cards"
        :key="c.label"
        :label="c.label"
        :value="loading ? '…' : c.value"
        :icon="c.icon"
        :tone="c.tone as 'navy' | 'green' | 'magenta' | 'orange'"
      />
    </div>

    <template v-if="opsCards.length">
      <h3 class="section-title"><i class="pi pi-users" /> Operasional Siswa</h3>
      <div class="grid menu-widget-row">
        <ChartPanel
          class="span-4"
          title="Menu Katering Hari Ini"
          subtitle="Foto & keterangan menu"
          icon="pi pi-image"
          accent="orange"
          size="sm"
          :loading="loading"
        >
          <div v-if="menuHariIni?.gambar_url" class="menu-photo-wrap">
            <img :src="menuHariIni.gambar_url" alt="Foto menu katering" class="menu-photo" />
          </div>
          <p v-if="menuHariIni?.keterangan" class="menu-text">{{ menuHariIni.keterangan }}</p>
          <p v-else-if="!loading" class="muted menu-empty">Belum ada menu untuk hari ini.</p>
        </ChartPanel>
      </div>
      <div class="kpi-grid ops-grid">
        <KpiCard
          v-for="c in opsCards"
          :key="c.label"
          :label="c.label"
          :value="loading ? '…' : c.value"
          :icon="c.icon"
          :tone="c.tone"
        />
      </div>
      <div class="grid">
        <ChartPanel
          class="span-6"
          title="Tren Kehadiran"
          subtitle="6 bulan terakhir"
          icon="pi pi-chart-bar"
          accent="blue"
          size="sm"
          :loading="loading"
          :empty="!hasAbsensiSpark"
        >
          <div class="chart-wrap"><Chart type="bar" :data="absensiSparkData" :options="sparkOpts" /></div>
        </ChartPanel>
        <ChartPanel
          class="span-6"
          title="Jurnal Menunggu Approve"
          subtitle="Status draft"
          icon="pi pi-inbox"
          accent="orange"
          size="sm"
          :loading="loading"
        >
          <template #action>
            <a class="link" @click.prevent="router.push('/jurnal')">Buka jurnal</a>
          </template>
          <div class="table-wrap">
            <table class="mini">
              <thead><tr><th>No. Bukti</th><th>Tanggal</th><th>Tipe</th></tr></thead>
              <tbody>
                <tr v-for="j in pendingJurnal" :key="j.id">
                  <td>{{ j.no_bukti }}</td>
                  <td>{{ j.tanggal }}</td>
                  <td class="muted">{{ j.tipe_sumber }}</td>
                </tr>
                <tr v-if="pendingJurnal.length === 0">
                  <td colspan="3" class="muted center">Tidak ada jurnal draft.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </ChartPanel>
      </div>
    </template>

    <div class="grid">
      <ChartPanel
        class="span-8"
        title="Arus Kas Bulanan"
        subtitle="Kas masuk, keluar & net flow dari jurnal posted"
        icon="pi pi-chart-line"
        accent="green"
        size="lg"
        :loading="loading"
        :empty="!hasArusKas"
      >
        <div class="chart-wrap"><Chart type="line" :data="arusKasData" :options="lineOpts" /></div>
      </ChartPanel>
      <ChartPanel
        class="span-4"
        title="Utilisasi Anggaran"
        subtitle="Pagu vs realisasi total"
        icon="pi pi-percentage"
        accent="navy"
        size="lg"
        :loading="loading"
      >
        <div class="gauge-wrap">
          <RingGauge :value="utilisasiTotal" label="terpakai" :size="168" />
          <div class="gauge-stats">
            <div class="gauge-stat">
              <span>Pagu</span>
              <strong class="tabular-nums">{{ rp(ringkasan?.anggaran.pagu) }}</strong>
            </div>
            <div class="gauge-stat">
              <span>Realisasi</span>
              <strong class="tabular-nums">{{ rp(ringkasan?.anggaran.realisasi) }}</strong>
            </div>
          </div>
        </div>
      </ChartPanel>
    </div>

    <div class="grid">
      <ChartPanel
        class="span-4"
        title="Komposisi Pendapatan"
        subtitle="Per akun pendapatan"
        icon="pi pi-arrow-down-left"
        accent="green"
        :loading="loading"
        :empty="!hasDonutPendapatan"
      >
        <div class="chart-wrap"><Chart type="doughnut" :data="donutPendapatan" :options="donutOpts" /></div>
      </ChartPanel>
      <ChartPanel
        class="span-4"
        title="Komposisi Beban"
        subtitle="Per akun beban"
        icon="pi pi-arrow-up-right"
        accent="magenta"
        :loading="loading"
        :empty="!hasDonutBeban"
      >
        <div class="chart-wrap"><Chart type="doughnut" :data="donutBeban" :options="donutOpts" /></div>
      </ChartPanel>
      <ChartPanel
        class="span-4"
        title="Realisasi vs Pagu"
        subtitle="Top 5 akun — % terpakai"
        icon="pi pi-sliders-h"
        accent="navy"
        :loading="loading"
        :empty="realisasiTop.length === 0"
      >
        <div class="chart-wrap"><Chart type="bar" :data="realisasiBarData" :options="hbarOpts" /></div>
      </ChartPanel>
    </div>

    <div class="grid">
      <ChartPanel
        class="span-8"
        title="Laba Rugi per Bulan"
        :subtitle="`Tahun ${lrBulanan?.tahun ?? filterTahun}`"
        icon="pi pi-chart-bar"
        accent="green"
        size="lg"
        :loading="loading"
        :empty="!hasLrBulanan"
      >
        <div class="chart-wrap"><Chart type="bar" :data="lrBulananData" :options="stackedOpts" /></div>
      </ChartPanel>
      <ChartPanel
        class="span-4"
        title="Utilisasi Kegiatan"
        subtitle="Top 5 kegiatan"
        icon="pi pi-flag"
        accent="blue"
        size="lg"
        :loading="loading"
        :empty="kegiatanTop.length === 0"
      >
        <div class="chart-wrap"><Chart type="bar" :data="kegiatanBarData" :options="vbarOpts" /></div>
      </ChartPanel>
    </div>

    <div class="grid">
      <ChartPanel
        class="span-6"
        title="Tagihan Belum Lunas"
        subtitle="5 tagihan teratas"
        icon="pi pi-exclamation-circle"
        accent="magenta"
        size="sm"
        :loading="loading"
      >
        <template #action>
          <a class="link" @click.prevent="router.push('/tunggakan-tagihan')">Lihat semua</a>
        </template>
        <div class="table-wrap">
          <table class="mini">
            <thead><tr><th>Siswa</th><th>Periode</th><th class="num">Total</th></tr></thead>
            <tbody>
              <tr v-for="t in outstanding" :key="t.id">
                <td>{{ t.siswa_nama ?? `#${t.siswa}` }}</td>
                <td>{{ BULAN[t.periode_bulan - 1] }} {{ t.periode_tahun }}</td>
                <td class="num">{{ rp(t.total) }}</td>
              </tr>
              <tr v-if="outstanding.length === 0">
                <td colspan="3" class="muted center">Tidak ada tagihan menunggak.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ChartPanel>

      <ChartPanel
        class="span-6"
        title="Mutasi Jurnal Terbaru"
        subtitle="Jurnal posted"
        icon="pi pi-book"
        accent="navy"
        size="sm"
        :loading="loading"
      >
        <template #action>
          <a class="link" @click.prevent="router.push('/jurnal')">Lihat semua</a>
        </template>
        <div class="table-wrap">
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
        </div>
      </ChartPanel>
    </div>
  </PageLayout>
</template>

<style scoped>
.dash-toolbar {
  margin-bottom: 1rem;
}
.periode-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--bee-navy) 8%, white);
  color: var(--bee-navy);
  font-size: 0.82rem;
  font-weight: 600;
}
.periode-badge i { opacity: 0.7; font-size: 0.85rem; }

.hero-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem 1.5rem;
  padding: 1.15rem 1.35rem;
  margin-bottom: 1.25rem;
  border-radius: var(--bee-radius-lg);
  background: linear-gradient(135deg, var(--bee-navy) 0%, #3a3690 100%);
  color: #fff;
  box-shadow: 0 12px 32px rgba(46, 42, 110, 0.22);
}
.hero-strip.positive {
  background: linear-gradient(135deg, #1f6b42 0%, var(--bee-success) 100%);
  box-shadow: 0 12px 32px rgba(46, 158, 91, 0.25);
}
.hero-strip.negative {
  background: linear-gradient(135deg, #9c0d55 0%, var(--bee-magenta) 100%);
  box-shadow: 0 12px 32px rgba(229, 25, 127, 0.22);
}
.hero-strip__label {
  display: block;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.85;
}
.hero-strip__value {
  font-family: "Baloo 2", sans-serif;
  font-size: 1.85rem;
  font-weight: 800;
  line-height: 1.1;
}
.hero-strip__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 1.75rem;
}
.hero-strip__meta div {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.hero-strip__meta span {
  font-size: 0.72rem;
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.hero-strip__meta strong {
  font-size: 0.95rem;
}

.menu-widget-row {
  margin-bottom: 0.5rem;
}
.menu-photo-wrap {
  margin: 0.25rem 0 0.5rem;
  border-radius: 12px;
  overflow: hidden;
  max-height: 160px;
  box-shadow: 0 4px 16px rgba(46, 42, 110, 0.1);
}
.menu-photo {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
}
.menu-text {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--app-text);
}
.menu-empty { margin: 0; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 0.5rem 0 1.5rem;
}
.ops-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
.section-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0.5rem 0 0.75rem;
  font-size: 0.88rem;
  font-weight: 800;
  color: var(--bee-navy);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.section-title i {
  font-size: 0.9rem;
  opacity: 0.65;
}

.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}
.grid > :deep(.chart-panel),
.grid > .span-4,
.grid > .span-6,
.grid > .span-8 {
  min-width: 0;
}
.span-4 { grid-column: span 4; }
.span-6 { grid-column: span 6; }
.span-8 { grid-column: span 8; }
@media (max-width: 980px) {
  .span-4, .span-6, .span-8 { grid-column: 1 / -1; }
  .hero-strip { flex-direction: column; align-items: flex-start; }
}

.chart-wrap {
  position: relative;
  height: 280px;
}

.gauge-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0 0.25rem;
}
.gauge-stats {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.gauge-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0.75rem;
  border-radius: 10px;
  background: rgba(46, 42, 110, 0.04);
  font-size: 0.85rem;
}
.gauge-stat span { color: var(--app-text-muted); }
.gauge-stat strong { color: var(--bee-navy); }

.table-wrap {
  overflow-x: auto;
  margin: -0.15rem 0;
}
.muted { color: var(--app-text-muted); font-size: 0.82rem; }
.center { text-align: center; padding: 0.75rem 0; }
.link {
  color: var(--bee-magenta);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  text-decoration: none;
}
.link:hover { text-decoration: underline; }

.mini { width: 100%; border-collapse: collapse; }
.mini th {
  padding: 0.5rem 0.4rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--app-text-muted);
  border-bottom: 1px solid rgba(46, 42, 110, 0.08);
}
.mini td {
  padding: 0.55rem 0.4rem;
  text-align: left;
  border-bottom: 1px solid rgba(46, 42, 110, 0.05);
  font-size: 0.88rem;
}
.mini tbody tr:hover td {
  background: rgba(46, 42, 110, 0.03);
}
.mini .num { text-align: right; font-variant-numeric: tabular-nums; }
</style>
