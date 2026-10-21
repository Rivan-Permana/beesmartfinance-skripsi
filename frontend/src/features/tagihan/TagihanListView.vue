<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue"

import { tagihanApi } from "./api"
import InvoicePreview from "./InvoicePreview.vue"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { coaApi } from "@/features/jurnal/api"
import { jenjangApi, kelompokApi } from "@/features/absensi/api"
import { tarifKateringApi } from "@/features/katering/api"
import { siswaApi } from "@/features/siswa/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import TagihanDirectory from "./TagihanDirectory.vue"
import TagihanPaymentDialog from "./TagihanPaymentDialog.vue"
import TagihanHistoryDialog from "./TagihanHistoryDialog.vue"
import { paymentPayload, paymentValid, type TagihanPaymentForm } from "./payment"
import { perluDicocokkan } from "./presentation"
import type {
  Coa,
  Jenjang,
  Kelompok,
  Siswa,
  StrukTagihan,
  Tagihan,
  TagihanDetail,
  TagihanKategori,
} from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const rows = ref<Tagihan[]>([])
const siswaList = ref<Siswa[]>([])
const loading = ref(false)
const loadError = ref("")
const defaultAkunPendapatan = ref("411")
const kasOptions = ref<Coa[]>([])

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const siswaNama = computed(() => {
  const map = new Map<number, string>()
  siswaList.value.forEach((s) => map.set(s.id, s.nama))
  return map
})

const KATEGORI_ORDER: TagihanKategori[] = ["TAHUNAN", "BULANAN", "LAIN"]
const KATEGORI_LABEL: Record<TagihanKategori, string> = {
  TAHUNAN: "Biaya tahunan",
  BULANAN: "Biaya bulanan",
  LAIN: "Lain-lain",
}

function prevMonth(): { bulan: number; tahun: number } {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return { bulan: d.getMonth() + 1, tahun: d.getFullYear() }
}

async function load() {
  loading.value = true
  loadError.value = ""
  try {
    rows.value = await tagihanApi.listAll()
  } catch (e) {
    rows.value = []
    loadError.value = "Tagihan belum berhasil dimuat. Periksa koneksi, lalu coba lagi."
  } finally {
    loading.value = false
  }
}

// --- generate / preview dialog ---
const genDialog = ref(false)
const previewLoading = ref(false)
const genForm = reactive({
  siswa: null as number | null,
  periode_bulan: prevMonth().bulan,
  periode_tahun: prevMonth().tahun,
  tarif_katering: 0,
})

async function loadTarifForPeriod(bulan: number, tahun: number) {
  let tarif = 0
  try { tarif = Number((await tarifKateringApi.get(bulan, tahun)).tarif_harian) } catch { /* Nol memakai tarif periode dari server. */ }
  if (genDialog.value && genForm.periode_bulan === bulan && genForm.periode_tahun === tahun) genForm.tarif_katering = tarif
  if (batchDialog.value && batchForm.periode_bulan === bulan && batchForm.periode_tahun === tahun) batchForm.tarif_katering = tarif
}

function openGenerate() {
  const p = prevMonth()
  genForm.siswa = null
  genForm.periode_bulan = p.bulan
  genForm.periode_tahun = p.tahun
  void loadTarifForPeriod(p.bulan, p.tahun)
  genDialog.value = true
}

watch(
  () => [genForm.periode_bulan, genForm.periode_tahun] as const,
  ([b, t]) => {
    if (genDialog.value) void loadTarifForPeriod(b, t)
  },
)

async function runPreview() {
  if (!genForm.siswa || previewLoading.value) return
  previewLoading.value = true
  try {
    const preview = await tagihanApi.preview({
      siswa: genForm.siswa,
      periode_bulan: genForm.periode_bulan,
      periode_tahun: genForm.periode_tahun,
      tarif_katering: genForm.tarif_katering || 0,
    })
    openEditor({
      id: null,
      siswa: preview.siswa,
      periode_bulan: preview.periode_bulan,
      periode_tahun: preview.periode_tahun,
      detail: preview.detail.map((d) => ({ ...d, nominal: String(d.nominal) })),
    })
    genDialog.value = false
  } catch (e) {
    notifyError(toast, e, "Gagal membuat preview tagihan.")
  } finally {
    previewLoading.value = false
  }
}

async function runGenerate() {
  if (!genForm.siswa || previewLoading.value) return
  previewLoading.value = true
  try {
    await tagihanApi.generate({
      siswa: genForm.siswa,
      periode_bulan: genForm.periode_bulan,
      periode_tahun: genForm.periode_tahun,
      tarif_katering: genForm.tarif_katering || 0,
    })
    notifySuccess(toast, "Tagihan berhasil dibuat.")
    genDialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal generate tagihan.")
  } finally {
    previewLoading.value = false
  }
}

// --- batch generate (E10.5) ---
const batchDialog = ref(false)
const batchLoading = ref(false)
const batchResult = ref<{
  count: number
  skipped: { nama: string; reason: string }[]
  sampleLines?: { kategori: string; komponen: string; keterangan: string }[]
  sampleTotal?: string
} | null>(null)
const jenjangList = ref<Jenjang[]>([])
const kelompokList = ref<Kelompok[]>([])
const batchForm = reactive({
  jenjang: null as number | null,
  kelompok: null as number | null,
  periode_bulan: prevMonth().bulan,
  periode_tahun: prevMonth().tahun,
  tarif_katering: 0,
})

async function openBatch() {
  batchResult.value = null
  const p = prevMonth()
  batchForm.jenjang = null
  batchForm.kelompok = null
  batchForm.periode_bulan = p.bulan
  batchForm.periode_tahun = p.tahun
  batchForm.tarif_katering = 0
  try {
    jenjangList.value = await jenjangApi.list()
  } catch {
    jenjangList.value = []
  }
  batchDialog.value = true
}

watch(
  () => batchForm.jenjang,
  async (id) => {
    batchForm.kelompok = null
    if (!id) {
      kelompokList.value = []
      return
    }
    try {
      kelompokList.value = await kelompokApi.list({ jenjang: id })
    } catch {
      kelompokList.value = []
    }
  },
)

watch(
  () => [batchForm.periode_bulan, batchForm.periode_tahun] as const,
  ([b, t]) => {
    if (batchDialog.value) void loadTarifForPeriod(b, t)
  },
)

watch(() => [batchForm.jenjang, batchForm.kelompok, batchForm.periode_bulan, batchForm.periode_tahun, batchForm.tarif_katering], () => { batchResult.value = null })

async function runBatchPreview() {
  if (batchLoading.value) return
  batchLoading.value = true
  batchResult.value = null
  try {
    const data = await tagihanApi.previewBatch({
      periode_bulan: batchForm.periode_bulan,
      periode_tahun: batchForm.periode_tahun,
      tarif_katering: batchForm.tarif_katering || 0,
      jenjang: batchForm.jenjang,
      kelompok: batchForm.kelompok,
    })
    batchResult.value = {
      count: data.count,
      skipped: data.skipped,
      sampleLines: data.previews[0]?.detail.map((d) => ({
        kategori: d.kategori,
        komponen: d.komponen,
        keterangan: d.keterangan,
      })),
      sampleTotal: data.previews[0]?.total,
    }
  } catch (e) {
    notifyError(toast, e, "Gagal preview batch tagihan.")
  } finally {
    batchLoading.value = false
  }
}

async function runBatchGenerate() {
  if (batchLoading.value || !batchResult.value?.count) return
  batchLoading.value = true
  try {
    const data = await tagihanApi.generateBatch({
      periode_bulan: batchForm.periode_bulan,
      periode_tahun: batchForm.periode_tahun,
      tarif_katering: batchForm.tarif_katering || 0,
      jenjang: batchForm.jenjang,
      kelompok: batchForm.kelompok,
    })
    notifySuccess(
      toast,
      `${data.count} tagihan dibuat${data.skipped.length ? `, ${data.skipped.length} dilewati` : ""}.`,
    )
    batchDialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal generate batch tagihan.")
  } finally {
    batchLoading.value = false
  }
}

// --- editor dialog ---
const editorDialog = ref(false)
const saving = ref(false)
const editor = reactive<{
  id: number | null
  siswa: number | null
  periode_bulan: number
  periode_tahun: number
  lines: TagihanDetail[]
}>({
  id: null,
  siswa: null,
  periode_bulan: 1,
  periode_tahun: 2026,
  lines: [],
})

const editorTotal = computed(() =>
  editor.lines.reduce((sum, l) => sum + Number(l.nominal || 0), 0),
)

const linesByKategori = computed(() =>
  KATEGORI_ORDER.map((kat) => ({
    kategori: kat,
    label: KATEGORI_LABEL[kat],
    lines: editor.lines
      .map((line, index) => ({ line, index }))
      .filter(({ line }) => line.kategori === kat),
  })).filter((g) => g.lines.length > 0 || g.kategori !== "BULANAN"),
)

function openEditor(payload: {
  id: number | null
  siswa: number
  periode_bulan: number
  periode_tahun: number
  detail: TagihanDetail[]
}) {
  editor.id = payload.id
  editor.siswa = payload.siswa
  editor.periode_bulan = payload.periode_bulan
  editor.periode_tahun = payload.periode_tahun
  editor.lines = payload.detail.map((d) => ({ ...d }))
  editorDialog.value = true
}

async function editTagihan(t: Tagihan) {
  try {
    const full = await tagihanApi.get(t.id)
    openEditor({
      id: full.id,
      siswa: full.siswa,
      periode_bulan: full.periode_bulan,
      periode_tahun: full.periode_tahun,
      detail: full.detail,
    })
  } catch (e) {
    notifyError(toast, e, "Gagal memuat tagihan.")
  }
}

function addLine(kategori: TagihanKategori) {
  editor.lines.push({
    komponen: "LAIN",
    kategori,
    keterangan: kategori === "TAHUNAN" ? "Biaya tahunan" : "",
    akun_pendapatan: defaultAkunPendapatan.value,
    nominal: "0",
  })
}

function removeLine(index: number) {
  editor.lines.splice(index, 1)
}

function cancelEditor() {
  if (!editor.id && editor.lines.length > 0) {
    confirm.require({
      message: "Batalkan pembuatan tagihan? Perubahan preview tidak disimpan.",
      header: "Batalkan Tagihan",
      icon: "pi pi-times-circle",
      rejectLabel: "Lanjut Edit",
      acceptLabel: "Batalkan",
      acceptClass: "p-button-danger",
      accept: () => {
        editorDialog.value = false
      },
    })
    return
  }
  editorDialog.value = false
}

function batalkanTagihan(t: Tagihan) {
  confirm.require({
    message: `Hapus tagihan ${siswaNama.value.get(t.siswa) ?? ""} periode ${BULAN[t.periode_bulan - 1]} ${t.periode_tahun}? Tagihan yang sudah dibayar sebagian tidak bisa dihapus.`,
    header: "Batalkan Tagihan",
    icon: "pi pi-trash",
    rejectLabel: "Batal",
    acceptLabel: "Hapus Tagihan",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await tagihanApi.remove(t.id)
        notifySuccess(toast, "Tagihan dibatalkan")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal membatalkan tagihan.")
      }
    },
  })
}

async function saveEditor() {
  if (!editor.siswa || editor.lines.length === 0 || saving.value) return
  saving.value = true
  try {
    const payload = {
      siswa: editor.siswa,
      periode_bulan: editor.periode_bulan,
      periode_tahun: editor.periode_tahun,
      detail: editor.lines.map((l) => ({
        komponen: l.komponen,
        kategori: l.kategori,
        keterangan: l.keterangan,
        akun_pendapatan: l.akun_pendapatan,
        nominal: l.nominal,
      })),
    }
    if (editor.id) {
      await tagihanApi.update(editor.id, payload)
      notifySuccess(toast, "Tagihan diperbarui")
    } else {
      await tagihanApi.create(payload)
      notifySuccess(toast, "Tagihan disimpan")
    }
    editorDialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan tagihan.")
  } finally {
    saving.value = false
  }
}

const bayarDialog = ref(false)
const bayarTarget = ref<Tagihan | null>(null)
const bayarSaving = ref(false)
const bayarError = ref("")
const bayarForm = ref<TagihanPaymentForm>({
  tanggal: new Date(), no_bukti: "", akun_kas: "", request_id: "",
  alokasi: [],
})
const bayarValid = computed(() => paymentValid(bayarForm.value))

async function bayar(t: Tagihan) {
  try {
    const full = await tagihanApi.get(t.id)
    if (perluDicocokkan(full)) {
      notifyError(toast, new Error("Pembayaran lama perlu direkonsiliasi sebelum menerima pembayaran baru."))
      return
    }
    if (full.detail.some((d) => Number(d.nominal) < 0)) {
      notifyError(toast, new Error("Sesuaikan potongan menjadi rincian netto sebelum pembayaran."))
      return
    }
    bayarTarget.value = full
    bayarError.value = ""
    bayarForm.value.tanggal = new Date()
    bayarForm.value.no_bukti = ""
    bayarForm.value.akun_kas = kasOptions.value[0]?.kode_akun ?? ""
    bayarForm.value.request_id = crypto.randomUUID()
    bayarForm.value.alokasi = full.detail.filter((d) => d.id && Number(d.nominal) > Number(d.total_terbayar ?? 0)).map((d) => ({
      detail: d.id!, label: d.keterangan || d.komponen, nominal: 0,
      sisa: Number(d.nominal) - Number(d.total_terbayar ?? 0),
    }))
    bayarDialog.value = true
  } catch (e) {
    notifyError(toast, e, "Gagal memuat rincian pembayaran.")
  }
}

async function simpanPembayaran() {
  if (!bayarTarget.value || !bayarValid.value || bayarSaving.value) return
  bayarSaving.value = true
  bayarError.value = ""
  try {
    const res = await tagihanApi.bayar(bayarTarget.value.id, paymentPayload(bayarForm.value))
    notifySuccess(toast, "Pembayaran tersimpan", res)
    bayarDialog.value = false
    bayarTarget.value = res.tagihan
    await load()
  } catch (e) {
    const error = friendlyError(e, "Pembayaran belum berhasil disimpan.")
    bayarError.value = [error.summary, error.detail].filter(Boolean).join(". ")
  } finally {
    bayarSaving.value = false
  }
}

const riwayatTarget = ref<Tagihan | null>(null)
async function lihatRiwayat(t: Tagihan) {
  try { riwayatTarget.value = await tagihanApi.get(t.id) }
  catch (e) { notifyError(toast, e, "Gagal memuat riwayat pembayaran.") }
}

// --- struk / cetak ---
const strukDialog = ref(false)
const struk = ref<StrukTagihan | null>(null)

async function lihatStruk(t: Tagihan) {
  try {
    struk.value = await tagihanApi.struk(t.id)
    strukDialog.value = true
  } catch (e) {
    notifyError(toast, e, "Gagal memuat struk.")
  }
}

function selesaiCetak() {
  document.body.classList.remove("bee-print-struk")
  window.removeEventListener("afterprint", selesaiCetak)
}

function cetak() {
  document.body.classList.add("bee-print-struk")
  window.addEventListener("afterprint", selesaiCetak, { once: true })
  try {
    window.print()
  } catch (e) {
    selesaiCetak()
    notifyError(toast, e, "Gagal membuka dialog cetak.")
  }
}

onBeforeUnmount(selesaiCetak)

async function loadAccounts() {
  try {
    const coa = await coaApi.list()
    kasOptions.value = coa.filter((c) => c.is_active && ["111", "112", "1011", "1101", "1102"].includes(c.kode_akun))
    const pend = coa.find((c) => c.kode_akun.startsWith("41"))
    if (pend) defaultAkunPendapatan.value = pend.kode_akun
  } catch (e) {
    notifyError(toast, e, "Akun pembayaran belum berhasil dimuat.")
  }
}
onMounted(async () => {
  await Promise.all([
    load(), loadAccounts(),
    siswaApi.listAll().then(data => { siswaList.value = data }).catch(e => notifyError(toast, e, "Nama siswa belum berhasil dimuat.")),
  ])
})
</script>

<template>
  <PageLayout title="Tagihan siswa" subtitle="Periksa tagihan, catat pembayaran, dan siapkan faktur." :surface="false">
    <template #actions>
      <Button label="Buat sekaligus" severity="secondary" @click="openBatch"><template #icon><Icon name="users" /></template></Button>
      <Button label="Buat tagihan" @click="openGenerate"><template #icon><Icon name="plus" /></template></Button>
    </template>
    <TagihanDirectory :rows="rows" :names="siswaNama" :loading="loading" :error="loadError" @create="openGenerate" @retry="load" @pay="bayar" @edit="editTagihan" @remove="batalkanTagihan" @history="lihatRiwayat" @invoice="lihatStruk" />
    <TagihanPaymentDialog v-model="bayarDialog" v-model:form="bayarForm" :target="bayarTarget" :student-name="bayarTarget ? siswaNama.get(bayarTarget.siswa) ?? bayarTarget.siswa_nama ?? 'Siswa' : ''" :accounts="kasOptions" :saving="bayarSaving" :error="bayarError" @save="simpanPembayaran" @reload-accounts="loadAccounts" />

    <TagihanHistoryDialog v-model:target="riwayatTarget" :student-name="riwayatTarget ? siswaNama.get(riwayatTarget.siswa) : undefined" />

    <!-- Generate -->
    <Dialog :close-button-props="{severity: 'secondary', text: true}" v-model:visible="genDialog" header="Buat tagihan" modal :closable="!previewLoading" :close-on-escape="!previewLoading" :style="{ width: '32rem' }">
      <template #closeicon><Icon name="x" /></template>
      <div class="form">
        <div class="field">
          <label for="generate-siswa">Siswa (wajib)</label>
          <Select :key="(previewLoading) ? 'locked' : 'editable'" input-id="generate-siswa"
            v-model="genForm.siswa" :disabled="previewLoading"
            :options="siswaList"
            option-label="nama"
            option-value="id"
            filter
            placeholder="Pilih siswa"
            fluid
          ><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select>
        </div>
        <div class="row">
          <div class="field">
            <label for="generate-bulan">Bulan (default: bulan lalu)</label>
            <Select :key="(previewLoading) ? 'locked' : 'editable'" input-id="generate-bulan"
              v-model="genForm.periode_bulan" :disabled="previewLoading"
              :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
              option-label="label"
              option-value="value"
              fluid
            ><template #dropdownicon><Icon name="caret-down" /></template></Select>
          </div>
          <div class="field">
            <label for="generate-tahun">Tahun</label>
            <InputNumber input-id="generate-tahun" v-model="genForm.periode_tahun" :disabled="previewLoading" :min="2020" :max="2100" :use-grouping="false" fluid />
          </div>
        </div>
        <div class="field">
          <label for="generate-tarif">Tarif katering per hari (Rp)</label>
          <InputNumber input-id="generate-tarif" locale="id-ID" :max-fraction-digits="2" v-model="genForm.tarif_katering" :disabled="previewLoading" :min="0" fluid />
          <small>0 = otomatis dari tarif periode katering. Jemputan dihitung otomatis dari absensi × tarif pendaftaran.</small>
        </div>
        <Message severity="info" :closable="false">
          Komponen <strong>tahunan TP</strong> (uang masuk, kegiatan, dll.) otomatis muncul di <strong>Juli</strong> sesuai jenjang &amp; status siswa.
        </Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text :disabled="previewLoading" @click="genDialog = false" />
        <Button
          label="Buat langsung"

          severity="secondary"
          :disabled="!genForm.siswa"
          :loading="previewLoading"
          @click="runGenerate"
        ><template #icon><Icon name="lightning" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
        <Button
          label="Periksa rincian"

          :disabled="!genForm.siswa"
          :loading="previewLoading"
          @click="runPreview"
        ><template #icon><Icon name="eye" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
      </template>
    </Dialog>

    <!-- Batch Generate -->
    <Dialog :close-button-props="{severity: 'secondary', text: true}" v-model:visible="batchDialog" header="Buat tagihan sekaligus" modal :closable="!batchLoading" :close-on-escape="!batchLoading" :style="{ width: '36rem' }">
      <template #closeicon><Icon name="x" /></template>
      <div class="form">
        <div class="row">
          <div class="field">
            <label for="batch-jenjang">Jenjang</label>
            <Select :key="(batchLoading) ? 'locked' : 'editable'" input-id="batch-jenjang"
              v-model="batchForm.jenjang" :disabled="batchLoading"
              :options="[{ id: null, kode: 'Semua' }, ...jenjangList]"
              option-label="kode"
              option-value="id"
              placeholder="Semua jenjang"
              show-clear
              fluid
            ><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select>
          </div>
          <div class="field">
            <label for="batch-kelompok">Kelompok</label>
            <Select :key="(batchLoading || !batchForm.jenjang) ? 'locked' : 'editable'" input-id="batch-kelompok"
              v-model="batchForm.kelompok"
              :options="kelompokList"
              option-label="nama"
              option-value="id"
              placeholder="Semua kelompok"
              show-clear
              :disabled="batchLoading || !batchForm.jenjang"
              fluid
            ><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select>
          </div>
        </div>
        <div class="row">
          <div class="field">
            <label for="batch-bulan">Bulan</label>
            <Select :key="(batchLoading) ? 'locked' : 'editable'" input-id="batch-bulan"
              v-model="batchForm.periode_bulan" :disabled="batchLoading"
              :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
              option-label="label"
              option-value="value"
              fluid
            ><template #dropdownicon><Icon name="caret-down" /></template></Select>
          </div>
          <div class="field">
            <label for="batch-tahun">Tahun</label>
            <InputNumber input-id="batch-tahun" v-model="batchForm.periode_tahun" :disabled="batchLoading" :min="2020" :max="2100" :use-grouping="false" fluid />
          </div>
        </div>
        <Message v-if="batchResult" severity="info" :closable="false" class="batch-preview-msg">
          <p>
            Hasil pemeriksaan: <strong>{{ batchResult.count }}</strong> siswa siap dibuatkan tagihan.
            <span v-if="batchResult.skipped.length">
              {{ batchResult.skipped.length }} dilewati (sudah ada / tanpa komponen).
            </span>
          </p>
          <p v-if="batchForm.periode_bulan !== 7" class="batch-hint">
            Bulan <strong>{{ BULAN[batchForm.periode_bulan - 1] }}</strong>: tagihan = SPP + katering + jemput saja.
            Komponen <strong>tahunan</strong> (uang masuk, kegiatan, dll.) hanya di <strong>Juli</strong>.
          </p>
          <template v-if="batchResult.sampleLines?.length">
            <p class="batch-hint">
              Contoh 1 siswa — total {{ formatRp(Number(batchResult.sampleTotal ?? 0)) }}:
            </p>
            <ul class="batch-sample-list">
              <li v-for="(line, i) in batchResult.sampleLines" :key="i">
                <span class="batch-kat">{{ line.kategori === 'TAHUNAN' ? 'Tahunan' : 'Bulanan' }}</span>
                — {{ line.keterangan || line.komponen }}
              </li>
            </ul>
          </template>
        </Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text :disabled="batchLoading" @click="batchDialog = false" />
        <Button label="Periksa daftar" severity="secondary" :loading="batchLoading" @click="runBatchPreview" ><template #icon><Icon name="eye" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
        <Button
          label="Buat tagihan terpilih"

          :loading="batchLoading"
          :disabled="!batchResult || batchResult.count === 0"
          @click="runBatchGenerate"
        ><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
      </template>
    </Dialog>

    <!-- Editor -->
    <Dialog
      v-model:visible="editorDialog"
      :header="editor.id ? 'Ubah tagihan' : 'Periksa rincian tagihan'"
      modal
      :style="{ width: '52rem', maxWidth: '96vw' }"
      :closable="false"
      :close-on-escape="false"
      class="tagihan-editor-dialog"
    >
      <template #closeicon><Icon name="x" /></template>
      <div class="editor-wrap">
      <div class="editor-head">
        <div>
          <strong class="bee-card-name">{{ siswaNama.get(editor.siswa ?? 0) ?? "—" }}</strong>
          <div class="muted">{{ BULAN[editor.periode_bulan - 1] }} {{ editor.periode_tahun }}</div>
        </div>
        <div class="editor-total">
          <span class="muted">Total tagihan</span>
          <strong>{{ formatRp(editorTotal) }}</strong>
        </div>
      </div>

      <div v-for="group in linesByKategori" :key="group.kategori" class="editor-section">
        <div class="editor-section-head">
          <h4 class="bee-field-label">{{ group.label }}</h4>
          <Button
            v-if="group.kategori !== 'BULANAN'"
            label="Tambah"

            size="small"
            text
            :disabled="saving" @click="addLine(group.kategori)"
          ><template #icon><Icon name="plus" /></template></Button>
        </div>
        <div v-if="group.lines.length > 0" class="editor-table-wrap">
          <table class="editor-table">
            <thead>
              <tr>
                <th>Keterangan</th>
                <th>Nominal</th>
                <th aria-hidden="true" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="{ line, index } in group.lines" :key="index">
                <td>
                  <InputText v-model="line.keterangan" :aria-label="`Keterangan komponen ${index + 1}`" placeholder="Keterangan" :disabled="saving" fluid />
                </td>
                <td>
                  <InputNumber
                    :model-value="Number(line.nominal)"
                    :aria-label="`Nominal komponen ${index + 1}`"
                    :disabled="saving"
                    mode="currency"
                    currency="IDR"
                    :max-fraction-digits="2"
                    locale="id-ID"
                    :min="0"
                    fluid
                    @update:model-value="(v) => (line.nominal = String(v ?? 0))"
                  />
                </td>
                <td class="line-action">
                  <Button
                    v-if="group.kategori !== 'BULANAN'"

                    severity="danger"
                    text
                    size="small"
                    aria-label="Hapus baris"
                    :disabled="saving" @click="removeLine(index)"
                  ><template #icon><Icon name="trash" /></template></Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="group.lines.length === 0 && group.kategori === 'TAHUNAN'" class="empty-section">
          Belum ada biaya tahunan — klik <strong>Tambah</strong> di atas.
        </p>
        <p v-if="group.lines.length === 0 && group.kategori === 'LAIN'" class="empty-section">
          Belum ada biaya lain-lain — klik <strong>Tambah</strong> di atas.
        </p>
      </div>
      </div>

      <template #footer>
        <Button
          :label="editor.id ? 'Batal' : 'Batalkan'"
          severity="secondary"
          text
          :disabled="saving"
          @click="cancelEditor"
        />
        <Button
          label="Simpan tagihan"

          :disabled="editor.lines.length === 0"
          :loading="saving"
          @click="saveEditor"
        ><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button>
      </template>
    </Dialog>

    <!-- Struk / Cetak -->
    <Dialog
      v-model:visible="strukDialog"
      header="Faktur tagihan"
      modal
      :style="{ width: '32rem' }"
      class="struk-dialog"
      :pt="{ mask: { class: 'struk-print-mask' } }"
      :dismissable-mask="true"
    >
      <template #closeicon><Icon name="x" /></template>
      <InvoicePreview v-if="struk" id="struk-print-area" :invoice="struk" printable />
      <template #footer>
        <Button label="Tutup" severity="secondary" text @click="strukDialog = false" />
        <Button label="Cetak" :disabled="!struk" @click="cetak" ><template #icon><Icon name="printer" /></template></Button>
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.row {
  display: flex;
  gap: 0.75rem;
}
.field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1;
}
.field label {
  font-weight: 600;
  font-size: 0.85rem;
}
.field small,
.muted {
  color: var(--app-text-muted);
  font-size: 0.8rem;
}
.editor-wrap {
  padding: 0 0.15rem;
}
.editor-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--app-border);
}
.editor-total {
  text-align: right;
  flex-shrink: 0;
}
.editor-total strong {
  display: block;
  font-size: 1.15rem;
  font-variant-numeric: tabular-nums;
  color: var(--bee-secondary);
  font-family: var(--bee-font-body);
}
.editor-section {
  margin-bottom: 1.15rem;
}
.editor-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.editor-section-head h4 {
  margin: 0;
}
.editor-table-wrap {
  overflow-x: auto;
}
.editor-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 0.45rem;
  table-layout: fixed;
}
.editor-table th {
  padding: 0 0.35rem 0.25rem;
  text-align: left;
  font-family: var(--bee-font-body);
  font-size: var(--bee-type-caption);
  font-weight: 500;
  color: var(--app-text-muted);
}
.editor-table th:last-child {
  width: 2.75rem;
}
.editor-table td {
  padding: 0 0.35rem;
  vertical-align: middle;
}
.editor-table td:first-child,
.editor-table th:first-child {
  width: 50%;
}
.editor-table td:nth-child(2),
.editor-table th:nth-child(2) {
  width: calc(50% - 2.75rem);
}
.line-action {
  text-align: center;
}
.empty-section {
  margin: 0 0 0.5rem;
  padding: 0 0.15rem;
  font-size: 0.85rem;
  color: var(--app-text-muted);
}
.batch-preview-msg p {
  margin: 0 0 0.35rem;
}
.batch-hint {
  font-size: 0.88rem;
  color: var(--app-text-muted);
}
.batch-sample-list {
  margin: 0.35rem 0 0;
  padding-left: 1.1rem;
  font-size: 0.85rem;
}
.batch-kat {
  font-weight: 700;
  color: var(--app-text-muted);
}
@media(max-width:520px) { .row { flex-direction: column; }.editor-head { flex-wrap: wrap; }.editor-table { min-width: 440px; } }
</style>

<style>
.tagihan-editor-dialog .p-dialog-content {
  overflow-x: hidden;
}
</style>
