<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import Chart from "primevue/chart"
import Select from "primevue/select"
import DatePicker from "primevue/datepicker"
import Button from "primevue/button"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Tabs from "primevue/tabs"
import TabList from "primevue/tablist"
import Tab from "primevue/tab"
import TabPanels from "primevue/tabpanels"
import TabPanel from "primevue/tabpanel"
import type { ChartEvent, ActiveElement } from "chart.js"
import PageLayout from "@/shared/components/PageLayout.vue"
import ChartPanel from "@/shared/components/ChartPanel.vue"
import ChartDataTable from "@/shared/components/ChartDataTable.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { useAuthStore } from "@/stores/auth"
import { formatLocalDate, formatRp } from "@/core/format"
import { dashboardApi, type DashboardFilter } from "./api"
import { CHART, CHART_PALETTE, lineChartOptions, barChartOptions } from "./chartTheme"
import { dashboardMode, canReviewJurnal, defaultPeriode } from "./presentation"
import { jurnalApi } from "@/features/jurnal/api"
import { kegiatanApi } from "@/features/kegiatan/api"
import { laporanApi } from "@/features/laporan/api"
import { tagihanApi } from "@/features/tagihan/api"
import { periodeApi } from "@/features/anggaran-periode/api"
import type { DashboardRingkasan, Jurnal, Kegiatan, LabaRugiBulananResult, LabaRugiResult, PeriodeAkuntansi, PrediksiKasRow, RealisasiAnggaranRow, Tagihan } from "@/types/api"

type FilterMode = "day" | "month" | "period"
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
const periods = ref<PeriodeAkuntansi[]>([])
const filterMode = ref<FilterMode>("period")
const day = ref<Date | null>(new Date())
const month = ref(new Date().getMonth() + 1)
const year = ref(new Date().getFullYear())
const periodeId = ref<number | null>(null)
const appliedScope = ref("")
const chartScope = ref("")
const cashScope = ref("")
const appliedProfitScope = ref("")
let loadSequence = 0
let ready = false
const filterModes: { label: string; value: FilterMode; icon: string }[] = [
  { label: "Hari", value: "day", icon: "calendar-blank" },
  { label: "Bulan", value: "month", icon: "calendar-plus" },
  { label: "Periode", value: "period", icon: "graduation-cap" },
]
const periodOptions = computed(() => periods.value.map((row) => ({ ...row, label: `${row.kode}${row.status === "CLOSED" ? " · ditutup" : ""}` })))
const selectedPeriod = computed(() => periods.value.find((row) => row.id === periodeId.value) ?? null)
const params = computed((): DashboardFilter | null => {
  if (filterMode.value === "day") return day.value && Number.isFinite(day.value.getTime()) ? { tanggal: formatLocalDate(day.value) } : null
  if (filterMode.value === "period") return periodeId.value ? { periode: periodeId.value } : null
  return { tahun: year.value, bulan: month.value }
})
const rp = (value: string | number | null | undefined) => value == null ? "Belum diketahui" : formatRp(value)
const dateText = (iso: string) => iso.split("-").reverse().join("/")
const surplus = computed(() => Number(ringkasan.value?.surplus_defisit ?? 0))
const cards = computed(() => [
  { label: "Pendapatan", value: rp(ringkasan.value?.total_pendapatan), icon: "arrow-down-left", tone: "green" as const, hint: "Akun 4 · jurnal tercatat", to: { path: "/jurnal", query: { jenis: "masuk" } } },
  { label: "Beban", value: rp(ringkasan.value?.total_beban), icon: "arrow-up-right", tone: "magenta" as const, hint: "Akun 5 · jurnal tercatat", to: { path: "/jurnal", query: { jenis: "keluar" } } },
  { label: surplus.value < 0 ? "Defisit" : "Surplus", value: rp(ringkasan.value?.surplus_defisit), icon: "chart-line", tone: surplus.value < 0 ? "red" as const : "blue" as const, hint: "Pendapatan dikurangi beban", to: "/laporan" },
])
const ops = computed(() => ringkasan.value?.operasional)
const sparkMax = computed(() => Math.max(1, ...(ops.value?.absensi_sparkline ?? []).map((row) => row.hadir)))
const reviewQueue = computed(() => principal.value ? queue.value.filter((item) => canReviewJurnal(item, auth.user?.id)) : queue.value)
const budgetTop = computed(() => [...budget.value].sort((a, b) => Number(b.realisasi) - Number(a.realisasi)).slice(0, 5))
const multiYear = computed(() => new Set((monthly.value?.data ?? []).map((row) => row.tahun)).size > 1 || new Set(cash.value.map((row) => row.tahun)).size > 1)
const monthLabel = (bulan: number, tahun?: number) => multiYear.value && tahun ? `${months[bulan - 1]} ${String(tahun).slice(2)}` : months[bulan - 1]!
const cashData = computed(() => ({ labels: cash.value.map((row) => `${months[row.bulan - 1]} ${row.tahun}`), datasets: [
  { label: "Kas masuk", data: cash.value.map((row) => Number(row.arus_kas_masuk)), borderColor: CHART.green, backgroundColor: `${CHART.green}22`, fill: true, tension: 0.35, pointRadius: 3, pointHoverRadius: 6 },
  { label: "Kas keluar", data: cash.value.map((row) => Number(row.arus_kas_keluar)), borderColor: CHART.magenta, backgroundColor: `${CHART.magenta}18`, fill: true, tension: 0.35, pointRadius: 3, pointHoverRadius: 6 },
  { label: "Arus kas bersih", data: cash.value.map((row) => Number(row.net_cash_flow_bulanan)), borderColor: CHART.blue, backgroundColor: CHART.blue, borderDash: [5, 4], tension: 0.35, pointRadius: 3, pointHoverRadius: 6 },
] }))
const monthlyData = computed(() => ({ labels: (monthly.value?.data ?? []).map((row) => monthLabel(row.bulan, row.tahun)), datasets: [
  { label: "Pendapatan", data: (monthly.value?.data ?? []).map((row) => row.pendapatan), backgroundColor: CHART.green, hoverBackgroundColor: CHART.navy, borderRadius: 6 },
  { label: "Beban", data: (monthly.value?.data ?? []).map((row) => row.beban), backgroundColor: CHART.magenta, hoverBackgroundColor: CHART.navy, borderRadius: 6 },
] }))
const budgetData = computed(() => ({ labels: budgetTop.value.map((row) => `${row.kode_akun} ${row.nama_akun}`), datasets: [
  { label: "Pagu", data: budgetTop.value.map((row) => Number(row.pagu)), backgroundColor: CHART.cream, borderColor: CHART.navy, borderWidth: 1, borderRadius: 6 },
  { label: "Realisasi", data: budgetTop.value.map((row) => Number(row.realisasi)), backgroundColor: budgetTop.value.map((row) => Number(row.realisasi) > Number(row.pagu) ? CHART.magenta : CHART.blue), borderRadius: 6 },
] }))
const incomeData = computed(() => ({ labels: (labaRugi.value?.pendapatan ?? []).map((row) => row.nama_akun), datasets: [{ label: "Pendapatan", data: (labaRugi.value?.pendapatan ?? []).map((row) => Number(row.saldo_akhir)), backgroundColor: CHART_PALETTE, borderRadius: 6 }] }))
const expenseData = computed(() => ({ labels: (labaRugi.value?.beban ?? []).map((row) => row.nama_akun), datasets: [{ label: "Beban", data: (labaRugi.value?.beban ?? []).map((row) => Number(row.saldo_akhir)), backgroundColor: CHART_PALETTE, borderRadius: 6 }] }))
const lineOptions = lineChartOptions(true)
// Klik batang bulan untuk melihat ringkasan bulan itu.
const barOptions = {
  ...barChartOptions(),
  onClick: (_event: ChartEvent, elements: ActiveElement[]) => {
    const row = monthly.value?.data[elements[0]?.index ?? -1]
    if (!row) return
    year.value = row.tahun ?? monthly.value!.tahun
    month.value = row.bulan
    filterMode.value = "month"
  },
  onHover: (event: ChartEvent, elements: ActiveElement[]) => {
    const target = event.native?.target as HTMLElement | undefined
    if (target) target.style.cursor = elements.length ? "pointer" : "default"
  },
}
const horizontalOptions = barChartOptions({ horizontal: true })

function scopeLabel(scope: DashboardFilter) {
  if (scope.tanggal) return dateText(scope.tanggal)
  if (scope.periode) return selectedPeriod.value ? `Periode ${selectedPeriod.value.kode} (${dateText(selectedPeriod.value.tgl_mulai)} – ${dateText(selectedPeriod.value.tgl_selesai)})` : "Periode terpilih"
  return `${months[scope.bulan! - 1]} ${scope.tahun}`
}

async function loadDashboard() {
  const scope = params.value
  if (!scope) return
  const sequence = ++loadSequence
  loading.value = true
  const chartYear = scope.tanggal ? Number(scope.tanggal.slice(0, 4)) : scope.periode ? (selectedPeriod.value ? Number(selectedPeriod.value.tgl_mulai.slice(0, 4)) : year.value) : scope.tahun!
  const series = scope.periode ? { periode: scope.periode } : chartYear
  const currentMode = mode.value
  const result = await Promise.allSettled([
    dashboardApi.ringkasan(scope),
    laporanApi.labaRugi(scope),
    dashboardApi.prediksiKas(series), dashboardApi.labaRugiBulanan(series), laporanApi.realisasiAnggaran(chartYear),
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
  const label = scopeLabel(scope)
  cashScope.value = `Saldo kumulatif hingga akhir ${label}.`
  appliedProfitScope.value = label
  chartScope.value = scope.periode ? `Periode ${selectedPeriod.value?.kode ?? ""}`.trim() : `Tahun ${chartYear}`
  appliedScope.value = label
  loading.value = false
}
async function loadPeriods() {
  try {
    periods.value = await periodeApi.listAll()
  } catch {
    periods.value = []
  }
  periodeId.value = defaultPeriode(periods.value, formatLocalDate(new Date()))?.id ?? null
  if (!periodeId.value) filterMode.value = "month"
}
watch([filterMode, day, month, year, periodeId, mode], () => { if (ready && auth.isAuthenticated) void loadDashboard() })
onMounted(async () => { await loadPeriods(); await nextTick(); ready = true; await loadDashboard() })
</script>

<template>
  <PageLayout class="dashboard-page" :title="principal ? 'Ikhtisar sekolah' : 'Ringkasan keuangan'" :subtitle="principal ? 'Keputusan, kondisi keuangan, dan kegiatan sekolah.' : 'Kas, pencatatan, dan tindak lanjut transaksi.'" :surface="false">
    <template #actions><Button label="Muat ulang" aria-label="Muat ulang dashboard" severity="secondary" :loading="loading" @click="loadDashboard"><template #icon><Icon name="arrows-clockwise" /></template></Button></template>
    <template #filters>
      <div class="dashboard-mode" role="group" aria-label="Cakupan ringkasan"><button v-for="item in filterModes" :key="item.value" type="button" :aria-pressed="filterMode === item.value" :disabled="item.value === 'period' && !periods.length" @click="filterMode = item.value"><Icon :name="item.icon" />{{ item.label }}</button></div>
      <DatePicker v-if="filterMode === 'day'" v-model="day" input-id="dashboard-day" date-format="dd/mm/yy" :max-date="new Date()" show-icon icon-display="input" aria-label="Tanggal ringkasan" class="dashboard-day"><template #inputicon="{ clickCallback }"><Icon name="calendar-blank" @click="clickCallback" /></template><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker>
      <PeriodPicker v-else-if="filterMode === 'month'" v-model:bulan="month" v-model:tahun="year" />
      <Select v-else v-model="periodeId" :options="periodOptions" option-label="label" option-value="id" aria-label="Periode tahun ajaran" class="dashboard-period"><template #dropdownicon><Icon name="caret-down" /></template></Select>
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
    <div class="dashboard-kpis"><KpiCard v-for="card in cards" :key="card.label" :label="card.label" :value="loading ? 'Memuat…' : card.value" :icon="card.icon" :tone="card.tone" :hint="card.hint" :to="card.to" /></div>
    <div v-if="ops || loading" class="dashboard-ops" aria-label="Operasional sekolah">
      <KpiCard label="Siswa aktif" :value="loading ? 'Memuat…' : String(ops?.siswa_aktif ?? 0)" icon="student" tone="blue" hint="Seluruh siswa berstatus aktif" />
      <KpiCard label="Catatan hadir siswa" :value="loading ? 'Memuat…' : String(ops?.hadir_bulan_ini ?? 0)" icon="calendar-plus" tone="gold" :hint="loading ? '' : `${ops?.katering_bulan_ini ?? 0} ikut katering · ${appliedScope}`">
        <div v-if="!loading && ops?.absensi_sparkline?.length" class="dashboard-spark" role="img" :aria-label="`Catatan hadir: ${ops.absensi_sparkline.map((row) => `${row.label} ${row.hadir}`).join(', ')}`"><span v-for="row in ops.absensi_sparkline" :key="row.label" :title="`${row.label}: ${row.hadir} hadir`" :style="{ height: `${Math.max(8, row.hadir / sparkMax * 100)}%` }" /></div>
      </KpiCard>
      <KpiCard label="Tagihan belum lunas" :value="loading ? 'Memuat…' : rp(ops?.tagihan_belum_nominal)" icon="file-text" tone="orange" :hint="loading ? '' : `${ops?.tagihan_belum ?? 0} tagihan pada cakupan ini`" to="/tunggakan-tagihan" />
      <KpiCard label="Tingkat pelunasan" :value="loading ? 'Memuat…' : `${ops?.collection_rate_pct ?? 0}%`" icon="check-circle" tone="green" :progress="loading ? null : ops?.collection_rate_pct ?? 0" hint="Tagihan lunas dibanding seluruh tagihan" />
    </div>
    <Tabs value="overview" class="dashboard-analysis" scrollable>
      <template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template>
      <TabList :pt="{tabList:{'aria-label':'Analisis dashboard'},prevButton:{'aria-label':'Lihat tab analisis sebelumnya'},nextButton:{'aria-label':'Lihat tab analisis berikutnya'}}"><Tab value="overview">{{ principal ? 'Anggaran dan kegiatan' : 'Arus kas dan hasil usaha' }}</Tab><Tab value="accounts">Rincian akun</Tab><Tab value="activity">Transaksi terbaru</Tab></TabList>
      <TabPanels>
        <TabPanel value="overview">
          <div class="dashboard-charts" :class="{ 'principal-order': principal }">
            <ChartPanel title="Bagaimana kas bergerak?" :subtitle="`${chartScope} · rupiah · jurnal tercatat`" icon="chart-line" accent="green" :loading="loading" :empty="!cash.length" :empty-text="failed.includes('Arus kas') ? 'Arus kas belum berhasil dimuat.' : 'Belum ada arus kas pada tahun ini.'">
              <div class="chart-wrap"><Chart type="line" :data="cashData" :options="lineOptions" :canvas-props="{ role: 'img', 'aria-label': 'Kas masuk, keluar, dan bersih. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="cashData.labels" :series="cashData.datasets" />
            </ChartPanel>
            <ChartPanel class="budget-panel" title="Bagaimana pagu dibanding realisasi?" :subtitle="`Tahun anggaran ${chartScope.replace('Tahun ', '')} · rupiah · 5 akun dengan realisasi terbesar · merah = melewati pagu`" icon="chart-bar" accent="blue" :loading="loading" :empty="!budget.length" :empty-text="failed.includes('Anggaran') ? 'Anggaran belum berhasil dimuat.' : 'Belum ada anggaran pada tahun ini.'">
              <div class="chart-wrap"><Chart type="bar" :data="budgetData" :options="horizontalOptions" :canvas-props="{ role: 'img', 'aria-label': 'Pagu dan realisasi lima akun. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="budgetData.labels" :series="budgetData.datasets" />
            </ChartPanel>
            <ChartPanel title="Bagaimana pendapatan dibanding beban?" :subtitle="`${chartScope} · rupiah · per bulan · klik batang untuk melihat bulan itu`" icon="chart-bar" accent="magenta" :loading="loading" :empty="!monthly?.data.length" :empty-text="failed.includes('Laba rugi bulanan') ? 'Laba rugi bulanan belum berhasil dimuat.' : 'Belum ada angka bulanan pada tahun ini.'">
              <div class="chart-wrap"><Chart type="bar" :data="monthlyData" :options="barOptions" :canvas-props="{ role: 'img', 'aria-label': 'Pendapatan dan beban per bulan. Angka tersedia pada tabel berikut.' }" /></div><ChartDataTable :labels="monthlyData.labels" :series="monthlyData.datasets" />
            </ChartPanel>
            <ChartPanel v-if="principal" title="Kegiatan yang perlu dipantau" subtitle="Halaman pertama daftar kegiatan · cakupan tahun pelajaran per kegiatan" icon="flag" accent="orange" :loading="loading" :empty="!activities.length" :empty-text="failed.includes('Kegiatan') ? 'Kegiatan belum berhasil dimuat.' : 'Belum ada kegiatan pada halaman ini.'">
              <template #action><Button label="Buka kegiatan" text @click="router.push('/kegiatan')" /></template>
              <ul class="activity-list"><li v-for="item in activities.slice(0, 5)" :key="item.id"><strong>{{ item.nama }}</strong><span>Pagu {{ rp(item.pagu) }} · realisasi {{ rp(item.realisasi) }}</span><span class="activity-meter" :class="{ over: Number(item.realisasi) > Number(item.pagu) }" role="progressbar" :aria-valuenow="Number(item.pagu) ? Math.round(Number(item.realisasi) / Number(item.pagu) * 100) : 0" aria-valuemin="0" aria-valuemax="100" :aria-label="`Serapan ${item.nama}`"><i :style="{ width: `${Number(item.pagu) ? Math.min(100, Number(item.realisasi) / Number(item.pagu) * 100) : 0}%` }" /></span></li></ul>
            </ChartPanel>
          </div>
        </TabPanel>
        <TabPanel value="accounts"><div class="dashboard-charts"><ChartPanel title="Pendapatan per akun" :subtitle="appliedProfitScope" icon="arrow-down-left" accent="green" :loading="loading" :empty="!incomeData.labels.length" :empty-text="failed.includes('Rincian pendapatan dan beban') ? 'Rincian belum berhasil dimuat.' : 'Belum ada pendapatan.'"><div class="chart-wrap"><Chart type="bar" :data="incomeData" :options="horizontalOptions" /></div><ChartDataTable :labels="incomeData.labels" :series="incomeData.datasets" /></ChartPanel><ChartPanel title="Beban per akun" :subtitle="appliedProfitScope" icon="arrow-up-right" accent="magenta" :loading="loading" :empty="!expenseData.labels.length" :empty-text="failed.includes('Rincian pendapatan dan beban') ? 'Rincian belum berhasil dimuat.' : 'Belum ada beban.'"><div class="chart-wrap"><Chart type="bar" :data="expenseData" :options="horizontalOptions" /></div><ChartDataTable :labels="expenseData.labels" :series="expenseData.datasets" /></ChartPanel></div></TabPanel>
        <TabPanel value="activity">
          <div class="dashboard-charts">
            <ChartPanel title="Tagihan belum lunas" subtitle="5 tagihan dari halaman pertama berstatus belum lunas · periode pada tiap baris" icon="file-text" accent="orange" :loading="loading" :empty="!outstanding.length" :empty-text="failed.includes('Tagihan') ? 'Tagihan belum berhasil dimuat.' : 'Tidak ada tagihan pada halaman ini.'"><template #action><Button label="Lihat tagihan" text @click="router.push('/tunggakan-tagihan')" /></template><div class="dashboard-table-scroll" tabindex="0" role="region" aria-label="Tagihan belum lunas"><table><thead><tr><th>Siswa</th><th>Periode</th><th>Total tagihan</th></tr></thead><tbody><tr v-for="item in outstanding" :key="item.id"><td>{{ item.siswa_nama || `#${item.siswa}` }}</td><td>{{ months[item.periode_bulan - 1] }} {{ item.periode_tahun }}</td><td class="numeric">{{ rp(item.total) }}</td></tr></tbody></table></div></ChartPanel>
            <ChartPanel title="Jurnal tercatat terbaru" subtitle="5 jurnal dari halaman pertama · urutan tanggal terbaru" icon="book-open" accent="blue" :loading="loading" :empty="!recent.length" :empty-text="failed.includes('Jurnal tercatat') ? 'Jurnal belum berhasil dimuat.' : 'Belum ada jurnal tercatat pada halaman ini.'"><template #action><Button label="Buka jurnal" text @click="router.push('/jurnal')" /></template><ul class="activity-list"><li v-for="item in recent" :key="item.id"><strong>{{ item.no_bukti }}</strong><span>{{ item.tanggal }} · {{ item.keterangan || item.tipe_sumber }}</span><Tag value="Tercatat" severity="success" /></li></ul></ChartPanel>
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
.dashboard-mode { display: inline-flex; padding: 3px; gap: 2px; border-radius: 12px; background: var(--bee-color-neutral-tint); }
.dashboard-mode button { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 40px; padding: 0 var(--bee-space-4); border: 0; border-radius: 9px; background: transparent; color: var(--app-text-muted); font: inherit; font-size: var(--bee-type-ui); cursor: pointer; transition: background .16s ease, color .16s ease; }
.dashboard-mode button .bee-icon { width: 16px; height: 16px; }
.dashboard-mode button[aria-pressed=true] { background: var(--app-surface); color: var(--bee-color-brand); font-weight: 600; box-shadow: 0 1px 3px rgb(32 36 61 / 12%); }
.dashboard-mode button:hover:not([aria-pressed=true]):not(:disabled) { color: var(--app-text); }
.dashboard-mode button:disabled { opacity: .5; cursor: default; }
.dashboard-mode button:focus-visible { outline: 2px solid var(--bee-color-focus); outline-offset: 1px; }
.dashboard-period { min-width: 220px; }
.dashboard-ops { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: var(--bee-space-5); margin-bottom: var(--bee-space-6); }
.dashboard-spark { display: flex; align-items: flex-end; gap: 4px; height: 32px; margin-top: var(--bee-space-3); }
.dashboard-spark span { flex: 1; border-radius: 3px 3px 0 0; background: var(--bee-color-honey); opacity: .55; transition: opacity .16s ease; }
.dashboard-spark span:last-child, .dashboard-spark span:hover { opacity: 1; }
.activity-meter { display: block; width: 100%; height: 6px; border-radius: 999px; background: var(--bee-color-info-tint); overflow: hidden; }
.activity-meter i { display: block; height: 100%; border-radius: inherit; background: var(--bee-color-info); }
.activity-meter.over i { background: var(--bee-color-critical); }
.cash-position { background: linear-gradient(135deg, var(--bee-color-nav) 0%, var(--bee-color-chart-ink) 60%, var(--bee-color-brand-active) 140%); color: var(--bee-color-nav-text); border-radius: var(--bee-radius-panel); padding: var(--bee-space-6); display: flex; flex-direction: column; align-items: flex-start; }
.cash-position > span { display: flex; align-items: center; gap: var(--bee-space-2); font-size: var(--bee-type-ui); }.cash-position > span .bee-icon { color: var(--bee-color-honey); }
.cash-position > strong { font-size: clamp(28px, 3vw, 44px); font-weight: 500; line-height: 1.2; margin-top: var(--bee-space-5); overflow-wrap: anywhere; }
.cash-position p { color: var(--bee-color-nav-muted); font-size: var(--bee-type-caption); margin-block: var(--bee-space-4); }.cash-position :deep(.p-button) { color: var(--bee-color-nav-text); margin-top: auto; }.cash-position :deep(.p-button:hover) { background: var(--bee-color-nav-border); }.cash-position :deep(.p-button:focus-visible) { outline-color: var(--bee-color-nav-text); }
.journal-queue { border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); padding: var(--bee-space-5); background: var(--app-surface); min-width: 0; }
.journal-queue header { display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-3); flex-wrap: wrap; }.journal-queue h2 { font-size: var(--bee-type-section); font-weight: 500; }.journal-queue p,.journal-queue > small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.journal-queue ul { list-style: none; padding: 0; margin-block: var(--bee-space-4); }.journal-queue li { display: flex; align-items: center; justify-content: space-between; gap: var(--bee-space-3); padding-block: var(--bee-space-3); border-bottom: 1px solid var(--app-border); }.journal-queue li strong,.journal-queue li small { display: block; }.journal-queue li strong { font-weight: 500; }.journal-queue li small { color: var(--app-text-muted); margin-top: var(--bee-space-1); }
.dashboard-kpis { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: var(--bee-space-5); margin-block: var(--bee-space-5); }
.dashboard-analysis { min-width: 0; }.dashboard-analysis :deep(.p-tabpanels) { padding: var(--bee-space-5) 0 0; background: transparent; }.dashboard-analysis :deep(.p-tablist-tab-list) { background: transparent; }
.dashboard-charts { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: var(--bee-space-5); }.principal-order .budget-panel { order: -1; }.chart-wrap { position: relative; height: 280px; }
.activity-list { list-style: none; padding: 0; margin: 0; }.activity-list li { display: flex; align-items: flex-start; flex-wrap: wrap; gap: var(--bee-space-2); padding-block: var(--bee-space-3); border-bottom: 1px solid var(--app-border); }.activity-list strong { font-weight: 500; width: 100%; }.activity-list span { font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.dashboard-table-scroll { overflow-x: auto; }table { width: 100%; border-collapse: collapse; font-size: var(--bee-type-ui); }th,td { padding: var(--bee-space-3); text-align: start; border-bottom: 1px solid var(--app-border); }th { font-size: var(--bee-type-caption); color: var(--app-text-muted); font-weight: 500; }.numeric { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
@media(max-width:1100px) { .dashboard-summary { grid-template-columns: minmax(0,1fr); }.dashboard-ops { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media(max-width:767px) { .dashboard-kpis,.dashboard-charts { grid-template-columns: minmax(0,1fr); }.dashboard-ops { gap: var(--bee-space-3); }.dashboard-mode { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); width: 100%; }.dashboard-mode button { justify-content: center; min-height: 44px; padding-inline: var(--bee-space-2); }.dashboard-period,.dashboard-day { width: 100%; min-width: 0; }.cash-position { padding: var(--bee-space-4); }.cash-position > strong { font-size: var(--bee-type-number-mobile); margin-top: var(--bee-space-3); }.cash-position p { margin-block: var(--bee-space-2); }.cash-position :deep(.p-button) { margin-top: var(--bee-space-1); }.journal-queue li { flex-wrap: wrap; }.dashboard-page :deep(.bee-page__header) { align-items: center; flex-wrap: nowrap; }.dashboard-page :deep(.bee-page__titles) { min-width: 0; }.dashboard-page :deep(.bee-page__actions) { flex: none; }.dashboard-page :deep(.bee-page__actions .p-button) { min-width: 44px; min-height: 44px; padding-inline: var(--bee-space-3); }.dashboard-page :deep(.bee-page__actions .p-button-label) { display: none; }.dashboard-page :deep(.bee-page__filters) { margin-bottom: var(--bee-space-3); }.dashboard-page :deep(.period-picker) { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); width: 100%; }.dashboard-page :deep(.period-picker .p-select) { min-width: 0; }.dashboard-scope { margin: var(--bee-space-3) 0; } }
@media(max-width:520px) { .dashboard-ops { grid-template-columns: minmax(0,1fr); } }
</style>
