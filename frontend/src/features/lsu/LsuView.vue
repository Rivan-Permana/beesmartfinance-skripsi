<script setup lang="ts">
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"
import { RouterLink } from "vue-router"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { formatLocalDate, formatRp } from "@/core/format"
import { siswaApi } from "@/features/siswa/api"
import Icon from "@/shared/components/PhosphorIcon.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import SearchField from "@/shared/components/SearchField.vue"
import type { PaketLSU, Siswa } from "@/types/api"
import { lsuApi } from "./api"
import { JUMLAH_SESI_OPTIONS, paketState, siswaPunyaPaketBerjalan, sisaSesi, tagihanState, urutkanPaket } from "./presentation"

const toast = useToast()
const confirm = useConfirm()
const rows = ref<PaketLSU[]>([])
const siswa = ref<Siswa[]>([])
const loading = ref(false)
const error = ref("")
const query = ref("")
const terbuka = ref<number | null>(null)

const tampil = computed(() => {
  const q = query.value.trim().toLocaleLowerCase("id-ID")
  return urutkanPaket(rows.value).filter((p) => !q || p.siswa_nama.toLocaleLowerCase("id-ID").includes(q))
})
const siswaOptions = computed(() => siswa.value.map((s) => ({ label: s.nama, value: s.id })))
const tanggal = (iso: string) => iso.split("-").reverse().join("/")

async function load() {
  loading.value = true
  error.value = ""
  try {
    ;[rows.value, siswa.value] = await Promise.all([lsuApi.listAll(), siswaApi.listAll({ status: "aktif" })])
  } catch (cause) {
    const message = friendlyError(cause, "Data LSU belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally {
    loading.value = false
  }
}
function ganti(paket: PaketLSU) {
  rows.value = rows.value.map((p) => (p.id === paket.id ? paket : p))
}

const paketDialog = ref(false)
const saving = ref(false)
const paketError = ref("")
const paketForm = reactive<{ siswa: number | null; jumlah_sesi: 8 | 16; harga: number | null; tanggal_mulai: Date | null; keterangan: string }>({
  siswa: null, jumlah_sesi: 8, harga: null, tanggal_mulai: new Date(), keterangan: "",
})
const masihBerjalan = computed(() => siswaPunyaPaketBerjalan(rows.value, paketForm.siswa))
function bukaPaket() {
  Object.assign(paketForm, { siswa: null, jumlah_sesi: 8, harga: null, tanggal_mulai: new Date(), keterangan: "" })
  paketError.value = ""
  paketDialog.value = true
}
async function simpanPaket() {
  if (!paketForm.siswa || !paketForm.harga || paketForm.harga <= 0 || !paketForm.tanggal_mulai) {
    paketError.value = "Pilih siswa, jumlah pertemuan, harga paket, dan tanggal mulai."
    return
  }
  saving.value = true
  paketError.value = ""
  try {
    const paket = await lsuApi.create({
      siswa: paketForm.siswa, jumlah_sesi: paketForm.jumlah_sesi, harga: paketForm.harga.toFixed(2),
      tanggal_mulai: formatLocalDate(paketForm.tanggal_mulai), keterangan: paketForm.keterangan.trim(),
    })
    rows.value = [paket, ...rows.value]
    paketDialog.value = false
    notifySuccess(toast, `Paket ${paket.jumlah_sesi} pertemuan dibuat. Tagihannya muncul di menu Tagihan.`)
  } catch (cause) {
    const message = friendlyError(cause, "Paket belum tersimpan")
    paketError.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally {
    saving.value = false
  }
}

const sesiTarget = ref<PaketLSU | null>(null)
const sesiError = ref("")
const sesiForm = reactive<{ tanggal: Date | null; catatan: string }>({ tanggal: new Date(), catatan: "" })
function bukaSesi(paket: PaketLSU) {
  sesiTarget.value = paket
  sesiForm.tanggal = new Date()
  sesiForm.catatan = ""
  sesiError.value = ""
}
async function simpanSesi() {
  if (!sesiTarget.value || !sesiForm.tanggal) { sesiError.value = "Pilih tanggal pertemuan."; return }
  saving.value = true
  sesiError.value = ""
  try {
    const paket = await lsuApi.catatPertemuan(sesiTarget.value.id, { tanggal: formatLocalDate(sesiForm.tanggal), catatan: sesiForm.catatan.trim() })
    ganti(paket)
    sesiTarget.value = null
    notifySuccess(toast, sisaSesi(paket) ? `Pertemuan dicatat. Sisa ${sisaSesi(paket)} sesi.` : "Pertemuan dicatat. Sesi paket ini sudah habis.")
  } catch (cause) {
    const message = friendlyError(cause, "Pertemuan belum tersimpan")
    sesiError.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally {
    saving.value = false
  }
}

function hapusPertemuan(paket: PaketLSU, pertemuan: PaketLSU["pertemuan"][number]) {
  confirm.require({
    header: "Hapus catatan pertemuan?",
    message: `Hapus pertemuan ${tanggal(pertemuan.tanggal)} untuk ${paket.siswa_nama}? Sesinya kembali tersedia.`,
    rejectLabel: "Batal", acceptLabel: "Hapus", acceptClass: "p-button-danger",
    accept: async () => {
      try { ganti(await lsuApi.hapusPertemuan(paket.id, pertemuan.id)); notifySuccess(toast, "Catatan pertemuan dihapus") }
      catch (cause) { notifyError(toast, cause, "Catatan pertemuan belum terhapus") }
    },
  })
}
function hapusPaket(paket: PaketLSU) {
  confirm.require({
    header: "Hapus paket LSU?",
    message: `Hapus paket ${paket.jumlah_sesi} pertemuan ${paket.siswa_nama} beserta tagihannya? Hanya bisa bila belum ada pertemuan dan penerimaan.`,
    rejectLabel: "Batal", acceptLabel: "Hapus", acceptClass: "p-button-danger",
    accept: async () => {
      try { await lsuApi.remove(paket.id); rows.value = rows.value.filter((p) => p.id !== paket.id); notifySuccess(toast, "Paket dan tagihannya dihapus") }
      catch (cause) { notifyError(toast, cause, "Paket belum terhapus") }
    },
  })
}

onMounted(load)
</script>

<template>
  <PageLayout title="Learning Support Unit" subtitle="Paket terapi 8 atau 16 pertemuan. Sesi dihabiskan tanpa pengembalian dana; TU mencatat kehadiran dari rekap terapis." :surface="false">
    <template #actions>
      <Button label="Paket baru" :disabled="loading || !!error" @click="bukaPaket"><template #icon><Icon name="plus" /></template></Button>
    </template>
    <section class="lsu-panel" aria-label="Daftar paket LSU" :aria-busy="loading">
      <div class="lsu-toolbar">
        <div class="lsu-field"><label for="lsu-search">Cari siswa</label><SearchField input-id="lsu-search" v-model="query" placeholder="Nama siswa" hint="Mencari pada paket yang dimuat" /></div>
        <Button label="Muat ulang" severity="secondary" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template></Button>
      </div>
      <div v-if="error" class="lsu-notice"><Message severity="error" :closable="false">{{ error }}</Message><Button label="Coba lagi" severity="secondary" @click="load" /></div>
      <p v-else class="lsu-results" role="status">{{ loading ? "Memuat paket…" : `${tampil.length} paket ditampilkan` }}</p>
      <div v-if="!loading && !error && !tampil.length" class="lsu-empty"><Icon name="student" /><h2>{{ query ? 'Tidak ada paket yang cocok' : 'Belum ada paket LSU' }}</h2><p>{{ query ? 'Ubah kata pencarian.' : 'Buat paket saat orang tua mendaftarkan anak ke LSU. Tagihannya otomatis dibuat.' }}</p></div>
      <ul v-else class="lsu-list">
        <li v-for="paket in tampil" :key="paket.id" class="lsu-item">
          <div class="lsu-item-head">
            <div><strong>{{ paket.siswa_nama }}</strong><small>Paket {{ paket.jumlah_sesi }} pertemuan · mulai {{ tanggal(paket.tanggal_mulai) }} · {{ formatRp(paket.harga) }}</small></div>
            <div class="lsu-tags"><Tag :value="paketState(paket).label" :severity="paketState(paket).severity" /><Tag :value="tagihanState(paket).label" :severity="tagihanState(paket).severity" /></div>
          </div>
          <div class="lsu-progress" role="img" :aria-label="`${paket.sesi_terpakai} dari ${paket.jumlah_sesi} sesi terpakai`"><span v-for="n in paket.jumlah_sesi" :key="n" :class="{ 'is-used': n <= paket.sesi_terpakai }" /></div>
          <p v-if="paket.keterangan" class="lsu-note">{{ paket.keterangan }}</p>
          <div class="lsu-actions">
            <Button v-if="sisaSesi(paket)" label="Catat pertemuan" severity="secondary" :aria-label="`Catat pertemuan ${paket.siswa_nama}`" @click="bukaSesi(paket)"><template #icon><Icon name="calendar-plus" /></template></Button>
            <Button :label="terbuka === paket.id ? 'Tutup riwayat' : `Riwayat (${paket.sesi_terpakai})`" severity="secondary" text :aria-expanded="terbuka === paket.id" :aria-controls="`lsu-riwayat-${paket.id}`" @click="terbuka = terbuka === paket.id ? null : paket.id" />
            <RouterLink v-if="paket.tagihan && paket.tagihan_status !== 'LUNAS'" class="lsu-link" to="/tagihan">Bayar di Tagihan</RouterLink>
            <Button v-if="!paket.sesi_terpakai" label="Hapus paket" severity="danger" text @click="hapusPaket(paket)" />
          </div>
          <ol v-if="terbuka === paket.id" :id="`lsu-riwayat-${paket.id}`" class="lsu-history">
            <li v-if="!paket.pertemuan.length" class="lsu-history-empty">Belum ada pertemuan dicatat.</li>
            <li v-for="(p, i) in paket.pertemuan" :key="p.id"><span class="lsu-history-no">{{ i + 1 }}</span><span>{{ tanggal(p.tanggal) }}<small v-if="p.catatan"> · {{ p.catatan }}</small></span><Button severity="secondary" text :aria-label="`Hapus pertemuan ${tanggal(p.tanggal)}`" @click="hapusPertemuan(paket, p)"><template #icon><Icon name="trash" /></template></Button></li>
          </ol>
        </li>
      </ul>
    </section>

    <Dialog v-model:visible="paketDialog" header="Paket LSU baru" modal :draggable="false" :closable="!saving" class="lsu-dialog" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup' }">
      <template #closeicon><Icon name="x" /></template>
      <form id="lsu-paket-form" class="lsu-form" novalidate @submit.prevent="simpanPaket">
        <div class="lsu-field lsu-full"><label for="lsu-siswa">Siswa (wajib)</label><Select input-id="lsu-siswa" v-model="paketForm.siswa" :options="siswaOptions" option-label="label" option-value="value" filter placeholder="Pilih siswa aktif" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select>
          <small v-if="masihBerjalan" class="lsu-warn">Siswa ini masih punya paket dengan sisa sesi. Habiskan dulu sebelum membuka paket baru.</small></div>
        <div class="lsu-field"><label for="lsu-sesi">Jumlah pertemuan</label><Select input-id="lsu-sesi" v-model="paketForm.jumlah_sesi" :options="[...JUMLAH_SESI_OPTIONS]" option-label="label" option-value="value" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div class="lsu-field"><label for="lsu-harga">Harga paket (Rp)</label><InputNumber input-id="lsu-harga" v-model="paketForm.harga" locale="id-ID" :min="0" :disabled="saving" fluid /></div>
        <div class="lsu-field"><label for="lsu-mulai">Tanggal mulai</label><DatePicker input-id="lsu-mulai" v-model="paketForm.tanggal_mulai" date-format="dd/mm/yy" :disabled="saving" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small>Tagihan dibuat di bulan ini.</small></div>
        <div class="lsu-field"><label for="lsu-ket">Keterangan</label><InputText id="lsu-ket" v-model="paketForm.keterangan" maxlength="255" placeholder="Opsional, mis. nama terapis" :disabled="saving" fluid /></div>
        <Message v-if="paketError" severity="error" :closable="false" class="lsu-full" role="alert">{{ paketError }}</Message>
      </form>
      <template #footer><Button label="Batal" severity="secondary" :disabled="saving" @click="paketDialog = false" /><Button label="Buat paket dan tagihan" type="submit" form="lsu-paket-form" :loading="saving" :disabled="masihBerjalan" /></template>
    </Dialog>

    <Dialog :visible="!!sesiTarget" header="Catat pertemuan" modal :draggable="false" :closable="!saving" class="lsu-dialog" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup' }" @update:visible="v => { if (!v && !saving) sesiTarget = null }">
      <template #closeicon><Icon name="x" /></template>
      <form v-if="sesiTarget" id="lsu-sesi-form" class="lsu-form" novalidate @submit.prevent="simpanSesi">
        <p class="lsu-full lsu-context"><strong>{{ sesiTarget.siswa_nama }}</strong> · pertemuan ke-{{ sesiTarget.sesi_terpakai + 1 }} dari {{ sesiTarget.jumlah_sesi }}</p>
        <div class="lsu-field"><label for="lsu-tgl">Tanggal pertemuan</label><DatePicker input-id="lsu-tgl" v-model="sesiForm.tanggal" date-format="dd/mm/yy" :disabled="saving" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker></div>
        <div class="lsu-field"><label for="lsu-catatan">Catatan</label><InputText id="lsu-catatan" v-model="sesiForm.catatan" maxlength="255" placeholder="Opsional" :disabled="saving" fluid /></div>
        <Message v-if="sesiError" severity="error" :closable="false" class="lsu-full" role="alert">{{ sesiError }}</Message>
      </form>
      <template #footer><Button label="Batal" severity="secondary" :disabled="saving" @click="sesiTarget = null" /><Button label="Simpan pertemuan" type="submit" form="lsu-sesi-form" :loading="saving" /></template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.lsu-panel { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: hidden; }
.lsu-toolbar { display: flex; flex-wrap: wrap; align-items: end; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.lsu-toolbar .lsu-field { flex: 1 1 260px; }
.lsu-field { display: grid; gap: var(--bee-space-2); min-width: 0; align-content: start; }
.lsu-field label { font-size: var(--bee-type-caption); font-weight: 600; }
.lsu-field small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.lsu-field small.lsu-warn { color: var(--bee-color-critical); }
.lsu-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.lsu-results { margin: 0; padding: var(--bee-space-3) var(--bee-space-5); border-top: 1px solid var(--app-border); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.lsu-empty { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-7) var(--bee-space-5); text-align: center; border-top: 1px solid var(--app-border); }
.lsu-empty .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); }
.lsu-empty h2 { margin: 0; font-size: var(--bee-type-section); }
.lsu-empty p { margin: 0; color: var(--app-text-muted); max-width: 48ch; }
.lsu-list { list-style: none; margin: 0; padding: 0; }
.lsu-item { display: grid; gap: var(--bee-space-3); padding: var(--bee-space-4) var(--bee-space-5); border-top: 1px solid var(--app-border); }
.lsu-item-head { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--bee-space-2) var(--bee-space-4); }
.lsu-item-head small { display: block; color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-top: var(--bee-space-1); }
.lsu-tags { display: flex; flex-wrap: wrap; gap: var(--bee-space-2); align-items: start; }
.lsu-progress { display: flex; gap: 4px; max-width: 420px; }
.lsu-progress span { flex: 1; height: 8px; border-radius: 4px; background: var(--bee-color-surface-subtle); border: 1px solid var(--app-border); }
.lsu-progress span.is-used { background: var(--bee-color-brand); border-color: var(--bee-color-brand); }
.lsu-note { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.lsu-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-2); }
.lsu-link { display: inline-flex; align-items: center; min-height: 44px; padding: 0 var(--bee-space-3); color: var(--bee-color-brand); font-size: var(--bee-type-ui); }
.lsu-history { list-style: none; margin: 0; padding: 0; border: 1px solid var(--app-border); border-radius: var(--bee-radius-control); }
.lsu-history li { display: flex; align-items: center; gap: var(--bee-space-3); padding: var(--bee-space-1) var(--bee-space-3); border-bottom: 1px solid var(--app-border); font-variant-numeric: tabular-nums; }
.lsu-history li:last-child { border-bottom: 0; }
.lsu-history li > span:nth-child(2) { flex: 1; }
.lsu-history small { color: var(--app-text-muted); }
.lsu-history-no { color: var(--app-text-muted); font-size: var(--bee-type-caption); min-width: 2ch; }
.lsu-history-empty { color: var(--app-text-muted); padding: var(--bee-space-3) !important; }
.lsu-dialog { width: min(560px, calc(100vw - 32px)); }
.lsu-form { display: grid; grid-template-columns: 1fr 1fr; gap: var(--bee-space-4); }
.lsu-full { grid-column: 1 / -1; }
.lsu-context { margin: 0; }
@media (max-width: 540px) { .lsu-form { grid-template-columns: minmax(0, 1fr); } .lsu-toolbar > .p-button { width: 100%; } }
</style>
