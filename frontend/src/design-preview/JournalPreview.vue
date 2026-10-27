<script setup lang="ts">
import { computed, nextTick, reactive, ref } from "vue"
import Drawer from "primevue/drawer"
import InputNumber from "primevue/inputnumber"
import type { Role } from "@/types/api"
import { formatRp } from "@/core/format"
import Icon from "./PhosphorIcon.vue"
import { availableAction, createDemoJournals, demoAccounts, hasValidLines, journalSources, journalStates, lineTotals, type DemoJournal, type JournalLine, type JournalState } from "./journal-preview"

const props = defineProps<{ role: Role; kind: "masuk" | "keluar" | "all"; initialCode?: string | null }>()
const rows = ref(createDemoJournals())
const query = ref("")
const month = ref("")
const status = ref<JournalState | "">(props.role === "SchoolPrincipal" ? "PENDING" : "")
const selected = ref<DemoJournal | null>(null)
const mode = ref<"view" | "edit" | "confirm" | "discard" | "result">("view")
const visible = ref(false)
const result = ref("")
const announcement = ref("")
const error = ref("")
const errorElement = ref<HTMLElement | null>(null)
const resultElement = ref<HTMLElement | null>(null)
const listHeading = ref<HTMLElement | null>(null)
const decisionElement = ref<HTMLElement | null>(null)
const detailHeading = ref<HTMLElement | null>(null)
let trigger: HTMLElement | null = null
const original = ref("")
const form = reactive({ code: "", date: "2026-10-15", title: "", lines: [] as JournalLine[] })
const statusOptions: (JournalState | "")[] = ["", "DRAFT", "PENDING", "POSTED"]
const actions = { record: "Catat ke buku besar", submit: "Ajukan persetujuan", approve: "Setujui dan catat" }
const action = computed(() => selected.value ? availableAction(selected.value, props.role) : null)
const editable = computed(() => props.role === "Finance" && selected.value?.state === "DRAFT" && selected.value.source === "MANUAL")
const totals = computed(() => lineTotals(form.lines))
const dirty = computed(() => JSON.stringify(form) !== original.value)
const drawerVisible = computed({ get: () => visible.value, set: (value) => { if (!value) close() } })
const kindRows = computed(() => rows.value.filter((journal) => props.kind === "all" || journal.lines.some((line) => line.account.startsWith(props.kind === "masuk" ? "4" : "5"))))
const baseRows = computed(() => kindRows.value.filter((journal) => !month.value || journal.date.startsWith(month.value)))
const filtered = computed(() => baseRows.value.filter((journal) => (!status.value || journal.state === status.value)
  && `${journal.code} ${journal.title} ${journalSources[journal.source]}`.toLocaleLowerCase("id").includes(query.value.trim().toLocaleLowerCase("id")))
  .sort((a, b) => b.date.localeCompare(a.date) || a.code.localeCompare(b.code)))
const availableMonths = computed(() => [...new Set(kindRows.value.map((journal) => journal.date.slice(0, 7)))].sort().reverse())
const monthFormatter = new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric" })
const dateFormatter = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", year: "numeric" })
function dateLabel(date: string) { return dateFormatter.format(new Date(`${date}T12:00:00`)) }
function accountName(code: string) { return demoAccounts.find((account) => account.code === code)?.name ?? code }
function href(kind: "all" | "masuk" | "keluar") {
  return `?${new URLSearchParams({ role: props.role, screen: kind === "all" ? "/jurnal" : `/jurnal?jenis=${kind}` })}`
}
function reset() { query.value = ""; month.value = ""; status.value = "" }
function open(journal: DemoJournal) {
  trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
  selected.value = journal; mode.value = "view"; error.value = ""; visible.value = true
}
async function edit(create = false) {
  if (props.role !== "Finance" || (!create && !editable.value)) return
  if (create) { trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null; selected.value = null }
  const journal = selected.value
  Object.assign(form, journal ? { code: journal.code, date: journal.date, title: journal.title, lines: journal.lines.map((line) => ({ ...line })) }
    : { code: "", date: "2026-10-15", title: "", lines: [
      { account: props.kind === "keluar" ? "5.3.01" : "1.1.02", debit: 0, credit: 0 },
      { account: props.kind === "keluar" ? "1.1.02" : "4.1.08", debit: 0, credit: 0 },
    ] })
  original.value = JSON.stringify(form); error.value = ""; mode.value = "edit"; visible.value = true
  await nextTick(); document.getElementById("journal-code")?.focus()
}
async function changeMode(value: "edit" | "view" | "confirm" | "discard") {
  mode.value = value
  await nextTick()
  if (value === "edit") document.getElementById("journal-code")?.focus()
  else (decisionElement.value ?? detailHeading.value)?.focus()
}
function close() {
  if (mode.value === "edit" && dirty.value) { void changeMode("discard"); return }
  visible.value = false
}
function discard() { if (selected.value) void changeMode("view"); else visible.value = false }
function restoreFocus() { (trigger?.isConnected ? trigger : listHeading.value)?.focus() }
async function showError(message: string) { error.value = message; await nextTick(); errorElement.value?.focus() }
async function showResult(message: string) {
  result.value = message; announcement.value = message; mode.value = "result"
  await nextTick(); resultElement.value?.focus()
}
async function save() {
  if (props.role !== "Finance" || (selected.value && !editable.value)) return
  if (!form.code.trim() || !form.title.trim()) return showError("Isi nomor bukti dan keterangan transaksi.")
  if (rows.value.some((journal) => journal !== selected.value && journal.code.toLocaleLowerCase("id") === form.code.trim().toLocaleLowerCase("id"))) return showError("Nomor bukti sudah digunakan. Gunakan nomor lain.")
  const date = new Date(`${form.date}T12:00:00Z`)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(form.date) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== form.date) return showError("Pilih tanggal transaksi yang valid.")
  if (!hasValidLines(form.lines)) return showError("Pilih akun pada setiap baris. Isi salah satu debit atau kredit per baris dengan rupiah bulat; total keduanya harus sama dan lebih dari nol.")
  if (props.kind !== "all" && !form.lines.some((line) => line.account.startsWith(props.kind === "masuk" ? "4" : "5"))) return showError(`Sertakan akun ${props.kind === "masuk" ? "pendapatan (4.x)" : "beban (5.x)"} agar jurnal sesuai daftar ini.`)
  const values = { code: form.code.trim(), title: form.title.trim(), date: form.date, lines: form.lines.map((line) => ({ account: line.account, debit: Number(line.debit), credit: Number(line.credit) })) }
  if (selected.value) Object.assign(selected.value, values)
  else { rows.value.unshift({ ...values, source: "MANUAL", state: "DRAFT", creator: "Finance", needsMatching: false }); selected.value = rows.value[0]! }
  reset()
  await showResult(`Draf ${values.code} tersimpan di pratinjau. Belum tercatat di buku besar.`)
}
async function performAction() {
  const journal = selected.value
  const next = action.value
  if (!journal || !next || mode.value !== "confirm") return
  journal.state = next === "submit" ? "PENDING" : "POSTED"
  await showResult(`${journal.code}: ${next === "submit" ? "pengajuan persetujuan" : "pencatatan ke buku besar"} berhasil disimulasikan. Tidak ada perubahan pada sistem sekolah.`)
}
const initial = rows.value.find((journal) => journal.code === props.initialCode && kindRows.value.includes(journal))
if (initial) { selected.value = initial; visible.value = true }
</script>

<template>
  <section class="journal-workspace" aria-label="Daftar jurnal">
    <div class="journal-navigation"><nav aria-label="Jenis jurnal"><a :href="href('all')" :aria-current="kind === 'all' ? 'page' : undefined">Semua jurnal</a><a :href="href('masuk')" :aria-current="kind === 'masuk' ? 'page' : undefined"><Icon name="arrow-down-left" />Pemasukan</a><a :href="href('keluar')" :aria-current="kind === 'keluar' ? 'page' : undefined"><Icon name="arrow-up-right" />Pengeluaran</a></nav><button v-if="role === 'Finance'" class="button" @click="edit(true)"><Icon name="file-text" />Buat jurnal</button></div>
    <p v-if="announcement" class="preview-feedback" role="status"><Icon name="check-circle" />{{ announcement }}</p>
    <section class="panel journal-list-panel">
      <div class="journal-filters"><div class="field search-field"><label for="journal-search">Cari jurnal</label><div class="input-icon"><Icon name="magnifying-glass" /><input id="journal-search" v-model="query" type="search" placeholder="Nomor bukti, keterangan, atau sumber"></div></div><div class="field"><label for="journal-month">Bulan transaksi</label><select id="journal-month" v-model="month"><option value="">Semua bulan</option><option v-for="value in availableMonths" :key="value" :value="value">{{ monthFormatter.format(new Date(`${value}-01T12:00:00`)) }}</option></select></div><button class="button secondary" @click="reset">Atur ulang</button></div>
      <div class="journal-status-tabs" role="group" aria-label="Status jurnal"><button v-for="option in statusOptions" :key="option" :aria-pressed="status === option" @click="status = option">{{ option ? journalStates[option].label : 'Semua status' }}<span>{{ baseRows.filter((journal) => !option || journal.state === option).length }}</span></button></div>
      <div class="journal-list-context"><h2 ref="listHeading" tabindex="-1">{{ filtered.length }} jurnal ditampilkan</h2><span>Data contoh · urutan tanggal terbaru</span></div>
      <div v-if="filtered.length" class="table-scroll journal-table-desktop" tabindex="0" role="region" aria-label="Hasil pencarian jurnal"><table><thead><tr><th scope="col">Tanggal dan bukti</th><th scope="col">Transaksi</th><th scope="col" class="num">Nominal</th><th scope="col">Status</th><th scope="col">Aksi</th></tr></thead><tbody><tr v-for="journal in filtered" :key="journal.code"><td><strong>{{ dateLabel(journal.date) }}</strong><small>{{ journal.code }}</small></td><td><strong>{{ journal.title }}</strong><small>{{ journalSources[journal.source] }}</small></td><td class="num">{{ formatRp(lineTotals(journal.lines).debit) }}</td><td><span class="status" :class="journalStates[journal.state].tone">{{ journalStates[journal.state].label }}</span></td><td><button class="row-action" :aria-label="`Buka ${journal.code}`" @click="open(journal)">{{ journal.state === 'POSTED' ? 'Lihat rincian' : 'Periksa jurnal' }}<Icon name="caret-right" /></button></td></tr></tbody></table></div>
      <ul v-if="filtered.length" class="journal-mobile-rows" aria-label="Jurnal pada perangkat kecil"><li v-for="journal in filtered" :key="journal.code"><div class="record-mobile-meta"><span class="status" :class="journalStates[journal.state].tone">{{ journalStates[journal.state].label }}</span><span>{{ dateLabel(journal.date) }}</span></div><h3>{{ journal.title }}</h3><p>{{ journal.code }} · {{ journalSources[journal.source] }}</p><div class="journal-mobile-action"><strong>{{ formatRp(lineTotals(journal.lines).debit) }}</strong><button class="row-action" :aria-label="`Buka ${journal.code}`" @click="open(journal)">{{ journal.state === 'POSTED' ? 'Lihat rincian' : 'Periksa jurnal' }}<Icon name="caret-right" /></button></div></li></ul>
      <div v-else class="filtered-empty"><Icon name="magnifying-glass" /><h2>Tidak ada jurnal yang sesuai</h2><p>Coba kata kunci lain atau tampilkan semua status dan bulan.</p><button class="button secondary" @click="reset">Atur ulang pencarian</button></div>
      <p class="panel-note"><Icon name="info" />Perubahan simulasi hanya bertahan di halaman ini. Memuat ulang atau berpindah halaman mengembalikan data contoh.</p>
    </section>
  </section>

  <Drawer v-model:visible="drawerVisible" position="right" :header="mode === 'edit' ? selected ? 'Ubah draf jurnal' : 'Buat jurnal' : selected?.code ?? 'Rincian jurnal'" aria-label="Rincian dan tindakan jurnal" @after-hide="restoreFocus" :close-button-props="{ class: 'icon-button', 'aria-label': 'Tutup jurnal' }" :pt="{ mask: { class: 'overlay-mask detail-mask' }, root: { class: 'detail-drawer' }, header: { class: 'overlay-header' }, content: { class: 'overlay-content' }, footer: { class: 'overlay-footer detail-drawer-footer' } }">
    <template #closeicon><Icon name="x" /></template>
    <p class="demo-notice"><Icon name="eye" />Simulasi desain. Tidak mengubah data sekolah.</p>
    <template v-if="mode === 'edit'">
      <form id="entry-form" class="entry-form" @submit.prevent="save">
        <div class="form-grid"><div class="field"><label for="journal-code">Nomor bukti <span aria-hidden="true">*</span></label><input id="journal-code" v-model="form.code" required maxlength="50" placeholder="Contoh: CONTOH-008" autofocus></div><div class="field"><label for="journal-date">Tanggal transaksi <span aria-hidden="true">*</span></label><input id="journal-date" v-model="form.date" type="date" required></div></div>
        <div class="field"><label for="journal-description">Keterangan transaksi <span aria-hidden="true">*</span></label><input id="journal-description" v-model="form.title" required maxlength="255" placeholder="Contoh: Pembayaran biaya operasional"></div>
        <div class="journal-lines-heading"><h2>Rincian akun</h2><p>Daftar akun contoh. Isi debit atau kredit pada setiap baris.</p></div>
        <fieldset v-for="(line, index) in form.lines" :key="index" class="journal-line"><legend>Baris {{ index + 1 }}</legend><div class="field"><label :for="`account-${index}`">Akun</label><select :id="`account-${index}`" v-model="line.account" required><option value="">Pilih akun</option><option v-for="account in demoAccounts" :key="account.code" :value="account.code">{{ account.code }} — {{ account.name }}</option></select></div><div class="journal-line-amounts"><div class="field"><label :for="`debit-${index}`">Debit (Rp)</label><InputNumber :input-id="`debit-${index}`" v-model="line.debit" locale="id-ID" :min="0" :max="Number.MAX_SAFE_INTEGER" :max-fraction-digits="0" /></div><div class="field"><label :for="`credit-${index}`">Kredit (Rp)</label><InputNumber :input-id="`credit-${index}`" v-model="line.credit" locale="id-ID" :min="0" :max="Number.MAX_SAFE_INTEGER" :max-fraction-digits="0" /></div><button v-if="form.lines.length > 2" class="icon-button" type="button" :aria-label="`Hapus baris ${index + 1}`" @click="form.lines.splice(index, 1)"><Icon name="x" /></button></div></fieldset>
        <button class="button secondary" type="button" @click="form.lines.push({ account: '', debit: 0, credit: 0 })">Tambah baris akun</button>
        <div class="entry-balance" :class="{ 'entry-balance--valid': hasValidLines(form.lines) }"><dl><dt>Total debit</dt><dd>{{ formatRp(totals.debit) }}</dd><dt>Total kredit</dt><dd>{{ formatRp(totals.credit) }}</dd><dt>Selisih</dt><dd>{{ formatRp(Math.abs(totals.debit - totals.credit)) }}</dd></dl><p><Icon :name="hasValidLines(form.lines) ? 'check-circle' : 'info'" />{{ hasValidLines(form.lines) ? 'Jurnal seimbang. Siap disimpan sebagai draf.' : 'Total debit dan kredit harus sama dan lebih dari nol.' }}</p></div>
        <p v-if="error" ref="errorElement" class="form-error" role="alert" tabindex="-1">{{ error }}</p>
      </form>
    </template>
    <section v-else-if="mode === 'discard'" ref="decisionElement" class="action-decision" tabindex="-1"><Icon name="warning-circle" /><h2>Perubahan belum disimpan</h2><p>Lanjutkan mengisi atau buang perubahan formulir ini. Jurnal sebelumnya tetap seperti semula.</p></section>
    <section v-else-if="mode === 'result'" ref="resultElement" class="preview-result" tabindex="-1"><Icon name="check-circle" /><h2>Simulasi berhasil</h2><p>{{ result }}</p><span v-if="selected" class="status" :class="journalStates[selected.state].tone">{{ journalStates[selected.state].label }}</span></section>
    <section v-else-if="mode === 'confirm' && selected && action" ref="decisionElement" class="action-decision" tabindex="-1"><Icon name="shield-check" /><h2>{{ actions[action] }}?</h2><p>{{ selected.title }}</p><dl><dt>Nomor bukti</dt><dd>{{ selected.code }}</dd><dt>Tanggal</dt><dd>{{ dateLabel(selected.date) }}</dd><dt>Nominal</dt><dd>{{ formatRp(lineTotals(selected.lines).debit) }}</dd></dl><p>{{ action === 'submit' ? 'Status contoh berubah menjadi Menunggu persetujuan.' : 'Status contoh berubah menjadi Tercatat. Jurnal yang tercatat tidak dapat diedit.' }}</p></section>
    <template v-else-if="selected">
      <div ref="detailHeading" class="entry-heading" tabindex="-1"><span class="status" :class="journalStates[selected.state].tone">{{ journalStates[selected.state].label }}</span><h2>{{ selected.title }}</h2><strong>{{ formatRp(lineTotals(selected.lines).debit) }}</strong></div>
      <dl class="record-metadata"><dt>Tanggal transaksi</dt><dd>{{ dateLabel(selected.date) }}</dd><dt>Sumber</dt><dd>{{ journalSources[selected.source] }}</dd><dt>Dibuat oleh</dt><dd>Staf Keuangan (contoh)</dd></dl>
      <h2 class="journal-detail-label">Rincian pencatatan</h2><p class="mobile-table-hint">Geser rincian untuk melihat debit dan kredit.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Akun debit dan kredit"><table class="journal-entry-table"><thead><tr><th scope="col">Akun</th><th scope="col" class="num">Debit</th><th scope="col" class="num">Kredit</th></tr></thead><tbody><tr v-for="(line, index) in selected.lines" :key="index"><td><strong>{{ accountName(line.account) }}</strong><small>{{ line.account }}</small></td><td class="num">{{ formatRp(line.debit) }}</td><td class="num">{{ formatRp(line.credit) }}</td></tr></tbody><tfoot><tr><th scope="row">Total</th><td class="num">{{ formatRp(lineTotals(selected.lines).debit) }}</td><td class="num">{{ formatRp(lineTotals(selected.lines).credit) }}</td></tr></tfoot></table></div>
      <p class="context-note"><Icon name="info" />{{ selected.state === 'POSTED' ? 'Sudah tercatat. Rincian jurnal tidak dapat diedit.' : selected.needsMatching ? 'Cocokkan data penerimaan sebelum melanjutkan pencatatan.' : selected.source !== 'MANUAL' ? 'Dibuat dari transaksi sumber. Perubahan dilakukan melalui transaksi tersebut.' : role === 'Finance' ? 'Draf manual dapat diubah sebelum dicatat ke buku besar.' : 'Penyuntingan draf dilakukan oleh staf keuangan.' }}</p>
      <p v-if="selected.state !== 'POSTED' && !action && !selected.needsMatching" class="context-note">{{ selected.state === 'PENDING' ? 'Menunggu kepala sekolah meninjau dan menyetujui jurnal ini.' : 'Belum ada tindakan pencatatan untuk peran ini.' }}</p>
    </template>
    <template #footer>
      <template v-if="mode === 'edit'"><button class="button secondary" @click="close">Batal</button><button class="button" type="submit" form="entry-form">Simpan draf</button></template>
      <template v-else-if="mode === 'discard'"><button class="button secondary" @click="changeMode('edit')">Lanjutkan mengisi</button><button class="button discard-button" @click="discard">Buang perubahan</button></template>
      <template v-else-if="mode === 'confirm'"><button class="button secondary" @click="changeMode('view')">Kembali ke rincian</button><button v-if="action" class="button" @click="performAction">{{ actions[action] }} (simulasi)</button></template>
      <template v-else-if="mode === 'result'"><button class="button secondary" @click="changeMode('view')">Lihat rincian</button><button class="button" @click="visible = false">Kembali ke daftar</button></template>
      <template v-else><button class="button secondary" @click="close">Tutup</button><button v-if="editable" class="button secondary" @click="edit()">Ubah draf</button><button v-if="action" class="button" @click="changeMode('confirm')">{{ actions[action] }}</button></template>
    </template>
  </Drawer>
</template>
