<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import Chart from "primevue/chart"
import Select from "primevue/select"
import Button from "primevue/button"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Tabs from "primevue/tabs"
import TabList from "primevue/tablist"
import Tab from "primevue/tab"
import TabPanels from "primevue/tabpanels"
import TabPanel from "primevue/tabpanel"
import PageLayout from "@/shared/components/PageLayout.vue"
import ChartPanel from "@/shared/components/ChartPanel.vue"
import ChartDataTable from "@/shared/components/ChartDataTable.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { useAuthStore } from "@/stores/auth"
import { formatRp } from "@/core/format"
import { dashboardApi, type DashboardFilter } from "./api"
import { CHART, CHART_PALETTE, lineChartOptions, barChartOptions } from "./chartTheme"
import { dashboardMode, canReviewJurnal } from "./presentation"
import { jurnalApi } from "@/features/jurnal/api"
import { kegiatanApi } from "@/features/kegiatan/api"
import { laporanApi } from "@/features/laporan/api"
import { tagihanApi } from "@/features/tagihan/api"
import type { DashboardRingkasan, Jurnal, Kegiatan, LabaRugiBulananResult, LabaRugiResult, PrediksiKasRow, RealisasiAnggaranRow, Tagihan } from "@/types/api"

const auth = useAuthStore()
const router = useRouter()
const mode = computed(() => dashboardMode(auth.roles))
const principal = computed(() => mode.value === "principal")
const months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
const ringkasan = ref<DashboardRingkasan | null>(null)
const labaRugi = ref<LabaRugiResult | null>(null)
const monthly = ref<LabaRugiBulananResult | null>(null)
const cash = ref<PrediksiKasRow[]>([])
const budget = ref<RealisasiAnggaranRow[]>([])
const activities = ref<Kegiatan[]>([])
const outstanding = ref<Tagihan[]>([])
const queue = ref<Jurnal[]>([])
const recent = ref<Jurnal[]>([])
const queuePageCount = ref(0)
const loading = ref(true)
const failed = ref<string[]>([])
const filterMode = ref<"month" | "year">("month")
const month = ref(new Date().getMonth() + 1)
const year = ref(new Date().getFullYear())
const appliedYear = ref(year.value)
const appliedScope = ref("")
const cashScope = ref("")
const appliedProfitScope = ref("")
let loadSequence = 0
const filterModes = [{ label: "Bulanan", value: "month" }, { label: "Tahunan", value: "year" }]
const years = Array.from({ length: new Date().getFullYear() - 2023 + 2 }, (_, index) => new Date().getFullYear() + 1 - index)
const params = computed((): DashboardFilter => filterMode.value === "year" ? { tahun: year.value } : { tahun: year.value, bulan: month.value })
const rp = (value: string | number | null | undefined) => value == null ? "Belum diketahui" : formatRp(value)
const cards = computed(() => [
  { label: "Pendapatan", value: rp(ringkasan.value?.total_pendapatan), icon: "arrow-down-left" },
  { label: "Beban", value: rp(ringkasan.value?.total_beban), icon: "arrow-up-right" },
  { label: "Surplus / defisit", value: rp(ringkasan.value?.surplus_defisit), icon: "chart-line" },
])
const reviewQueue = computed(() => principal.value ? queue.value.filter((item) => canReviewJurnal(item, auth.user?.id)) : queue.value)
const budgetTop = computed(() => [...budget.value].sort((a, b) => Number(b.realisasi) - Number(a.realisasi)).slice(0, 5))
const cashData = computed(() => ({ labels: cash.value.map((row) => `${months[row.bulan - 1]} ${row.tahun}`), datasets: [
  { label: "Kas masuk", data: cash.value.map((row) => Number(row.arus_kas_masuk)), borderColor: CHART.navy, backgroundColor: CHART.navy, pointRadius: 3 },
  { label: "Kas keluar", data: cash.value.map((row) => Number(row.arus_kas_keluar)), borderColor: CHART.magenta, backgroundColor: CHART.magenta, borderDash: [5, 4], pointRadius: 3 },
  { label: "Arus kas bersih", data: cash.value.map((row) => Number(row.net_cash_flow_bulanan)), borderColor: CHART.blue, backgroundColor: CHART.blue, borderDash: [2, 3], pointRadius: 3 },
] }))
const monthlyData = computed(() => ({ labels: (monthly.value?.data ?? []).map((row) => months[row.bulan - 1]!), datasets: [
  { label: "Pendapatan", data: (monthly.value?.data ?? []).map((row) => row.pendapatan), backgroundColor: CHART.navy },
  { label: "Beban", data: (monthly.value?.data ?? []).map((row) => row.beban), backgroundColor: CHART.magenta },
] }))
const budgetData = computed(() => ({ labels: budgetTop.value.map((row) => `${row.kode_akun} ${row.nama_akun}`), datasets: [
  { label: "Pagu", data: budgetTop.value.map((row) => Number(row.pagu)), backgroundColor: CHART.navy },
  { label: "Realisasi", data: budgetTop.value.map((row) => Number(row.realisasi)), backgroundColor: CHART.blue },
] }))
const incomeData = computed(() => ({ labels: (labaRugi.value?.pendapatan ?? []).map((row) => row.nama_akun), datasets: [{ label: "Pendapatan", data: (labaRugi.value?.pendapatan ?? []).map((row) => Number(row.saldo_akhir)), backgroundColor: CHART_PALETTE }] }))
const expenseData = computed(() => ({ labels: (labaRugi.value?.beban ?? []).map((row) => row.nama_akun), datasets: [{ label: "Beban", data: (labaRugi.value?.beban ?? []).map((row) => Number(row.saldo_akhir)), backgroundColor: CHART_PALETTE }] }))
const lineOptions = lineChartOptions(true)
const barOptions = barChartOptions()
const horizontalOptions = barChartOptions({ horizontal: true })

async function loadDashboard() {
  const sequence = ++loadSequence
  loading.value = true
  const scope = params.value
  const chartYear = scope.tahun ?? year.value
  const currentMode = mode.value
  const result = await Promise.allSettled([
    dashboardApi.ringkasan(scope),
    laporanApi.labaRugi(filterMode.value === "month" ? { tahun: scope.tahun, bulan: scope.bulan } : { tahun: chartYear }),
    dashboardApi.prediksiKas(chartYear), dashboardApi.labaRugiBulanan(chartYear), laporanApi.realisasiAnggaran(chartYear),
    currentMode === "principal" ? kegiatanApi.list() : Promise.resolve({ results: [] as Kegiatan[] }),
    tagihanApi.list({ status: "BELUM" }),
    jurnalApi.list({ status: currentMode === "principal" ? "PENDING" : "DRAFT", ordering: "-tanggal" }),
    jurnalApi.list({ status: "POSTED", ordering: "-tanggal" }),
  ])
  if (sequence !== loadSequence) return
  const errors: string[] = []
  function pick<T>(index: number, label: string): T | null {
    const item = result[index]!
    if (item.status === "fulfilled") return item.value as T
    errors.push(label)
    return null
  }
  ringkasan.value = pick<DashboardRingkasan>(0, "Ringkasan keuangan")
  labaRugi.value = pick<LabaRugiResult>(1, "Rincian pendapatan dan beban")
  cash.value = pick<PrediksiKasRow[]>(2, "Arus kas") ?? []
  monthly.value = pick<LabaRugiBulananResult>(3, "Laba rugi bulanan")
  budget.value = pick<RealisasiAnggaranRow[]>(4, "Anggaran") ?? []
  activities.value = pick<{ results: Kegiatan[] }>(5, "Kegiatan")?.results ?? []
  outstanding.value = pick<{ results: Tagihan[] }>(6, "Tagihan")?.results.slice(0, 5) ?? []
  queue.value = pick<{ results: Jurnal[] }>(7, "Jurnal yang perlu ditinjau")?.results ?? []
  queuePageCount.value = queue.value.length
  recent.value = pick<{ results: Jurnal[] }>(8, "Jurnal tercatat")?.results.slice(0, 5) ?? []
  failed.value = errors
  cashScope.value = scope.bulan ? `Saldo kumulatif hingga akhir ${months[scope.bulan - 1]} ${chartYear}.` : `Saldo kumulatif hingga akhir tahun ${chartYear}.`
  appliedProfitScope.value = scope.bulan ? `${months[scope.bulan - 1]} ${chartYear}` : `Tahun ${chartYear}`
  appliedYear.value = chartYear
  appliedScope.value = ringkasan.value?.periode_filter?.label ?? (scope.tanggal ?? (scope.bulan ? `${months[scope.bulan - 1]} ${chartYear}` : `Tahun ${chartYear}`))
  loading.value = false
}
watch([filterMode, month, year, mode], () => { if (auth.isAuthenticated) void loadDashboard() })
onMounted(loadDashboard)
</script>

<template>
  <PageLayout class="dashboard-page" :title="principal ? 'Ikhtisar sekolah' : 'Ringkasan keuangan'" :subtitle="principal ? 'Keputusan, kondisi keuangan, dan kegiatan sekolah.' : 'Kas, pencatatan, dan tindak lanjut transaksi.'" :surface="false">
    <template #actions><Button label="Muat ulang" aria-label="Muat ulang dashboard" severity="secondary" :loading="loading" @click="loadDashboard"><template #icon><Icon name="arrows-clockwise" /></template></Button></template>
    <template #filters>
      <Select v-model="filterMode" :options="filterModes" option-label="label" option-value="value" aria-label="Cakupan ringkasan" />
      <PeriodPicker v-if="filterMode === 'month'" v-model:bulan="month" v-model:tahun="year" />
      <Select v-else v-model="year" :options="years" aria-label="Tahun ringkasan" />
    </template>
    <Message v-if="failed.length" severity="warn" :closable="false" class="dashboard-error">Belum dapat memuat: {{ failed.join(', ') }}. Panel terkait ditandai di bawah; coba muat ulang.</Message>
    <p class="dashboard-scope" role="status">{{ loading ? 'Memuat ringkasan…' : `Ringkasan: ${appliedScope}` }}. Grafik dan daftar menyebut cakupannya masing-masing.</p>
    <div class="dashboard-summary">
      <section class="cash-position" aria-label="Kas dan bank">
        <span><Icon name="wallet" />Kas dan bank</span>
        <strong class="tabular-nums">{{ loading ? 'Memuat…' : rp(ringkasan?.kas) }}</strong>
        <p>{{ loading ? 'Memuat cakupan saldo…' : cashScope }}</p>
        <Button label="Buka laporan" text @click="router.push('/laporan')" />
      </section>
      <section class="journal-queue" :aria-label="principal ? 'Menunggu persetujuan' : 'Jurnal draf'">
        <header><h2>{{ principal ? 'Menunggu persetujuan' : 'Lanjutkan pencatatan' }}</h2><Button label="Buka jurnal" text @click="router.push('/jurnal')" /></header>
        <p>{{ principal ? 'Jurnal yang diajukan untuk ditinjau; transaksi milik sendiri tidak ditampilkan.' : 'Jurnal draf yang belum masuk buku besar.' }}</p>
        <p v-if="loading" role="status">Memuat jurnal…</p>
        <Message v-else-if="failed.includes('Jurnal yang perlu ditinjau')" severity="warn" :closable="false">Antrean belum berhasil dimuat.</Message>
        <ul v-else><li v-for="item in reviewQueue.slice(0, 3)" :key="item.id"><div><strong>{{ item.keterangan || item.no_bukti }}</strong><small>{{ item.no_bukti }} · {{ item.tanggal }}</small></div><Tag :value="principal ? 'Menunggu' : 'Draf'" :severity="principal ? 'warn' : 'secondary'" /></li><li v-if="!reviewQueue.length">{{ principal ? 'Tidak ada jurnal yang memenuhi syarat pada halaman ini.' : 'Tidak ada jurnal draf pada halaman ini.' }}</li></ul>
        <small v-if="!loading && !failed.includes('Jurnal yang perlu ditinjau')">{{ reviewQueue.length }} sesuai dari {{ queuePageCount }} jurnal pada halaman pertama; tampil maksimal 3.</small>
      </section>
    </div>
    <div class="dashboard-kpis"><KpiCard v-for="card in cards" :key="card.label" :label="card.label" :value="loading ? 'Memuat…' : card.value" :icon="card.icon" /></div>
    <Tabs value="overview" class="dashboard-analysis" scrollable>
      <template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template>
      <TabList :pt="{tabList:{'aria-label':'Analisis dashboard'},prevButton:{'aria-label':'Lihat tab analisis sebelumnya'},nextButton:{'aria-label':'Lihat tab analisis berikutnya'}}"><Tab value="overview">{{ principal ? 'Anggaran dan kegiatan' : 'Arus kas dan hasil usaha' }}</Tab><Tab value="accounts">Rincian akun</Tab><Tab value="activity">Transaksi terbaru</Tab></TabList>
      <TabPanels>
        <TabPanel value="overview">
          <div class="dashboard-charts" :class="{ 'principal-order': principal }">
            <ChartPanel title="Bagaimana kas bergerak?" :subtitle="`Tahun ${appliedYear} · rupiah · jurnal tercatat`" icon="chart-line" :loading="loading" :empty="!cash.length" :empty-text="failed.includes('Arus kas') ? 'Arus kas belum berhasil dimuat.' : 'Belum ada arus kas pada tahun ini.'">
              <div class="chart-wrap"><Chart type="line" :data="cashData" :options="lineOptions" :canvas-props="{ role: 'img', 'aria-label': 'Kas masuk, keluar, dan bersih. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="cashData.labels" :series="cashData.datasets" />
            </ChartPanel>
            <ChartPanel class="budget-panel" title="Bagaimana pagu dibanding realisasi?" :subtitle="`Tahun ${appliedYear} · rupiah · 5 akun dengan realisasi terbesar`" icon="chart-bar" :loading="loading" :empty="!budget.length" :empty-text="failed.includes('Anggaran') ? 'Anggaran belum berhasil dimuat.' : 'Belum ada anggaran pada tahun ini.'">
              <div class="chart-wrap"><Chart type="bar" :data="budgetData" :options="horizontalOptions" :canvas-props="{ role: 'img', 'aria-label': 'Pagu dan realisasi lima akun. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="budgetData.labels" :series="budgetData.datasets" />
            </ChartPanel>
            <ChartPanel title="Bagaimana pendapatan dibanding beban?" :subtitle="`Tahun ${appliedYear} · rupiah · per bulan`" icon="chart-bar" :loading="loading" :empty="!monthly?.data.length" :empty-text="failed.includes('Laba rugi bulanan') ? 'Laba rugi bulanan belum berhasil dimuat.' : 'Belum ada angka bulanan pada tahun ini.'">
              <div class="chart-wrap"><Chart type="bar" :data="monthlyData" :options="barOptions" :canvas-props="{ role: 'img', 'aria-label': 'Pendapatan dan beban per bulan. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="monthlyData.labels" :series="monthlyData.datasets" />
            </ChartPanel>
            <ChartPanel v-if="principal" title="Kegiatan yang perlu dipantau" subtitle="Halaman pertama daftar kegiatan · cakupan tahun pelajaran per kegiatan" icon="flag" :loading="loading" :empty="!activities.length" :empty-text="failed.includes('Kegiatan') ? 'Kegiatan belum berhasil dimuat.' : 'Belum ada kegiatan pada halaman ini.'">
              <template #action><Button label="Buka kegiatan" text @click="router.push('/kegiatan')" /></template>
              <ul class="activity-list"><li v-for="item in activities.slice(0, 5)" :key="item.id"><strong>{{ item.nama }}</strong><span>Pagu {{ rp(item.pagu) }} · realisasi {{ rp(item.realisasi) }}</span></li></ul>
            </ChartPanel>
          </div>
        </TabPanel>
        <TabPanel value="accounts"><div class="dashboard-charts"><ChartPanel title="Pendapatan per akun" :subtitle="appliedProfitScope" icon="arrow-down-left" :loading="loading" :empty="!incomeData.labels.length" :empty-text="failed.includes('Rincian pendapatan dan beban') ? 'Rincian belum berhasil dimuat.' : 'Belum ada pendapatan.'"><div class="chart-wrap"><Chart type="bar" :data="incomeData" :options="horizontalOptions" /></div><ChartDataTable :labels="incomeData.labels" :series="incomeData.datasets" /></ChartPanel><ChartPanel title="Beban per akun" :subtitle="appliedProfitScope" icon="arrow-up-right" :loading="loading" :empty="!expenseData.labels.length" :empty-text="failed.includes('Rincian pendapatan dan beban') ? 'Rincian belum berhasil dimuat.' : 'Belum ada beban.'"><div class="chart-wrap"><Chart type="bar" :data="expenseData" :options="horizontalOptions" /></div><ChartDataTable :labels="expenseData.labels" :series="expenseData.datasets" /></ChartPanel></div></TabPanel>
        <TabPanel value="activity">
          <div class="dashboard-charts">
            <ChartPanel title="Tagihan belum lunas" subtitle="5 tagihan dari halaman pertama berstatus belum lunas · periode pada tiap baris" icon="file-text" :loading="loading" :empty="!outstanding.length" :empty-text="failed.includes('Tagihan') ? 'Tagihan belum berhasil dimuat.' : 'Tidak ada tagihan pada halaman ini.'"><template #action><Button label="Lihat tagihan" text @click="router.push('/tunggakan-tagihan')" /></template><div class="dashboard-table-scroll" tabindex="0" role="region" aria-label="Tagihan belum lunas"><table><thead><tr><th>Siswa</th><th>Periode</th><th>Total tagihan</th></tr></thead><tbody><tr v-for="item in outstanding" :key="item.id"><td>{{ item.siswa_nama || `#${item.siswa}` }}</td><td>{{ months[item.periode_bulan - 1] }} {{ item.periode_tahun }}</td><td class="numeric">{{ rp(item.total) }}</td></tr></tbody></table></div></ChartPanel>
            <ChartPanel title="Jurnal tercatat terbaru" subtitle="5 jurnal dari halaman pertama · urutan tanggal terbaru" icon="book-open" :loading="loading" :empty="!recent.length" :empty-text="failed.includes('Jurnal tercatat') ? 'Jurnal belum berhasil dimuat.' : 'Belum ada jurnal tercatat pada halaman ini.'"><template #action><Button label="Buka jurnal" text @click="router.push('/jurnal')" /></template><ul class="activity-list"><li v-for="item in recent" :key="item.id"><strong>{{ item.no_bukti }}</strong><span>{{ item.tanggal }} · {{ item.keterangan || item.tipe_sumber }}</span><Tag value="Tercatat" severity="success" /></li></ul></ChartPanel>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </PageLayout>
</template>

<style scoped>
.dashboard-scope { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin: var(--bee-space-4) 0 var(--bee-space-5); }
.dashboard-error { margin-bottom: var(--bee-space-4); }
.dashboard-summary { display: grid; grid-template-columns: 1fr 1.25fr; gap: var(--bee-space-5); }
.cash-position { background: var(--bee-color-nav); color: var(--bee-color-nav-text); border-radius: var(--bee-radius-panel); padding: var(--bee-space-6); display: flex; flex-direction: column; align-items: flex-start; }
.cash-position > span { display: flex; align-items: center; gap: var(--bee-space-2); font-size: var(--bee-type-ui); }.cash-position > span .bee-icon { color: var(--bee-color-honey); }
.cash-position > strong { font-size: clamp(28px, 3vw, 44px); font-weight: 500; line-height: 1.2; margin-top: var(--bee-space-5); overflow-wrap: anywhere; }
.cash-position p { color: var(--bee-color-nav-muted); font-size: var(--bee-type-caption); margin-block: var(--bee-space-4); }.cash-position :deep(.p-button) { color: var(--bee-color-nav-text); margin-top: auto; }.cash-position :deep(.p-button:hover) { background: var(--bee-color-nav-border); }.cash-position :deep(.p-button:focus-visible) { outline-color: var(--bee-color-nav-text); }
.journal-queue { border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); padding: var(--bee-space-5); background: var(--app-surface); min-width: 0; }
.journal-queue header { display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-3); flex-wrap: wrap; }.journal-queue h2 { font-size: var(--bee-type-section); font-weight: 500; }.journal-queue p,.journal-queue > small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.journal-queue ul { list-style: none; padding: 0; margin-block: var(--bee-space-4); }.journal-queue li { display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-3); padding-block: var(--bee-space-3); border-bottom: 1px solid var(--app-border); }.journal-queue li strong,.journal-queue li small { display: block; }.journal-queue li strong { font-weight: 500; }.journal-queue li small { color: var(--app-text-muted); margin-top: var(--bee-space-1); }
.dashboard-kpis { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: var(--bee-space-5); margin-block: var(--bee-space-5) var(--bee-space-6); }
.dashboard-analysis { min-width: 0; }.dashboard-analysis :deep(.p-tabpanels) { padding: var(--bee-space-5) 0 0; background: transparent; }.dashboard-analysis :deep(.p-tablist-tab-list) { background: transparent; }
.dashboard-charts { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: var(--bee-space-5); }.principal-order .budget-panel { order: -1; }.chart-wrap { position: relative; height: 280px; }
.activity-list { list-style: none; padding: 0; margin: 0; }.activity-list li { display: flex; align-items: flex-start; flex-wrap: wrap; gap: var(--bee-space-2); padding-block: var(--bee-space-3); border-bottom: 1px solid var(--app-border); }.activity-list strong { font-weight: 500; width: 100%; }.activity-list span { font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.dashboard-table-scroll { overflow-x: auto; }table { width: 100%; border-collapse: collapse; font-size: var(--bee-type-ui); }th,td { padding: var(--bee-space-3); text-align: start; border-bottom: 1px solid var(--app-border); }th { font-size: var(--bee-type-caption); color: var(--app-text-muted); font-weight: 500; }.numeric { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
@media(max-width:1100px) { .dashboard-summary { grid-template-columns: minmax(0,1fr); } }
@media(max-width:767px) { .dashboard-kpis,.dashboard-charts { grid-template-columns: minmax(0,1fr); }.cash-position { padding: var(--bee-space-4); }.cash-position > strong { font-size: var(--bee-type-number-mobile); margin-top: var(--bee-space-3); }.cash-position p { margin-block: var(--bee-space-2); }.cash-position :deep(.p-button) { margin-top: var(--bee-space-1); }.journal-queue li { flex-wrap: wrap; }.dashboard-page :deep(.bee-page__header) { align-items: center; flex-wrap: nowrap; }.dashboard-page :deep(.bee-page__titles) { min-width: 0; }.dashboard-page :deep(.bee-page__actions) { flex: none; }.dashboard-page :deep(.bee-page__actions .p-button) { min-width: 44px; min-height: 44px; padding-inline: var(--bee-space-3); }.dashboard-page :deep(.bee-page__actions .p-button-label) { display: none; }.dashboard-page :deep(.bee-page__filters) { margin-bottom: var(--bee-space-3); }.dashboard-page :deep(.period-picker) { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); width: 100%; }.dashboard-page :deep(.period-picker .p-select) { min-width: 0; }.dashboard-scope { margin: var(--bee-space-3) 0; } }
</style>
