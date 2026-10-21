<script setup lang="ts">
import { computed, ref } from "vue"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Chart from "primevue/chart"
import type { ChartOptions } from "chart.js"
import type { Role } from "@/types/api"
import { navForRoles, roleHome } from "@/core/navigation"
import { formatRp } from "@/core/format"
import Icon from "@/shared/components/PhosphorIcon.vue"
import ComponentWorkbench from "./ComponentWorkbench.vue"
import StudentWorkbench from "./StudentWorkbench.vue"
import BillingWorkbench from "./BillingWorkbench.vue"
import ActivityWorkbench from "./ActivityWorkbench.vue"
import JournalWorkbench from "./JournalWorkbench.vue"
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import Select from "primevue/select"
import Toast from "primevue/toast"
import ConfirmDialog from "primevue/confirmdialog"
import tokenUrl from "@/core/design-tokens.json?url"
import { roles, screenInfo, monthly, months } from "../design-preview/fixtures"
import { createDemoJournals, journalStates, lineTotals, type DemoJournal } from "../design-preview/journal-preview"
import { tokens, contrastPairs, contrastRatio } from "./tokens"

const sections = [
  { id: "arah", label: "Arah desain" }, { id: "fondasi", label: "Warna dan tipografi" },
  { id: "ritme", label: "Ruang dan kepadatan" }, { id: "komponen", label: "Kontrol dan form" },
  { id: "data", label: "Tabel dan status" }, { id: "layar-siswa", label: "Layar siswa interaktif" }, { id: "layar-tagihan", label: "Tagihan dan pembayaran" }, { id: "layar-kegiatan", label: "Kegiatan tiap peran" }, { id: "layar-jurnal", label: "Jurnal dan pencatatan" }, { id: "grafik", label: "Grafik" },
  { id: "keadaan", label: "Keadaan antarmuka" }, { id: "peran", label: "Pola tiap peran" },
]
const coreColors = [
  { key: "nav", name: "Navy", role: "Navigasi dan struktur", light: true },
  { key: "brand", name: "Magenta", role: "Tindakan utama", light: true },
  { key: "honey", name: "Madu", role: "Identitas sekolah", light: false },
  { key: "canvas", name: "Kanvas", role: "Latar ruang kerja", light: false },
  { key: "surface", name: "Permukaan", role: "Area yang dikerjakan", light: false },
  { key: "ink", name: "Tinta", role: "Teks dan angka utama", light: true },
] as const
const specimens = [
  { role: "Judul halaman", token: "title", text: "Ringkasan keuangan", detail: "32 / 600 · arah halaman" },
  { role: "Judul bagian", token: "section", text: "Jurnal yang perlu diperiksa", detail: "20 / 600 · kelompok informasi" },
  { role: "Isi dan instruksi", token: "body", text: "Periksa nominal dan akun sebelum mencatat jurnal.", detail: "16 / 400 · teks yang dibaca" },
  { role: "Kontrol dan tabel", token: "ui", text: "Cari nama siswa atau nomor bukti", detail: "14 / 500 · pekerjaan rutin" },
  { role: "Keterangan", token: "caption", text: "Posisi kas pada 31 Oktober 2026", detail: "13 / 400 · konteks pendukung" },
] as const
const rows = createDemoJournals()
const chartMode = ref<"cash" | "profit">("cash")
const chartData = computed(() => ({ labels: months, datasets: chartMode.value === "cash" ? [
  { label: "Kas masuk", data: monthly.cashIn, borderColor: tokens.color["chart-ink"], backgroundColor: tokens.color["chart-ink"], borderWidth: 2.5, pointRadius: 3, tension: 0 },
  { label: "Kas keluar", data: monthly.cashOut, borderColor: tokens.color["chart-rose"], backgroundColor: tokens.color["chart-rose"], borderDash: [5, 4], borderWidth: 2.5, pointRadius: 3, tension: 0 },
] : [
  { label: "Pendapatan", data: monthly.income, backgroundColor: tokens.color["chart-ink"], borderRadius: 2, maxBarThickness: 20 },
  { label: "Beban", data: monthly.expense, backgroundColor: tokens.color["chart-rose"], borderRadius: 2, maxBarThickness: 20 },
] }))
const chartOptions: ChartOptions = {
  responsive: true, maintainAspectRatio: false, animation: false,
  plugins: { legend: { position: "bottom", labels: { color: tokens.color.muted, usePointStyle: true, boxWidth: 7, boxHeight: 7, pointStyleWidth: 7, font: { family: tokens.font.body, size: 13 }, padding: 20 } }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${formatRp(Number(context.parsed.y))}` } } },
  scales: { x: { grid: { display: false }, border: { display: false }, ticks: { color: tokens.color.muted, font: { family: tokens.font.body, size: 13 } } }, y: { beginAtZero: true, grid: { color: tokens.color.border }, border: { display: false }, ticks: { maxTicksLimit: 5, color: tokens.color.muted, callback: (value) => `${Number(value) / 1_000_000} jt` } } },
}
const uiState = ref<"empty" | "loading" | "error" | "success">("empty")
const dialog = ref(false)
const selectedRow = ref<DemoJournal | null>(null)
const form = ref({ proof: "", account: "", amount: 0 })
const formError = ref("")
const saved = ref(false)
function openRow(row: DemoJournal) { selectedRow.value = row; dialog.value = true }
function openForm() { selectedRow.value = null; saved.value = false; formError.value = ""; form.value = { proof: "", account: "", amount: 0 }; dialog.value = true }
function saveExample() {
  if (!form.value.proof.trim() || !form.value.account || !Number.isFinite(form.value.amount) || form.value.amount <= 0) { formError.value = "Lengkapi nomor bukti, Kas/Bank, dan nominal lebih dari nol."; return }
  saved.value = true; formError.value = ""
}
const role = ref<Role>("Finance")
const rolePatterns = {
  Finance: { title: "Ringkasan keuangan", subtitle: "Kas, pencatatan, dan tindak lanjut.", metric: "Kas dan bank", value: "Rp 78.450.000", scope: "Posisi 31 Oktober 2026", next: "Lanjutkan pencatatan", items: ["3 jurnal masih draf", "1 pembayaran perlu dicocokkan"], note: "Kehadiran siswa berada di area operasional yang berwenang." },
  SchoolPrincipal: { title: "Ikhtisar sekolah", subtitle: "Keputusan dan pengawasan anggaran.", metric: "Menunggu persetujuan", value: "2 jurnal", scope: "Antrean contoh, bukan semua draf", next: "Tinjau sebelum memutuskan", items: ["Realisasi kegiatan kelas — Rp 600.000", "Penggajian Oktober — Rp 20.000.000"], note: "Persetujuan, kondisi keuangan, dan pagu kegiatan menjadi prioritas." },
  Administration: { title: "Data siswa", subtitle: "Profil, kelompok, dan administrasi layanan.", metric: "Siswa dalam contoh", value: "4 siswa", scope: "3 aktif, 1 cuti", next: "Pekerjaan tata usaha", items: ["Periksa tagihan siswa", "Cocokkan bukti penerimaan lama"], note: "Pencatatan pembayaran berada di TU. Laporan keuangan bukan isi home TU." },
  TeacherInCharge: { title: "Kegiatan sekolah", subtitle: "Pagu dan realisasi kegiatan.", metric: "Kegiatan dalam contoh", value: "3 kegiatan", scope: "Pagu Rp 7.000.000", next: "Pantau kegiatan", items: ["Pekan membaca — realisasi Rp 1.200.000", "Kunjungan edukasi — realisasi Rp 2.100.000"], note: "Guru membaca kegiatan dan mencatat realisasi sesuai akses yang berlaku." },
}
const currentPattern = computed(() => rolePatterns[role.value])
const sampleNavigation = computed(() => navForRoles([role.value]).filter((item) => ["/dashboard", "/jurnal", "/tunggakan-tagihan", "/siswa", "/tagihan", "/kegiatan", "/rekap-siswa"].includes(item.to)).slice(0, 5))

</script>

<template>
  <Toast /><ConfirmDialog />
  <a class="bee-skip" href="#arah">Langsung ke isi</a>
  <header class="library-header"><a class="library-brand" href="#arah"><img src="/logo-lebah.svg" alt=""><strong>BeeSmart<span>Finance</span></strong></a><div class="library-context">Sistem desain <span class="bee-tag">Fondasi 0.12</span></div><a class="bee-link" href="#layar-jurnal">Coba jurnal<Icon name="arrow-down-left" /></a></header>
  <div class="library-layout"><aside class="library-sidebar"><nav aria-label="Bagian sistem desain"><a v-for="section in sections" :key="section.id" :href="`#${section.id}`">{{ section.label }}</a></nav><p>Fondasi untuk empat peran.<br>Terhubung ke tema aplikasi lokal.</p><a class="bee-link" :href="tokenUrl" download="beesmart-design-tokens.json">Unduh token JSON<Icon name="download" /></a></aside>
  <main class="library-main">
    <section id="arah" class="direction-section"><div class="direction-copy"><p class="section-kicker">Lebah Madu / BeeSmart Finance</p><h1>Jelas di setiap angka.</h1><p class="direction-lead">Sistem visual untuk pekerjaan keuangan dan operasional sekolah. Struktur tegas, teks yang nyaman, dan tindakan yang mudah dikenali.</p><div class="direction-attributes"><span><i class="attribute-dot" />Terstruktur</span><span>Terbaca</span><span>Terarah</span></div></div><div class="ledger-specimen"><div class="ledger-heading"><Icon name="wallet" /><span>Kas dan bank</span><span class="ledger-sample">Data contoh</span></div><strong class="ledger-number">Rp 78.450.000</strong><p>Posisi 31 Oktober 2026</p><div class="ledger-breakdown"><div><span>Pendapatan</span><strong>Rp 43.800.000</strong></div><div><span>Beban</span><strong>Rp 28.650.000</strong></div></div><div class="ledger-footer"><span>Surplus bulan ini</span><strong>Rp 15.150.000</strong></div></div></section>
    <div class="decision-note"><Icon name="info" /><p><strong>Fondasi dulu, layar mengikuti.</strong> Warna, ukuran, dan pola di halaman ini menjadi sumber rancangan berikutnya. Preview sebelumnya disimpan sebagai pembanding.</p></div>

    <section id="fondasi" class="system-section"><header class="system-section-heading"><h2>Warna punya pekerjaan.</h2><p>Navy membentuk struktur. Magenta menandai tindakan utama. Madu membawa identitas sekolah; status memakai warna semantiknya sendiri.</p></header><div class="palette-grid"><article v-for="color in coreColors" :key="color.key" class="palette-item"><div class="palette-swatch" :style="{ background: tokens.color[color.key], color: color.light ? tokens.color.surface : tokens.color.ink }"><span>Aa</span><code>{{ tokens.color[color.key] }}</code></div><h3>{{ color.name }}</h3><p>{{ color.role }}</p></article></div><div class="semantic-strip"><div class="bee-status bee-status--positive"><Icon name="check-circle" />Tercatat</div><div class="bee-status bee-status--warning"><Icon name="clock" />Menunggu persetujuan</div><div class="bee-status bee-status--critical"><Icon name="warning-circle" />Dibatalkan</div><div class="bee-status bee-status--neutral"><Icon name="file-text" />Draf</div></div><details class="spec-details"><summary>Pasangan warna dan rasio kontras</summary><div class="contrast-grid"><div v-for="pair in contrastPairs" :key="pair.name" class="contrast-sample" :style="{ color: pair.foreground, background: pair.background }"><strong>{{ pair.name }}</strong><span>{{ contrastRatio(pair.foreground, pair.background).toFixed(2) }} : 1</span></div></div><p>Perhitungan token untuk teks normal minimal 4,5 : 1. Ini bukan audit aksesibilitas seluruh aplikasi.</p></details>
      <div class="type-heading"><div><h3>Satu keluarga, hierarki yang jelas.</h3><p>IBM Plex Sans. Empat bobot; setiap ukuran punya peran. Angka memakai tabular numerals dan rata kanan di tabel.</p></div><div class="type-mark" aria-hidden="true">Ag<span>012345</span></div></div><div class="type-specimens"><div v-for="specimen in specimens" :key="specimen.role" class="type-specimen"><div><strong>{{ specimen.role }}</strong><small>{{ specimen.detail }}</small></div><p :style="{ fontSize: tokens.type[specimen.token], fontWeight: specimen.token === 'title' || specimen.token === 'section' ? 600 : specimen.token === 'ui' ? 500 : 400, lineHeight: specimen.token === 'title' || specimen.token === 'section' ? tokens.leading.heading : tokens.leading.body }">{{ specimen.text }}</p></div></div><div class="number-specimens"><div><span>Angka utama / 44 px / 500</span><strong>Rp 78.450.000</strong></div><div><span>Angka pendukung / 28 px / 500</span><strong>Rp 15.150.000</strong></div></div>
    </section>

    <section id="ritme" class="system-section"><header class="system-section-heading"><h2>Ruang membentuk hierarki.</h2><p>Gunakan jarak untuk mengelompokkan informasi. Panel dipakai untuk satu pekerjaan; bagian di dalamnya tidak perlu menjadi kartu baru.</p></header><div class="spacing-scale"><div v-for="(value, key) in tokens.space" :key="key"><span :style="{ width: value }"/><strong>{{ value }}</strong><small>space.{{ key }}</small></div></div><div class="rules-grid"><article><Icon name="squares-four" /><h3>Struktur halaman</h3><p>Gutter 32 px di desktop, 16 px di mobile. Jarak antarbagian 48 px; isi panel 24 px. Lebar mengikuti data dan pekerjaan.</p></article><article><Icon name="list" /><h3>Kepadatan yang disengaja</h3><p>Baris minimum 60 px, ringkas 48 px. Record dua baris memakai 72 / 60 px. Kontrol utama tetap 44 px. Mobile mengutamakan nominal, status, dan tindakan.</p></article><article><Icon name="eye" /><h3>Kedalaman seperlunya</h3><p>Permukaan memakai batas tipis. Bayangan untuk overlay dan bagian yang terangkat. Radius kontrol 6 px, panel 10 px, dialog 14 px.</p></article></div></section>

    <ComponentWorkbench :rows="rows" @open-form="openForm" @open-row="openRow" />

    <StudentWorkbench />
    <BillingWorkbench />
    <ActivityWorkbench />
    <JournalWorkbench />

    <section id="grafik" class="system-section"><header class="system-section-heading"><h2>Grafik menjawab pertanyaan.</h2><p>Satu pertanyaan per grafik. Periode, satuan, legenda, dan angka alternatif selalu ikut. Warna tidak menjadi satu-satunya pembeda.</p></header><div class="chart-specimens"><section class="bee-panel bee-chart-panel"><header><div><h3>{{ chartMode === 'cash' ? 'Bagaimana kas bergerak?' : 'Bagaimana pendapatan dibandingkan beban?' }}</h3><p>Mei–Oktober 2026 · juta rupiah · data contoh</p></div><div class="bee-segmented" role="group" aria-label="Contoh grafik"><button :aria-pressed="chartMode === 'cash'" @click="chartMode = 'cash'">Arus kas</button><button :aria-pressed="chartMode === 'profit'" @click="chartMode = 'profit'">Laba rugi</button></div></header><div class="ds-chart"><Chart :type="chartMode === 'cash' ? 'line' : 'bar'" :data="chartData" :options="chartOptions" :canvas-props="{ role: 'img', 'aria-label': chartMode === 'cash' ? 'Kas masuk dan keluar Mei sampai Oktober 2026. Angka tersedia pada tabel di bawah.' : 'Pendapatan dan beban Mei sampai Oktober 2026. Angka tersedia pada tabel di bawah.' }" /></div><details class="chart-alternative"><summary>Lihat tabel angka</summary><div class="ds-table-scroll" tabindex="0" role="region" aria-label="Angka pada grafik"><table class="bee-table"><thead><tr><th scope="col">Bulan</th><th v-for="series in chartData.datasets" :key="series.label" scope="col" class="numeric">{{ series.label }}</th></tr></thead><tbody><tr v-for="(label, index) in months" :key="label"><th scope="row">{{ label }}</th><td v-for="series in chartData.datasets" :key="series.label" class="numeric">{{ formatRp(series.data[index]) }}</td></tr></tbody></table></div></details></section><aside class="chart-rules"><h3>Pilihan bentuk</h3><dl><dt>Tren waktu</dt><dd>Garis, dengan titik aktual.</dd><dt>Perbandingan</dt><dd>Batang, baseline nol.</dd><dt>Pagu dan realisasi</dt><dd>Batang horizontal, tahun jelas.</dd><dt>Komposisi</dt><dd>Bar/daftar proporsi; donut hanya jika sedikit kategori dan ada nominal.</dd></dl><div class="chart-colors"><i v-for="color in [tokens.color['chart-ink'], tokens.color['chart-rose'], tokens.color['chart-teal'], tokens.color['chart-gold']]" :key="color" :style="{ background: color }"/></div><p>Arus kas dan pendapatan memakai definisi berbeda. Data hilang tidak diubah menjadi nol.</p></aside></div></section>

    <section id="keadaan" class="system-section"><header class="system-section-heading"><h2>Setiap keadaan punya jalan lanjut.</h2><p>Pesan menyebut kondisi dan langkah pemulihannya. Fokus keyboard terlihat. Perubahan tidak dijelaskan lewat warna saja.</p></header><div class="state-switcher bee-segmented" role="group" aria-label="Contoh keadaan antarmuka"><button v-for="(label, value) in { empty: 'Kosong', loading: 'Memuat', error: 'Gagal', success: 'Berhasil' }" :key="value" :aria-pressed="uiState === value" @click="uiState = value">{{ label }}</button></div><div class="bee-panel state-specimen"><div v-if="uiState === 'empty'" class="bee-empty"><Icon name="book-open" /><h3>Belum ada pembayaran pada periode ini</h3><p>Pilih periode lain atau mulai catat transaksi yang sudah memiliki bukti.</p><button class="bee-button" @click="openForm">Catat pembayaran contoh</button></div><div v-else-if="uiState === 'loading'" class="bee-loading" role="status"><span class="sr-only">Memuat pembayaran contoh</span><div class="skeleton-line"/><div class="skeleton-line"/><div class="skeleton-line"/><p>Memuat pembayaran…</p></div><div v-else-if="uiState === 'error'" class="bee-message bee-message--critical" role="alert"><Icon name="warning-circle" /><div><h3>Pembayaran belum berhasil dimuat</h3><p>Periksa koneksi, lalu coba muat ulang. Ini contoh pesan pemulihan.</p><button class="bee-button bee-button--secondary" @click="uiState = 'success'">Coba muat ulang contoh</button></div></div><div v-else class="bee-message bee-message--positive" role="status"><Icon name="check-circle" /><div><h3>Pembayaran tersimpan</h3><p>Periksa kembali rincian dan nomor bukti penerimaan. Ini contoh keadaan berhasil.</p></div></div></div></section>

    <section id="peran" class="system-section"><header class="system-section-heading"><h2>Satu sistem, prioritas berbeda.</h2><p>Komponen dan gaya tetap sama. Beranda, informasi, serta tindakan mengikuti tugas dan akses peran existing.</p></header><div class="role-switcher" role="group" aria-label="Contoh pola peran"><button v-for="item in roles" :key="item.value" :aria-pressed="role === item.value" @click="role = item.value">{{ item.label }}</button></div><div class="role-workbench"><aside><div class="sample-school"><img src="/logo-lebah.svg" alt=""><strong>Lebah Madu</strong></div><p>Cuplikan navigasi</p><ul><li v-for="item in sampleNavigation" :key="`${item.to}${item.query?.jenis ?? ''}`" :class="{ 'is-current': item.to === roleHome([role]) }"><Icon :name="screenInfo[item.query?.jenis ? `${item.to}?jenis=${item.query.jenis}` : item.to]?.icon ?? 'file-text'" />{{ item.label }}</li></ul><span>{{ roles.find((item) => item.value === role)?.label }}</span></aside><section class="role-surface"><header><h3>{{ currentPattern.title }}</h3><p>{{ currentPattern.subtitle }}</p></header><div class="role-key-value"><span>{{ currentPattern.metric }}</span><strong>{{ currentPattern.value }}</strong><small>{{ currentPattern.scope }}</small></div><div class="role-next"><h4>{{ currentPattern.next }}</h4><ul><li v-for="item in currentPattern.items" :key="item"><Icon name="caret-right" />{{ item }}</li></ul></div><p class="role-note">{{ currentPattern.note }}</p></section></div><p class="section-footnote">Contoh presentasi. Pengaturan peran ini tidak mengganti autentikasi atau permission aplikasi.</p></section>
    <footer class="library-footer"><p>BeeSmart Finance / Sistem desain 0.12</p><p>Phosphor Icons Regular, MIT. <a href="https://github.com/phosphor-icons/core">Sumber ikon</a> · <a href="/dashboard-preview.html?role=Finance">Preview sebelumnya</a></p></footer>
  </main></div>
  <Dialog v-model:visible="dialog" modal :draggable="false" :header="selectedRow ? 'Rincian jurnal contoh' : 'Contoh form pembayaran'" :close-button-props="{ severity: 'secondary', text: true, class: 'bee-icon-button', 'aria-label': 'Tutup dialog contoh' }" :pt="{ mask: { class: 'bee-overlay-mask' }, root: { class: 'bee-dialog' }, header: { class: 'bee-dialog-header' }, content: { class: 'bee-dialog-content' }, footer: { class: 'bee-dialog-footer' } }"><template #closeicon><Icon name="x" /></template><p class="dialog-scope">Spesimen komponen. Tidak menyimpan transaksi sekolah.</p><section v-if="selectedRow" class="record-dialog"><span class="bee-status" :class="selectedRow.state === 'POSTED' ? 'bee-status--positive' : selectedRow.state === 'PENDING' ? 'bee-status--warning' : 'bee-status--neutral'">{{ journalStates[selectedRow.state].label }}</span><h3>{{ selectedRow.title }}</h3><p>{{ selectedRow.code }} · {{ selectedRow.date.split('-').reverse().join('/') }}</p><strong>{{ formatRp(lineTotals(selectedRow.lines).debit) }}</strong><dl><template v-for="(line, index) in selectedRow.lines" :key="index"><dt>Akun {{ line.account }}</dt><dd>Debit {{ formatRp(line.debit) }} / Kredit {{ formatRp(line.credit) }}</dd></template></dl></section><section v-else-if="saved" class="bee-message bee-message--positive" role="status"><Icon name="check-circle" /><div><h3>Contoh berhasil disimpan</h3><p>Nominal {{ formatRp(form.amount) }}. Bentuk, pesan, dan fokus mengikuti pola yang sama.</p></div></section><form v-else id="specimen-form" class="bee-form" @submit.prevent="saveExample"><div class="bee-field"><label for="dialog-proof">Nomor bukti penerimaan</label><InputText id="dialog-proof" v-model="form.proof" required maxlength="100" placeholder="Contoh: BKT-002" autofocus /></div><div class="bee-field"><label for="dialog-account">Kas/Bank penerima</label><Select input-id="dialog-account" v-model="form.account" :options="['Kas di Tangan', 'Kas di Bank']" placeholder="Pilih Kas/Bank" /></div><div class="bee-field"><label for="dialog-amount">Nominal diterima (Rp)</label><InputNumber input-id="dialog-amount" v-model="form.amount" locale="id-ID" :min="0" :max-fraction-digits="2"/><small>Nominal lengkap tetap terlihat dan dapat dipilih.</small></div><p v-if="formError" class="bee-message bee-message--critical" role="alert">{{ formError }}</p></form><template #footer><Button severity="secondary" label="Tutup contoh" @click="dialog = false" /><Button v-if="!saved && !selectedRow" type="submit" form="specimen-form" label="Simpan contoh" /></template></Dialog>
</template>
