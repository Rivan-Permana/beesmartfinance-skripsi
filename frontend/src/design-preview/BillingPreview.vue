<script setup lang="ts">
import { computed, nextTick, reactive, ref } from "vue"
import Drawer from "primevue/drawer"
import InputNumber from "primevue/inputnumber"
import type { Role } from "@/types/api"
import { formatRp } from "@/core/format"
import Icon from "./PhosphorIcon.vue"
import { billStatus, billTotals, canPayBill, createDemoBills, paymentAccounts, validAllocation, type Allocation, type DemoBill, type DemoPayment } from "./billing-preview"

const props = defineProps<{ role: Role; outstanding: boolean; student?: string | null; initialId?: string | null }>()
const rows = ref(createDemoBills())
const query = ref(props.student ?? "")
const status = ref("")
const selected = ref<DemoBill | null>(null)
const payment = ref<DemoPayment | null>(null)
const mode = ref<"detail" | "payment" | "confirm" | "discard" | "result">("detail")
const visible = ref(false)
const original = ref("")
const error = ref("")
const announcement = ref("")
const focusTarget = ref<HTMLElement | null>(null)
const listHeading = ref<HTMLElement | null>(null)
let trigger: HTMLElement | null = null
const form = reactive({ date: "2026-10-15", proof: "", account: "", allocations: [] as Allocation[] })
const dirty = computed(() => JSON.stringify(form) !== original.value)
const drawerVisible = computed({ get: () => visible.value, set: (value) => { if (!value) close() } })
const scope = computed(() => rows.value.filter((bill) => !props.outstanding || billTotals(bill).remaining === null || billTotals(bill).remaining! > 0))
const filtered = computed(() => scope.value.filter((bill) => (!status.value || billStatus(bill).value === status.value)
  && `${bill.student} ${bill.studentId} ${bill.group} ${bill.id}`.toLocaleLowerCase("id").includes(query.value.trim().toLocaleLowerCase("id"))))
const known = computed(() => filtered.value.reduce((sum, bill) => sum + (billTotals(bill).remaining ?? 0), 0))
const unknown = computed(() => filtered.value.filter((bill) => billTotals(bill).remaining === null).length)
const amount = computed(() => form.allocations.reduce((sum, allocation) => sum + Number(allocation.amount), 0))
const selectedTotals = computed(() => selected.value ? billTotals(selected.value) : null)
function money(value: number | null) { return value === null ? "Belum diketahui" : formatRp(value) }
function dateLabel(value: string) { return new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00`)) }
function componentLabel(id: string) { return selected.value?.components.find((line) => line.id === id)?.label ?? id }
function accountLabel(code: string) { return paymentAccounts.find((account) => account.code === code)?.name ?? code }
function remaining(id: string) { const line = selected.value?.components.find((component) => component.id === id); return line && line.paid !== null ? line.total - line.paid : 0 }
function reset() { query.value = ""; status.value = "" }
function open(bill: DemoBill) {
  trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
  selected.value = bill; mode.value = "detail"; visible.value = true; error.value = ""
}
async function changeMode(value: "detail" | "confirm" | "discard" | "payment" | "result") {
  mode.value = value
  await nextTick()
  if (value === "payment") document.getElementById("bill-proof")?.focus()
  else focusTarget.value?.focus()
}
async function startPayment() {
  if (!selected.value || !canPayBill(selected.value, props.role)) return
  Object.assign(form, { date: "2026-10-15", proof: "", account: "", allocations: selected.value.components.filter((line) => line.paid !== null && line.total > line.paid).map((line) => ({ component: line.id, amount: 0 })) })
  original.value = JSON.stringify(form); error.value = ""
  await changeMode("payment")
}
function close() { if (["payment", "confirm"].includes(mode.value) && dirty.value) void changeMode("discard"); else visible.value = false }
function restoreFocus() { (trigger?.isConnected ? trigger : listHeading.value)?.focus() }
async function reviewPayment() {
  const bill = selected.value
  if (!bill || !canPayBill(bill, props.role)) return
  const date = new Date(`${form.date}T12:00:00Z`)
  let message = ""
  if (!form.proof.trim() || !paymentAccounts.some((account) => account.code === form.account)) message = "Isi nomor bukti dan pilih Kas/Bank penerima."
  else if (!/^\d{4}-\d{2}-\d{2}$/.test(form.date) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== form.date) message = "Pilih tanggal penerimaan yang valid."
  else if (rows.value.some((row) => row.payments.some((record) => record.proof.toLocaleLowerCase("id") === form.proof.trim().toLocaleLowerCase("id")))) message = "Nomor bukti sudah digunakan dalam contoh ini. Periksa riwayat sebelum mencatat pembayaran baru."
  else if (!validAllocation(bill, form.allocations)) message = "Isi alokasi pembayaran dengan rupiah bulat. Total harus lebih dari nol dan setiap komponen tidak boleh melebihi sisanya."
  if (message) { error.value = message; await nextTick(); document.getElementById("bill-error")?.focus(); return }
  error.value = ""
  await changeMode("confirm")
}
async function savePayment() {
  const bill = selected.value
  if (mode.value !== "confirm" || !bill || !canPayBill(bill, props.role) || !validAllocation(bill, form.allocations)) return
  if (rows.value.some((row) => row.payments.some((record) => record.proof.toLocaleLowerCase("id") === form.proof.trim().toLocaleLowerCase("id")))) return
  const receipt: DemoPayment = {
    proof: form.proof.trim(), date: form.date, account: form.account, amount: amount.value,
    allocations: form.allocations.filter((allocation) => Number(allocation.amount) > 0).map((allocation) => ({ ...allocation, amount: Number(allocation.amount) })),
    journal: `SIM-JRN-${String(rows.value.reduce((count, row) => count + row.payments.length, 0) + 1).padStart(3, "0")}`,
  }
  receipt.allocations.forEach((allocation) => { const line = bill.components.find((component) => component.id === allocation.component)!; line.paid = line.paid! + allocation.amount })
  bill.payments.unshift(receipt); payment.value = receipt
  announcement.value = `${receipt.proof}: pembayaran ${formatRp(receipt.amount)} untuk ${bill.student} berhasil disimulasikan.`
  await changeMode("result")
}
const initial = scope.value.find((bill) => bill.id === props.initialId)
if (initial) { selected.value = initial; visible.value = true }
</script>

<template>
  <section class="billing-workspace" aria-label="Tagihan dan pembayaran">
    <p v-if="role !== 'Administration'" class="inline-info"><Icon name="shield-check" />Akses baca-saja. Pencatatan pembayaran dilakukan oleh staf tata usaha.</p>
    <p v-if="announcement" class="preview-feedback" role="status"><Icon name="check-circle" />{{ announcement }}</p>
    <div class="billing-summary"><div><span>Sisa terverifikasi pada hasil</span><strong>{{ formatRp(known) }}</strong><small>Nilai yang belum diketahui tidak masuk jumlah ini.</small></div><div><span>Perlu dicocokkan</span><strong>{{ unknown }} <small>tagihan</small></strong><small>Periksa bukti penerimaan sebelumnya.</small></div></div>
    <section class="panel billing-list-panel"><div class="journal-filters"><div class="field search-field"><label for="billing-search">Cari tagihan</label><div class="input-icon"><Icon name="magnifying-glass" /><input id="billing-search" v-model="query" type="search" placeholder="Nama, NIS, kelompok, atau nomor tagihan"></div></div><div class="field"><label for="billing-status">Status pembayaran</label><select id="billing-status" v-model="status"><option value="">Semua status</option><option value="unpaid">Belum bayar</option><option value="partial">Sebagian dibayar</option><option v-if="!outstanding" value="paid">Lunas</option><option value="matching">Perlu dicocokkan</option></select></div><button class="button secondary" @click="reset">Atur ulang</button></div>
      <div class="journal-list-context"><h2 ref="listHeading" tabindex="-1">{{ filtered.length }} tagihan ditampilkan</h2><span>Oktober 2026 · data contoh</span></div>
      <div v-if="filtered.length" class="table-scroll billing-table-desktop" tabindex="0" role="region" aria-label="Daftar tagihan"><table><thead><tr><th scope="col">Siswa dan tagihan</th><th scope="col" class="num">Total</th><th scope="col" class="num">Diterima</th><th scope="col" class="num">Sisa</th><th scope="col">Status</th><th scope="col">Aksi</th></tr></thead><tbody><tr v-for="bill in filtered" :key="bill.id"><td><strong>{{ bill.student }}</strong><small>{{ bill.group }} · {{ bill.id }}</small></td><td class="num">{{ money(billTotals(bill).total) }}</td><td class="num">{{ money(billTotals(bill).paid) }}</td><td class="num">{{ money(billTotals(bill).remaining) }}</td><td><span class="status" :class="billStatus(bill).tone">{{ billStatus(bill).label }}</span></td><td><button class="row-action" :aria-label="`Buka ${bill.id}`" @click="open(bill)">Lihat rincian<Icon name="caret-right" /></button></td></tr></tbody></table></div>
      <ul v-if="filtered.length" class="billing-mobile-rows" aria-label="Tagihan pada perangkat kecil"><li v-for="bill in filtered" :key="bill.id"><div class="record-mobile-meta"><span class="status" :class="billStatus(bill).tone">{{ billStatus(bill).label }}</span><span>{{ bill.group }}</span></div><h3>{{ bill.student }}</h3><p>{{ bill.id }}</p><dl><dt>Total tagihan</dt><dd>{{ money(billTotals(bill).total) }}</dd><dt>Diterima</dt><dd>{{ money(billTotals(bill).paid) }}</dd><dt>Sisa</dt><dd>{{ money(billTotals(bill).remaining) }}</dd></dl><button class="row-action" :aria-label="`Buka ${bill.id}`" @click="open(bill)">Lihat rincian<Icon name="caret-right" /></button></li></ul>
      <div v-else class="filtered-empty"><Icon name="file-text" /><h2>Tagihan tidak ditemukan</h2><p>Coba nama atau status lain, lalu periksa kembali hasilnya.</p><button class="button secondary" @click="reset">Atur ulang pencarian</button></div>
      <p class="panel-note"><Icon name="info" />Simulasi di halaman ini. Memuat ulang atau berpindah halaman mengembalikan data contoh.</p>
    </section>
  </section>
  <Drawer v-model:visible="drawerVisible" position="right" :header="mode === 'payment' ? 'Catat pembayaran' : selected?.id ?? 'Rincian tagihan'" aria-label="Rincian tagihan dan pembayaran" @after-hide="restoreFocus" :close-button-props="{ class: 'icon-button', 'aria-label': 'Tutup tagihan' }" :pt="{ mask: { class: 'overlay-mask detail-mask' }, root: { class: 'detail-drawer' }, header: { class: 'overlay-header' }, content: { class: 'overlay-content' }, footer: { class: 'overlay-footer detail-drawer-footer' } }">
    <template #closeicon><Icon name="x" /></template>
    <p class="demo-notice"><Icon name="eye" />Simulasi desain. Tidak mengubah data sekolah.</p>
    <template v-if="selected && selectedTotals">
      <form v-if="mode === 'payment'" id="billing-form" class="entry-form" @submit.prevent="reviewPayment">
        <div><h2>{{ selected.student }}</h2><p class="billing-muted">{{ selected.period }} · sisa {{ money(selectedTotals.remaining) }}</p></div>
        <div class="form-grid"><div class="field"><label for="bill-proof">Nomor bukti penerimaan *</label><input id="bill-proof" v-model="form.proof" required maxlength="100" placeholder="Contoh: CONTOH-PBY-002" autofocus></div><div class="field"><label for="bill-date">Tanggal penerimaan *</label><input id="bill-date" v-model="form.date" type="date" required></div></div>
        <div class="field"><label for="bill-account">Kas/Bank penerima *</label><select id="bill-account" v-model="form.account" required><option value="">Pilih Kas/Bank</option><option v-for="account in paymentAccounts" :key="account.code" :value="account.code">{{ account.code }} — {{ account.name }}</option></select></div>
        <div class="billing-allocation-heading"><div><h2>Alokasi per komponen</h2><p class="billing-muted">Isi pembayaran sesuai komponen yang diterima.</p></div><button class="row-action" type="button" @click="form.allocations.forEach((allocation) => allocation.amount = remaining(allocation.component))">Isi seluruh sisa</button></div>
        <div v-for="allocation in form.allocations" :key="allocation.component" class="billing-allocation"><div><label :for="`allocation-${allocation.component}`">{{ componentLabel(allocation.component) }}</label><small>Sisa {{ formatRp(remaining(allocation.component)) }}</small></div><InputNumber :input-id="`allocation-${allocation.component}`" v-model="allocation.amount" locale="id-ID" :min="0" :max="Number.MAX_SAFE_INTEGER" :max-fraction-digits="0" /></div>
        <div class="entry-balance"><dl><dt>Total diterima</dt><dd>{{ formatRp(amount) }}</dd><dt>Sisa setelah pembayaran</dt><dd>{{ selectedTotals.remaining !== null && amount > selectedTotals.remaining ? 'Melebihi sisa tagihan' : money(selectedTotals.remaining === null ? null : selectedTotals.remaining - amount) }}</dd></dl><p>Pembayaran akan membentuk jurnal draf untuk ditindaklanjuti Finance pada aplikasi.</p></div>
        <p v-if="error" id="bill-error" class="form-error" role="alert" tabindex="-1">{{ error }}</p>
      </form>
      <section v-else-if="mode === 'discard'" ref="focusTarget" class="action-decision" tabindex="-1"><Icon name="warning-circle" /><h2>Pembayaran belum disimpan</h2><p>Lanjutkan mengisi atau buang perubahan formulir. Riwayat pembayaran sebelumnya tetap seperti semula.</p></section>
      <section v-else-if="mode === 'confirm'" ref="focusTarget" class="action-decision" tabindex="-1"><Icon name="shield-check" /><h2>Periksa pembayaran</h2><p>{{ selected.student }} · {{ selected.period }}</p><dl><dt>Nomor bukti</dt><dd>{{ form.proof }}</dd><dt>Tanggal</dt><dd>{{ dateLabel(form.date) }}</dd><dt>Penerima</dt><dd>{{ accountLabel(form.account) }}</dd><dt>Total diterima</dt><dd>{{ formatRp(amount) }}</dd></dl><ul class="billing-confirm-lines"><li v-for="allocation in form.allocations.filter((item) => Number(item.amount) > 0)" :key="allocation.component"><span>{{ componentLabel(allocation.component) }}</span><strong>{{ formatRp(allocation.amount) }}</strong></li></ul><p>Simpan akan memperbarui tagihan contoh. Tidak ada pembayaran nyata yang dicatat.</p></section>
      <section v-else-if="mode === 'result' && payment" ref="focusTarget" class="preview-result" tabindex="-1"><Icon name="check-circle" /><h2>Pembayaran berhasil disimulasikan</h2><p>{{ payment.proof }} · {{ selected.student }}</p><dl><dt>Diterima kali ini</dt><dd>{{ formatRp(payment.amount) }}</dd><dt>Sisa tagihan</dt><dd>{{ money(selectedTotals.remaining) }}</dd><dt>Jurnal draf contoh</dt><dd>{{ payment.journal }}</dd></dl><span class="status" :class="billStatus(selected).tone">{{ billStatus(selected).label }}</span><p>Hasil ini hanya di halaman preview. Jurnal tidak dikirim ke Finance atau backend.</p></section>
      <template v-else>
        <div ref="focusTarget" class="entry-heading" tabindex="-1"><span class="status" :class="billStatus(selected).tone">{{ billStatus(selected).label }}</span><h2>{{ selected.student }}</h2><p class="billing-muted">{{ selected.group }} · {{ selected.period }}</p><strong>{{ money(selectedTotals.remaining) }}</strong><p class="billing-muted">Sisa tagihan</p></div>
        <dl class="record-metadata"><dt>Total tagihan</dt><dd>{{ money(selectedTotals.total) }}</dd><dt>Sudah diterima</dt><dd>{{ money(selectedTotals.paid) }}</dd><dt>NIS</dt><dd>{{ selected.studentId }}</dd></dl>
        <p v-if="selectedTotals.remaining === null" class="billing-matching-note"><Icon name="warning-circle" />Pembayaran lama belum terverifikasi. Cocokkan bukti penerimaan bersama tata usaha sebelum menerima pembayaran baru. Nilai belum diketahui tidak dianggap nol.</p>
        <h2>Komponen tagihan</h2><ul class="billing-components"><li v-for="line in selected.components" :key="line.id"><strong>{{ line.label }}</strong><dl><dt>Tagihan</dt><dd>{{ formatRp(line.total) }}</dd><dt>Diterima</dt><dd>{{ money(line.paid) }}</dd><dt>Sisa</dt><dd>{{ money(line.paid === null ? null : line.total - line.paid) }}</dd></dl></li></ul>
        <div class="billing-history-heading"><h2>Riwayat pembayaran</h2><span>{{ selected.payments.length }} bukti contoh</span></div><ul v-if="selected.payments.length" class="billing-history"><li v-for="record in selected.payments" :key="record.proof"><div><strong>{{ record.proof }}</strong><small>{{ dateLabel(record.date) }} · {{ accountLabel(record.account) }}</small></div><b>{{ formatRp(record.amount) }}</b><p v-for="allocation in record.allocations" :key="allocation.component">{{ componentLabel(allocation.component) }}: {{ formatRp(allocation.amount) }}</p><small>Referensi jurnal draf contoh: {{ record.journal }}</small></li></ul><p v-else class="billing-history-empty">{{ selectedTotals.remaining === null ? 'Riwayat lama belum dapat dipastikan. Ini tidak berarti belum pernah ada pembayaran.' : 'Belum ada pembayaran pada contoh ini.' }}</p>
        <p v-if="role !== 'Administration'" class="context-note"><Icon name="eye" />Rincian bersifat baca-saja. Hubungi tata usaha untuk pencatatan pembayaran.</p>
      </template>
    </template>
    <template #footer>
      <template v-if="mode === 'payment'"><button class="button secondary" @click="close">Batal</button><button class="button" type="submit" form="billing-form">Periksa pembayaran</button></template>
      <template v-else-if="mode === 'discard'"><button class="button secondary" @click="changeMode('payment')">Lanjutkan mengisi</button><button class="button discard-button" @click="changeMode('detail')">Buang perubahan</button></template>
      <template v-else-if="mode === 'confirm'"><button class="button secondary" @click="changeMode('payment')">Kembali ke form</button><button class="button" @click="savePayment">Simpan pembayaran (simulasi)</button></template>
      <template v-else-if="mode === 'result'"><button class="button secondary" @click="changeMode('detail')">Lihat rincian</button><button class="button" @click="visible = false">Kembali ke daftar</button></template>
      <template v-else><button class="button secondary" @click="close">Tutup</button><button v-if="selected && canPayBill(selected, role)" class="button" @click="startPayment">Catat pembayaran</button></template>
    </template>
  </Drawer>
</template>
