<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import InputNumber from "primevue/inputnumber"
import Select from "primevue/select"
import MultiSelect from "primevue/multiselect"
import DatePicker from "primevue/datepicker"
import Checkbox from "primevue/checkbox"
import ToggleSwitch from "primevue/toggleswitch"
import Textarea from "primevue/textarea"
import Password from "primevue/password"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Tag from "primevue/tag"
import Message from "primevue/message"
import Tabs from "primevue/tabs"
import TabList from "primevue/tablist"
import Tab from "primevue/tab"
import TabPanels from "primevue/tabpanels"
import TabPanel from "primevue/tabpanel"
import Drawer from "primevue/drawer"
import { useToast } from "primevue/usetoast"
import { useConfirm } from "primevue/useconfirm"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import { formatRp } from "@/core/format"
import { journalStates, lineTotals, type DemoJournal } from "../design-preview/journal-preview"

const props = defineProps<{ rows: DemoJournal[] }>()
const emit = defineEmits<{ openForm: []; openRow: [row: DemoJournal] }>()
const toast = useToast()
const confirm = useConfirm()
const keyword = ref("")
const status = ref<string | null>(null)
const density = ref<"comfortable" | "compact">("comfortable")
const first = ref(0)
const date = ref<Date | null>(null)
const account = ref<string | null>(null)
const groups = ref<string[]>([])
const checked = ref(false)
const active = ref(true)
const note = ref("")
const password = ref("")
const amount = ref<number | null>(1250.5)
const month = ref(10)
const year = ref(2026)
const drawer = ref(false)
const drawerTrigger = ref<{ $el: HTMLButtonElement } | null>(null)
const proof = ref("BKT-001")
const tableLoading = ref(false)
const iconNames = ["squares-four", "wallet", "book-open", "student", "calendar-blank", "magnifying-glass", "funnel", "file-text", "check-circle", "warning-circle", "printer", "trash", "plus", "x"]
const statusOptions = Object.entries(journalStates).map(([value, state]) => ({ value, label: state.label }))
const filtered = computed(() => props.rows.filter((row) => (!status.value || row.state === status.value)
  && `${row.code} ${row.title}`.toLowerCase().includes(keyword.value.trim().toLowerCase())))
watch([keyword, status], () => { first.value = 0 })
function exampleToast() {
  toast.add({ severity: "success", summary: "Contoh notifikasi", detail: "Ini contoh pesan berhasil. Data sekolah tidak berubah.", life: 5000 })
}
function exampleConfirmation() {
  confirm.require({
    header: "Batalkan contoh?", message: "Ini spesimen konfirmasi. Tidak ada transaksi sekolah yang dibatalkan.",
    acceptLabel: "Batalkan contoh", rejectLabel: "Kembali", acceptProps: { severity: "danger" },
    accept: () => toast.add({ severity: "info", summary: "Contoh dibatalkan", detail: "Tidak ada perubahan data sekolah.", life: 5000 }),
  })
}
</script>

<template>
  <section id="komponen" class="system-section">
    <header class="system-section-heading">
      <h2>Komponen yang dipakai aplikasi.</h2>
      <p>PrimeVue styled dengan BeePreset yang sama. Klik kontrol untuk memeriksa popup, fokus, validasi visual, dan pilihan. Semua data di sini contoh.</p>
    </header>
    <div class="component-board">
      <div class="component-line">
        <span class="spec-label">Tindakan</span>
        <div class="spec-controls">
          <Button label="Catat pembayaran" @click="emit('openForm')"><template #icon><Icon name="wallet" /></template></Button>
          <Button label="Buka contoh dialog" severity="secondary" @click="emit('openForm')" />
          <Button label="Lihat pola form" text @click="emit('openForm')" />
          <Button label="Simpan pembayaran" disabled />
          <Button label="Menyimpan contoh" loading disabled />
          <Button aria-label="Buka contoh form" severity="secondary" @click="emit('openForm')"><template #icon><Icon name="eye" /></template></Button>
        </div>
      </div>
      <div class="component-line">
        <span class="spec-label">Ukuran</span>
        <div class="spec-controls">
          <Button label="Ringkas desktop / 36 px" severity="secondary" class="bee-button-compact" @click="emit('openForm')" />
          <Button label="Utama / 44 px" severity="secondary" @click="emit('openForm')" />
          <span class="component-hint">Kontrol ringkas kembali minimum 44 px di mobile.</span>
        </div>
      </div>
      <div class="component-line">
        <span class="spec-label">Form</span>
        <div class="workbench-fields">
          <div class="bee-field"><label for="sample-name">Nama siswa</label><InputText id="sample-name" placeholder="Cari nama atau NIS" /><small>Label tetap terlihat ketika mengetik.</small></div>
          <div class="bee-field"><label for="sample-account">Kas/Bank penerima</label><Select input-id="sample-account" v-model="account" :options="['Kas di Bank', 'Kas di Tangan']" filter show-clear placeholder="Pilih Kas/Bank"><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
          <div class="bee-field"><label for="sample-date">Tanggal pembayaran</label><DatePicker input-id="sample-date" v-model="date" date-format="dd/mm/yy" show-icon show-button-bar fluid><template #dropdownicon><Icon name="calendar-blank" /></template></DatePicker><small>Tanggal tampilan mengikuti format Indonesia.</small></div>
          <div class="bee-field"><label for="sample-amount">Nominal contoh (Rp)</label><InputNumber input-id="sample-amount" v-model="amount" locale="id-ID" :min="0" :max-fraction-digits="2" fluid /><small>Desimal tetap didukung. Contoh: 1.250,50.</small></div>
          <div class="bee-field"><label for="sample-proof">Nomor bukti penerimaan</label><InputText id="sample-proof" v-model="proof" invalid aria-invalid="true" aria-describedby="proof-help" /><small id="proof-help" class="field-error"><Icon name="warning-circle" />Nomor bukti sudah digunakan. Periksa riwayatnya.</small></div>
          <div class="bee-field"><label for="sample-groups">Kelompok siswa</label><MultiSelect input-id="sample-groups" v-model="groups" :options="['Playgroup', 'TK A', 'TK B']" filter placeholder="Pilih kelompok" display="chip" /><small>Contoh pilihan lebih dari satu kelompok.</small></div>
          <div class="bee-field"><label for="sample-note">Keterangan</label><Textarea id="sample-note" v-model="note" rows="3" auto-resize /></div>
          <div class="bee-field"><label for="sample-password">Kata sandi contoh</label><Password input-id="sample-password" v-model="password" :feedback="false" toggle-mask fluid autocomplete="new-password" /></div>
          <div class="workbench-checks"><Checkbox input-id="sample-check" v-model="checked" binary /><label for="sample-check">Bukti sudah diperiksa</label><ToggleSwitch input-id="sample-active" v-model="active" /><label for="sample-active">Tampilkan data aktif</label></div>
          <div class="bee-field"><span class="spec-label">Periode laporan</span><PeriodPicker v-model:bulan="month" v-model:tahun="year" /></div>
        </div>
      </div>
      <div class="component-line">
        <span class="spec-label">Pesan dan lapisan</span>
        <div class="workbench-feedback">
          <Message severity="info" :closable="false"><template #icon><Icon name="info" /></template>Periksa nominal dan bukti sebelum mencatat.</Message>
          <Message severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>Pembayaran lama perlu dicocokkan sebelum dilanjutkan.</Message>
          <div class="spec-controls"><Button label="Lihat notifikasi" severity="secondary" @click="exampleToast" /><Button label="Contoh konfirmasi" severity="secondary" @click="exampleConfirmation" /><Button ref="drawerTrigger" label="Buka menu mobile" severity="secondary" @click="drawer = true" /></div>
        </div>
      </div>
      <div class="component-line">
        <span class="spec-label">Tab</span>
        <Tabs value="0"><TabList><Tab value="0">Rincian</Tab><Tab value="1">Riwayat</Tab></TabList><TabPanels><TabPanel value="0">Nominal dan akun berada pada rincian. Ini contoh tab yang dapat digunakan lewat keyboard.</TabPanel><TabPanel value="1">Belum ada perubahan pada record contoh ini.</TabPanel></TabPanels></Tabs>
      </div>
      <div class="component-line"><span class="spec-label">Ikon</span><div><div class="icon-specimens"><div v-for="name in iconNames" :key="name" :title="name"><Icon :name="name" /></div></div><p class="component-hint">Phosphor Regular, aset resmi lokal dan MIT. Ikon 20 px; label tindakan tetap tertulis.</p></div></div>
    </div>
  </section>

  <section id="data" class="system-section">
    <header class="system-section-heading"><h2>Tabel yang siap menerima data.</h2><p>DataTable menggunakan pagination dan sorting bawaan. Pencarian contoh menyaring seluruh tujuh record lokal; pagination server pada jurnal aplikasi tetap mengikuti endpoint.</p></header>
    <div class="bee-panel workbench-table">
      <div class="table-toolbar">
        <div class="bee-field"><label for="sample-journal-search">Cari jurnal contoh</label><SearchField input-id="sample-journal-search" v-model="keyword" placeholder="Nomor bukti atau keterangan" hint="Cari jurnal contoh" /></div>
        <div class="bee-field"><label for="sample-status">Status</label><Select input-id="sample-status" v-model="status" :options="statusOptions" option-label="label" option-value="value" placeholder="Semua status" show-clear /></div>
        <div class="bee-segmented" role="group" aria-label="Kepadatan tabel"><button :aria-pressed="density === 'comfortable'" @click="density = 'comfortable'">Nyaman</button><button :aria-pressed="density === 'compact'" @click="density = 'compact'">Ringkas</button></div>
        <div class="workbench-checks"><ToggleSwitch input-id="sample-table-loading" v-model="tableLoading" /><label for="sample-table-loading">Contoh memuat</label></div>
      </div>
      <p class="table-results" role="status">{{ filtered.length }} jurnal contoh</p>
      <p class="workbench-scroll-hint">Geser tabel untuk melihat semua kolom pada layar kecil.</p>
      <DataTable :value="filtered" :loading="tableLoading" paginator :rows="5" :first="first" @page="first = $event.first" data-key="code" :size="density === 'compact' ? 'small' : undefined" :table-style="{ minWidth: '780px' }" :pt="{ tableContainer: { tabindex: 0, role: 'region', 'aria-label': 'Tabel jurnal contoh' } }">
        <template #empty>Tidak ada jurnal yang sesuai. Ubah kata kunci atau status.</template>
        <Column field="title" header="Transaksi" sortable><template #body="{ data }"><strong>{{ data.title }}</strong><small class="workbench-record-code">{{ data.code }}</small></template></Column>
        <Column field="date" header="Tanggal" sortable><template #body="{ data }">{{ data.date.split('-').reverse().join('/') }}</template></Column>
        <Column header="Nominal" header-class="bee-numeric" body-class="bee-numeric"><template #body="{ data }">{{ formatRp(lineTotals(data.lines).debit) }}</template></Column>
        <Column header="Status"><template #body="{ data }"><Tag :value="journalStates[data.state as keyof typeof journalStates].label" :severity="data.state === 'POSTED' ? 'success' : data.state === 'PENDING' ? 'warn' : 'secondary'" /></template></Column>
        <Column header="Aksi"><template #body="{ data }"><Button label="Periksa" text :aria-label="`Buka contoh ${data.code}`" @click="emit('openRow', data)" /></template></Column>
        <template #paginatorfirstpagelinkicon><Icon name="arrow-left" /></template><template #paginatorprevpagelinkicon><Icon name="caret-left" /></template><template #paginatornextpagelinkicon><Icon name="caret-right" /></template><template #paginatorlastpagelinkicon><Icon name="arrow-right" /></template>
      </DataTable>
      <div class="table-footnote"><Icon name="info" />Draf belum masuk buku besar. Nilai yang belum diketahui tetap ditandai dan tidak diubah menjadi nol.</div>
    </div>
    <div class="semantic-strip"><Tag value="Draf" severity="secondary" /><Tag value="Menunggu persetujuan" severity="warn" /><Tag value="Tercatat" severity="success" /><Tag value="Dibatalkan" severity="danger" /><Tag value="Perlu dicocokkan" severity="warn" /></div>
  </section>
  <Drawer v-model:visible="drawer" @after-hide="drawerTrigger?.$el.focus()" header="Navigasi contoh" :style="{ width: 'min(320px, 100vw)' }"><template #closeicon><Icon name="x" /></template><p>Contoh lapisan navigasi dengan Escape dan pengembalian fokus.</p><Button label="Tutup menu contoh" severity="secondary" @click="drawer = false" /></Drawer>
</template>

<style scoped>
.workbench-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--bee-space-5); }
.workbench-checks { display: flex; align-items: center; gap: var(--bee-space-3); flex-wrap: wrap; font-size: var(--bee-type-ui); }
.workbench-checks label { cursor: pointer; }
.workbench-feedback { display: grid; gap: var(--bee-space-4); }
.workbench-record-code { display: block; margin-top: var(--bee-space-1); color: var(--bee-color-muted); font-size: var(--bee-type-caption); }
.workbench-table :deep(.p-datatable) { font-size: var(--bee-type-ui); }
.workbench-table :deep(.p-datatable-tbody strong) { font-weight: 500; }
.workbench-table :deep(.p-datatable-tbody > tr > td) { height: var(--bee-size-row-multiline); padding-block: var(--bee-space-3); }
.workbench-table :deep(.p-datatable-sm .p-datatable-tbody > tr > td) { height: var(--bee-size-row-compact-multiline); padding-block: 6px; }
.workbench-scroll-hint { display: none; font-size: var(--bee-type-caption); color: var(--bee-color-muted); padding-inline: var(--bee-space-5); }
@media (max-width: 680px) { .workbench-fields { grid-template-columns: minmax(0, 1fr); }.workbench-scroll-hint { display: block; }.table-toolbar > .bee-field { flex: 1 1 100%; } }
</style>
