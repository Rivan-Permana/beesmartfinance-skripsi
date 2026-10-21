<script setup lang="ts">
import { computed, ref } from "vue"
import Drawer from "primevue/drawer"
import Dialog from "primevue/dialog"
import type { ChartData, ChartOptions } from "chart.js"
import type { Role } from "@/types/api"
import { navForRoles, roleHome } from "@/core/navigation"
import { formatRp } from "@/core/format"
import Icon from "./PhosphorIcon.vue"
import ChartCard from "./PreviewChart.vue"
import JournalPreview from "./JournalPreview.vue"
import BillingPreview from "./BillingPreview.vue"
import { roles, navigationGroupOrder, screenInfo, months, monthly, incomeParts, expenseParts, annualBudget, students, bills, journals, approvals, activities } from "./fixtures"

const params = new URLSearchParams(location.search)
const role = roles.find((r) => r.value === params.get("role")) ?? roles[0]!
const isPrincipal = role.value === "SchoolPrincipal"
const isFinance = role.value === "Finance"
const isTeacher = role.value === "TeacherInCharge"
const navItems = navForRoles([role.value]).map((n) => {
  const path = n.query?.jenis ? `${n.to}?jenis=${n.query.jenis}` : n.to
  return { ...screenInfo[path]!, path }
})
const allowed = [...navItems.map((n) => n.path), ...(isFinance || isPrincipal ? ["/jurnal"] : [])]
const requested = params.get("screen") ?? roleHome([role.value])
const screen = allowed.includes(requested) ? requested : roleHome([role.value])
const page = screenInfo[screen]!
const groups = navigationGroupOrder[role.value].filter((group) => navItems.some((item) => item.group === group))
const supported = new Set(["/dashboard", "/siswa", "/kegiatan", "/tagihan", "/tunggakan-tagihan", "/jurnal", "/jurnal?jenis=masuk", "/jurnal?jenis=keluar", "/rekap-siswa"])
const state = ref<"normal" | "empty" | "error" | "loading">("normal")
const mobileOpen = ref(false)
const mobileTrigger = ref<HTMLButtonElement | null>(null)
const query = ref("")
const status = ref("")
const analysis = ref<"cash" | "profit">("cash")
const composition = ref<"income" | "expense">("expense")
const detail = ref<{ title: string; text: string } | null>(null)
const dialogVisible = computed({ get: () => !!detail.value, set: (value) => { if (!value) detail.value = null } })
const isJournal = screen.startsWith("/jurnal")
const isBills = screen === "/tagihan" || screen === "/tunggakan-tagihan"
const filteredStudents = computed(() => students.filter((s) => (!status.value || s.status === status.value) && `${s.name} ${s.id} ${s.group}`.toLocaleLowerCase("id").includes(query.value.toLocaleLowerCase("id"))))
const knownOutstanding = bills.reduce((sum, bill) => sum + (bill.remaining ?? 0), 0)
const unmatchedBills = bills.filter((bill) => bill.remaining === null).length
const activityBudget = activities.reduce((sum, activity) => sum + activity.pagu, 0)
const activityActual = activities.reduce((sum, activity) => sum + activity.realisasi, 0)
const budgetTotal = annualBudget.pagu.reduce((sum, value) => sum + value, 0)
const budgetActual = annualBudget.realisasi.reduce((sum, value) => sum + value, 0)
const budgetPercent = Math.round(budgetActual / budgetTotal * 100)
const colors = { navy: "#2e2a6e", brand: "#b51268", green: "#19765b", amber: "#c38b32", teal: "#2d8c83", grid: "#edf0f5" }
const palette = [colors.navy, colors.brand, colors.teal, colors.amber]
const cartesian: ChartOptions = {
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: "#637087", font: { family: "Nunito Sans", size: 12 } } },
    y: { beginAtZero: true, grid: { color: colors.grid }, border: { display: false }, ticks: { color: "#637087", maxTicksLimit: 5, callback: (v) => `${Number(v) / 1_000_000} jt` } },
  },
}
const cashData: ChartData = { labels: months, datasets: [
  { label: "Kas masuk", data: monthly.cashIn, borderColor: colors.green, backgroundColor: "#19765b0c", fill: true, tension: 0, borderWidth: 3, pointBackgroundColor: colors.green, pointRadius: 3, pointHoverRadius: 6 },
  { label: "Kas keluar", data: monthly.cashOut, borderColor: colors.brand, backgroundColor: colors.brand, tension: 0, borderWidth: 3, pointRadius: 3, pointHoverRadius: 6 },
] }
const profitData: ChartData = { labels: months, datasets: [
  { label: "Pendapatan", data: monthly.income, backgroundColor: colors.navy, borderRadius: 3, maxBarThickness: 22 },
  { label: "Beban", data: monthly.expense, backgroundColor: "#bd6d96", borderRadius: 3, maxBarThickness: 22 },
] }
const compositionData = computed<ChartData>(() => {
  const parts = composition.value === "income" ? incomeParts : expenseParts
  return { labels: parts.map((p) => p.label), datasets: [{ label: composition.value === "income" ? "Pendapatan" : "Beban", data: parts.map((p) => p.value), backgroundColor: palette, borderWidth: 3, borderColor: "#ffffff" }] }
})
const budgetData: ChartData = { labels: annualBudget.labels, datasets: [
  { label: "Pagu", data: annualBudget.pagu, backgroundColor: "#e9e8f2", borderRadius: 3, maxBarThickness: 16 },
  { label: "Realisasi", data: annualBudget.realisasi, backgroundColor: colors.navy, borderRadius: 3, maxBarThickness: 16 },
] }
const horizontal: ChartOptions = { indexAxis: "y", scales: {
  x: { beginAtZero: true, grid: { color: colors.grid }, border: { display: false }, ticks: { maxTicksLimit: 4, color: "#637087", callback: (v) => `${Number(v) / 1_000_000} jt` } },
  y: { grid: { display: false }, border: { display: false }, ticks: { color: "#56647b", font: { family: "Nunito Sans", size: 12 } } },
} }
const attendanceData: ChartData = { labels: months, datasets: [{ label: "Kehadiran tercatat", data: [1035, 1120, 960, 1210, 1150, 1080], backgroundColor: colors.teal, borderRadius: 4, maxBarThickness: 28 }] }
const attendanceOptions: ChartOptions = { scales: {
  x: cartesian.scales?.x,
  y: { beginAtZero: true, grid: { color: colors.grid }, border: { display: false }, ticks: { maxTicksLimit: 5, color: "#637087" } },
} }
const activityData: ChartData = { labels: activities.map((a) => a.title), datasets: [
  { label: "Pagu", data: activities.map((a) => a.pagu), backgroundColor: "#e9e8f2", borderRadius: 3, maxBarThickness: 17 },
  { label: "Realisasi", data: activities.map((a) => a.realisasi), backgroundColor: colors.teal, borderRadius: 3, maxBarThickness: 17 },
] }

function href(path: string, nextRole: Role = role.value) {
  return `?${new URLSearchParams({ role: nextRole, screen: path })}`
}
function journalHref(code: string) { return `${href('/jurnal')}&entry=${encodeURIComponent(code)}` }
function changeRole(event: Event) {
  const next = (event.target as HTMLSelectElement).value as Role
  location.href = href(roleHome([next]), next)
}
function resetFilters() { query.value = ""; status.value = "" }
function showDetail(title: string, text: string) { detail.value = { title, text } }
</script>

<template>
  <a class="skip-link" href="#main">Langsung ke isi</a>
  <div class="preview-bar"><span><Icon name="eye" /><strong>Pratinjau desain</strong><span class="preview-explanation">Data contoh, tanpa transaksi nyata.</span></span><div class="preview-controls"><label for="preview-role">Peran</label><select id="preview-role" :value="role.value" @change="changeRole"><option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option></select><label for="preview-state">Tampilan</label><select id="preview-state" v-model="state"><option value="normal">Berisi data</option><option value="empty">Kosong</option><option value="error">Gagal dimuat</option><option value="loading">Memuat</option></select></div></div>
  <div class="app-shell workspace-theme">
    <aside class="sidebar"><a class="school-brand" :href="href(roleHome([role.value]))"><img src="/logo-lebah.svg" alt=""><div><strong>Lebah Madu</strong><small>BeeSmart Finance</small></div></a><nav aria-label="Navigasi utama"><section v-for="group in groups" :key="group" class="nav-group"><h2>{{ group }}</h2><template v-for="item in navItems.filter((n) => n.group === group)" :key="item.path"><a v-if="supported.has(item.path)" :href="href(item.path)" class="nav-item" :aria-current="screen === item.path ? 'page' : undefined"><Icon :name="item.icon" />{{ item.label }}</a><span v-else class="nav-item nav-item--pending" :title="`${item.label}: belum dibuat pada pratinjau ini`"><Icon :name="item.icon" />{{ item.label }}<span class="sr-only">, belum tersedia dalam pratinjau</span></span></template></section></nav><div class="school"><Icon name="buildings" /><div><strong>Sekolah Lebah Madu</strong><small>{{ role.label }}</small></div></div></aside>
    <div class="workspace"><header class="topbar"><div class="topbar-context"><button ref="mobileTrigger" class="icon-button mobile-menu" type="button" aria-label="Buka menu navigasi" @click="mobileOpen = true"><Icon name="list" /></button><span v-if="page.group !== page.label">{{ page.group }}</span><Icon v-if="page.group !== page.label" name="caret-right" /><strong>{{ page.label }}</strong></div><div class="identity"><div><strong>{{ role.label }}</strong><small>Ruang kerja sekolah</small></div><span class="avatar" aria-hidden="true">{{ role.short }}</span></div></header>
      <main id="main">
        <header class="page-heading"><div><h1>{{ screen === '/dashboard' ? isPrincipal ? 'Ikhtisar sekolah' : 'Ringkasan keuangan' : page.label }}</h1><p>{{ screen === '/dashboard' ? isPrincipal ? 'Keputusan yang menunggu, kondisi keuangan, dan penggunaan anggaran.' : 'Posisi kas dan pekerjaan pencatatan Oktober 2026.' : screen === '/rekap-siswa' ? 'Baca catatan kehadiran siswa per bulan.' : isTeacher ? 'Periksa pagu, realisasi, dan rincian kegiatan sekolah.' : screen === '/siswa' ? 'Kelola profil, kelompok, dan status siswa.' : isBills ? 'Periksa rincian, pembayaran, dan sisa tagihan siswa.' : isJournal ? isPrincipal ? 'Tinjau jurnal yang diajukan dan periksa pencatatan sekolah.' : 'Periksa transaksi, lengkapi draf, dan lanjutkan pencatatan.' : 'Informasi sekolah sesuai akses peran.' }}</p></div><div v-if="!isJournal" class="period-label"><Icon :name="screen === '/siswa' ? 'student' : 'calendar-blank'" />{{ screen === '/siswa' ? 'Data contoh' : screen === '/kegiatan' ? 'Tahun 2026' : 'Oktober 2026' }}</div><a v-if="isFinance && screen === '/dashboard'" class="button heading-action" :href="href('/jurnal')"><Icon name="book-open" />Buka jurnal</a></header>

        <div v-if="state === 'loading'" class="loading-state" role="status"><span class="sr-only">Memuat contoh tampilan</span><div class="skeleton skeleton--metrics"/><div class="skeleton skeleton--chart"/><button class="button secondary" @click="state = 'normal'">Selesaikan simulasi memuat</button></div>
        <section v-else-if="state === 'empty' || state === 'error'" class="empty-state panel" :role="state === 'error' ? 'alert' : undefined"><Icon :name="state === 'error' ? 'warning-circle' : 'file-text'" /><h2>{{ state === 'error' ? 'Data belum berhasil dimuat' : 'Belum ada data pada periode ini' }}</h2><p>{{ state === 'error' ? 'Periksa koneksi, lalu coba muat ulang. Data tidak dianggap nol saat gagal dimuat.' : 'Coba periode lain atau periksa apakah data sudah dicatat. Grafik akan tampil setelah data tersedia.' }}</p><button class="button" @click="state = 'normal'">{{ state === 'error' ? 'Coba muat ulang' : 'Kembali ke contoh data' }}</button><small>Simulasi tampilan untuk review desain.</small></section>
        <template v-else-if="screen === '/dashboard'">
          <section class="metric-strip" aria-label="Ringkasan keuangan Oktober 2026">
            <div class="metric metric--balance"><span><Icon name="wallet" />Kas dan bank</span><strong>{{ formatRp(78_450_000) }}</strong><small>Posisi 31 Oktober 2026</small></div>
            <div class="metric"><span>Pendapatan</span><strong>{{ formatRp(43_800_000) }}</strong><small>Oktober 2026</small></div>
            <div class="metric"><span>Beban</span><strong>{{ formatRp(28_650_000) }}</strong><small>Oktober 2026</small></div>
            <div class="metric"><span>Surplus bulan ini</span><strong>{{ formatRp(15_150_000) }}</strong><small>Pendapatan dikurangi beban</small></div>
          </section>

          <template v-if="isFinance">
            <div class="finance-workspace">
              <ChartCard class="primary-chart" :title="analysis === 'cash' ? 'Pergerakan kas' : 'Pendapatan dan beban'" subtitle="Mei–Oktober 2026 · juta rupiah" :description="analysis === 'cash' ? 'Kas masuk dan keluar dari jurnal tercatat. Tidak termasuk proyeksi.' : 'Pendapatan dan beban dari jurnal tercatat; berbeda dari pergerakan kas.'" :type="analysis === 'cash' ? 'line' : 'bar'" :data="analysis === 'cash' ? cashData : profitData" :options="cartesian">
                <template #summary><div class="flow-totals"><div><span><i :style="{ background: analysis === 'cash' ? colors.green : colors.navy }" />{{ analysis === 'cash' ? 'Kas masuk Oktober' : 'Pendapatan Oktober' }}</span><strong>{{ formatRp(analysis === 'cash' ? monthly.cashIn[5]! : monthly.income[5]!) }}</strong></div><div><span><i :style="{ background: analysis === 'cash' ? colors.brand : '#bd6d96' }" />{{ analysis === 'cash' ? 'Kas keluar Oktober' : 'Beban Oktober' }}</span><strong>{{ formatRp(analysis === 'cash' ? monthly.cashOut[5]! : monthly.expense[5]!) }}</strong></div></div></template>
                <template #actions><div class="segmented" role="group" aria-label="Analisis keuangan"><button :aria-pressed="analysis === 'cash'" @click="analysis = 'cash'">Arus kas</button><button :aria-pressed="analysis === 'profit'" @click="analysis = 'profit'">Laba rugi</button></div></template>
              </ChartCard>
              <aside class="work-queue" aria-label="Pekerjaan staf keuangan">
                <header><h2>Daftar kerja</h2><span class="queue-label">Perlu ditangani</span></header>
                <a class="queue-item" :href="href('/jurnal')"><span class="queue-symbol"><Icon name="book-open" /></span><div><strong>{{ journals.length }} jurnal masih draf</strong><small>Belum masuk buku besar</small></div><Icon name="arrow-up-right" /></a>
                <a class="queue-item" :href="href('/tunggakan-tagihan')"><span class="queue-symbol queue-symbol--warning"><Icon name="warning-circle" /></span><div><strong>{{ unmatchedBills }} pembayaran belum cocok</strong><small>Cocokkan bersama tata usaha</small></div><Icon name="arrow-up-right" /></a>
                <div class="receivable-summary"><span>Sisa tagihan terverifikasi</span><strong>{{ formatRp(knownOutstanding) }}</strong><p>Dari {{ bills.length - unmatchedBills }} tagihan contoh. {{ unmatchedBills }} tagihan belum diketahui sisanya.</p><a class="button secondary" :href="href('/tunggakan-tagihan')">Periksa tunggakan<Icon name="arrow-right" /></a></div>
              </aside>
              <section class="panel work-table">
                <header class="panel-heading"><div><h2>Lanjutkan pencatatan</h2><p>{{ journals.length }} draf, belum tercatat di buku besar</p></div><a class="text-link" :href="href('/jurnal')">Buka jurnal<Icon name="arrow-right" /></a></header>
                <p class="mobile-table-hint">Geser tabel untuk melihat seluruh kolom.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Jurnal draf"><table><thead><tr><th scope="col">Transaksi</th><th scope="col">Jenis</th><th scope="col" class="num">Nominal</th></tr></thead><tbody><tr v-for="journal in journals" :key="journal.code"><td><a class="transaction-link" :href="journalHref(journal.code)"><strong><Icon :name="journal.kind === 'Penerimaan' ? 'arrow-down-left' : 'arrow-up-right'" />{{ journal.title }}</strong><small>{{ journal.code }} · {{ journal.date }}</small></a></td><td><span class="status" :class="journal.tone">{{ journal.kind }}</span></td><td class="num">{{ formatRp(journal.amount) }}</td></tr></tbody></table></div>
                <p class="panel-note"><Icon name="info" />Nilai draf belum dihitung dalam ringkasan keuangan.</p>
              </section>
              <ChartCard class="composition-panel" :title="composition === 'expense' ? 'Rincian beban' : 'Sumber pendapatan'" subtitle="Oktober 2026" description="Kategori dari jurnal yang sudah tercatat." type="doughnut" :data="compositionData">
                <template #actions><div class="segmented" role="group" aria-label="Jenis rincian"><button :aria-pressed="composition === 'expense'" @click="composition = 'expense'">Beban</button><button :aria-pressed="composition === 'income'" @click="composition = 'income'">Pendapatan</button></div></template>
              </ChartCard>
            </div>
          </template>

          <template v-else-if="isPrincipal">
            <section class="approval-desk" aria-label="Persetujuan kepala sekolah">
              <div class="approval-intro"><span class="approval-symbol"><Icon name="shield-check" /></span><h2>{{ approvals.length }} jurnal menunggu keputusan</h2><p>Tinjau rincian sebelum memberi persetujuan.</p><a class="text-link" :href="href('/jurnal')">Buka antrean persetujuan<Icon name="arrow-right" /></a></div>
              <div class="approval-items"><a v-for="journal in approvals" :key="journal.code" :href="journalHref(journal.code)"><div><strong>{{ journal.title }}</strong><small>{{ journal.code }} · Menunggu persetujuan</small></div><b>{{ formatRp(journal.amount) }}</b><Icon name="caret-right" /></a></div>
            </section>
            <div class="dashboard-main principal-analysis">
              <ChartCard class="primary-chart" title="Penggunaan anggaran" subtitle="Tahun 2026 · juta rupiah" description="Realisasi tahun berjalan terhadap pagu per kategori, bukan hanya bulan Oktober." type="bar" :data="budgetData" :options="horizontal" />
              <aside class="budget-overview"><h2>Anggaran tahun 2026</h2><div class="budget-ratio">{{ budgetPercent }}<span>%</span></div><p>pagu telah direalisasikan</p><meter min="0" max="100" :value="budgetPercent" :aria-label="`${budgetPercent} persen pagu telah direalisasikan`"/><dl><dt>Pagu</dt><dd>{{ formatRp(budgetTotal) }}</dd><dt>Realisasi</dt><dd>{{ formatRp(budgetActual) }}</dd><dt>Sisa pagu</dt><dd>{{ formatRp(budgetTotal - budgetActual) }}</dd></dl><small>Sisa pagu bukan saldo kas yang tersedia.</small></aside>
            </div>
            <section class="panel activity-overview"><header class="panel-heading"><div><h2>Kegiatan dalam pengawasan</h2><p>{{ activities.length }} kegiatan contoh tahun 2026</p></div><a class="text-link" :href="href('/kegiatan')">Tinjau kegiatan<Icon name="arrow-right" /></a></header><div class="activity-progress-list"><a v-for="activity in activities" :key="activity.title" :href="href('/kegiatan')"><div><strong>{{ activity.title }}</strong><small>{{ activity.pic }} · {{ activity.date }}</small></div><div class="activity-progress"><div><span>{{ formatRp(activity.realisasi) }} <small>dari {{ formatRp(activity.pagu) }}</small></span><strong>{{ Math.round(activity.realisasi / activity.pagu * 100) }}%</strong></div><meter min="0" :max="activity.pagu" :value="activity.realisasi" :aria-label="`Realisasi ${activity.title}`" /></div><Icon name="caret-right" /></a></div></section>
          </template>
        </template>
        <template v-else-if="screen === '/siswa'">
          <div class="operations-summary"><div><strong>{{ students.length }}</strong><span>Siswa dalam contoh</span></div><div><strong>{{ students.filter((student) => student.status === 'Aktif').length }}</strong><span>Siswa aktif</span></div><div><strong>{{ students.filter((student) => student.status === 'Cuti').length }}</strong><span>Siswa cuti</span></div><a class="button secondary" :href="href('/tagihan')">Periksa tagihan<Icon name="arrow-right" /></a></div>
          <section class="panel"><div class="toolbar"><div class="field search-field"><label for="student-search">Cari siswa</label><div class="input-icon"><Icon name="magnifying-glass" /><input id="student-search" v-model="query" type="search" placeholder="Nama, NIS, atau kelompok"></div></div><div class="field"><label for="student-status">Status siswa</label><select id="student-status" v-model="status"><option value="">Semua status</option><option>Aktif</option><option>Cuti</option></select></div><button class="button secondary" @click="resetFilters">Atur ulang filter</button></div><div class="results-count">{{ filteredStudents.length }} dari {{ students.length }} siswa contoh</div><div v-if="filteredStudents.length" class="table-scroll" tabindex="0" role="region" aria-label="Data siswa contoh"><table><thead><tr><th scope="col">Siswa</th><th scope="col">Jenjang dan kelompok</th><th scope="col">Status</th><th scope="col" class="num">SPP bulanan</th><th scope="col">Aksi</th></tr></thead><tbody><tr v-for="s in filteredStudents" :key="s.id"><td><strong>{{ s.name }}</strong><small>{{ s.id }}</small></td><td>{{ s.group }}</td><td><span class="status" :class="s.status === 'Aktif' ? 'success' : 'warning'">{{ s.status }}</span></td><td class="num">{{ formatRp(s.spp) }}</td><td><button class="row-action" @click="showDetail(s.name, `${s.group}. SPP bulanan contoh ${formatRp(s.spp)}. Profil ini hanya untuk meninjau desain.`)">Lihat profil<Icon name="eye" /></button><a class="row-action student-billing-link" :href="`${href('/tagihan')}&student=${encodeURIComponent(s.id)}`">Tagihan<Icon name="arrow-right" /></a></td></tr></tbody></table></div><div v-else class="filtered-empty"><h2>Siswa tidak ditemukan</h2><p>Coba nama lain atau atur ulang filter.</p><button class="button secondary" @click="resetFilters">Atur ulang filter</button></div><p class="panel-note">SPP mengikuti tarif masing-masing siswa. Nominal di pratinjau merupakan data contoh.</p></section>
        </template>
        <BillingPreview v-else-if="isBills" :role="role.value" :outstanding="screen === '/tunggakan-tagihan'" :student="params.get('student')" :initial-id="params.get('bill')" />
        <JournalPreview v-else-if="isJournal" :role="role.value" :kind="screen.includes('jenis=masuk') ? 'masuk' : screen.includes('jenis=keluar') ? 'keluar' : 'all'" :initial-code="params.get('entry')" />
        <template v-else-if="screen === '/kegiatan'">
          <p class="inline-info"><Icon :name="isTeacher ? 'flag' : 'shield-check'" />{{ isTeacher ? 'Periksa rincian kegiatan untuk melihat realisasi. Pengelolaan kegiatan dilakukan oleh kepala sekolah.' : 'Tinjau pagu dan realisasi kegiatan. Pengeluaran dicatat oleh guru atau kepala sekolah sesuai kewenangan.' }}</p><div class="operations-summary"><div><strong>{{ activities.length }}</strong><span>Kegiatan dalam contoh</span></div><div><strong>{{ formatRp(activityBudget) }}</strong><span>Total pagu kegiatan</span></div><div><strong>{{ formatRp(activityActual) }}</strong><span>Realisasi tercatat</span></div></div><section class="panel activity-section"><header class="panel-heading"><div><h2>Daftar kegiatan</h2><p>Periksa penanggung jawab dan sisa pagu sebelum mencatat realisasi.</p></div></header><p class="mobile-table-hint">Geser tabel untuk melihat seluruh kolom.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Daftar kegiatan contoh"><table><thead><tr><th scope="col">Kegiatan dan waktu</th><th scope="col">Penanggung jawab</th><th scope="col" class="num">Pagu</th><th scope="col" class="num">Realisasi</th><th scope="col">Status</th><th scope="col">Aksi</th></tr></thead><tbody><tr v-for="a in activities" :key="a.title"><td><strong>{{ a.title }}</strong><small>{{ a.date }}</small></td><td>{{ a.pic }}</td><td class="num">{{ formatRp(a.pagu) }}</td><td class="num">{{ formatRp(a.realisasi) }}</td><td><span class="status" :class="a.status === 'Berjalan' ? 'info' : 'neutral'">{{ a.status }}</span></td><td><button class="row-action" @click="showDetail(a.title, `Pagu ${formatRp(a.pagu)}, realisasi ${formatRp(a.realisasi)}, sisa ${formatRp(a.pagu - a.realisasi)}. Penanggung jawab ${a.pic}. Rincian ini memakai data contoh.`)">Lihat realisasi<Icon name="eye" /></button></td></tr></tbody></table></div></section>
          <div class="activity-analysis"><ChartCard title="Pagu dan realisasi kegiatan" subtitle="Tiga kegiatan contoh tahun 2026" description="Bandingkan realisasi dengan pagu tiap kegiatan. Nilai ini tidak mewakili seluruh anggaran sekolah." type="bar" :data="activityData" :options="horizontal" /></div>
        </template>
        <template v-else-if="screen === '/rekap-siswa'">
          <p class="inline-info"><Icon name="eye" />{{ isTeacher ? 'Guru memiliki akses baca-saja. Hubungi staf tata usaha untuk mengubah absensi.' : 'Rekap kehadiran siswa. Pencatatan dilakukan melalui halaman absensi.' }}</p><ChartCard title="Tren kehadiran siswa" subtitle="Mei–Oktober 2026, data contoh" description="Jumlah catatan hadir per bulan. Angka tidak menunjukkan persentase kehadiran atau siswa unik." type="bar" :data="attendanceData" :options="attendanceOptions" unit="count" />
        </template>
        <footer><span>BeeSmart Finance. Pratinjau desain untuk {{ role.label.toLowerCase() }}.</span><span>Data contoh. Belum terhubung ke sistem sekolah.</span></footer>
      </main>
    </div>
  </div>
  <Drawer v-model:visible="mobileOpen" @after-hide="mobileTrigger?.focus()" :close-button-props="{ class: 'icon-button', 'aria-label': 'Tutup menu navigasi' }" header="Menu navigasi" aria-label="Menu navigasi" :pt="{ mask: { class: 'overlay-mask' }, root: { class: 'mobile-drawer' }, header: { class: 'overlay-header' }, content: { class: 'overlay-content' } }"><template #closeicon><Icon name="x" /></template><nav aria-label="Navigasi mobile"><section v-for="group in groups" :key="group" class="nav-group"><h2>{{ group }}</h2><template v-for="item in navItems.filter((n) => n.group === group)" :key="item.path"><a v-if="supported.has(item.path)" :href="href(item.path)" class="nav-item" :aria-current="screen === item.path ? 'page' : undefined"><Icon :name="item.icon" />{{ item.label }}</a><span v-else class="nav-item nav-item--pending"><Icon :name="item.icon" />{{ item.label }}<span class="sr-only">, belum tersedia dalam pratinjau</span></span></template></section></nav></Drawer>
  <Dialog v-model:visible="dialogVisible" :close-button-props="{ class: 'icon-button', 'aria-label': 'Tutup rincian' }" modal :draggable="false" :header="detail?.title" :pt="{ mask: { class: 'overlay-mask dialog-mask' }, root: { class: 'preview-dialog' }, header: { class: 'overlay-header' }, content: { class: 'overlay-content' }, footer: { class: 'overlay-footer' } }"><template #closeicon><Icon name="x" /></template><p class="detail-copy">{{ detail?.text }}</p><template #footer><button class="button secondary" @click="dialogVisible = false">Tutup pratinjau</button></template></Dialog>
</template>
