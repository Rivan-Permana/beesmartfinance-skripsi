<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"

import { tagihanApi } from "./api"
import InvoicePreview from "./InvoicePreview.vue"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { coaApi } from "@/features/jurnal/api"
import { jenjangApi, kelompokApi } from "@/features/absensi/api"
import { tarifKateringApi } from "@/features/katering/api"
import { siswaApi } from "@/features/siswa/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type {
  Jenjang,
  Kelompok,
  Siswa,
  StrukTagihan,
  Tagihan,
  TagihanDetail,
  TagihanKategori,
  TagihanStatus,
} from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const rows = ref<Tagihan[]>([])
const siswaList = ref<Siswa[]>([])
const loading = ref(false)
const defaultAkunPendapatan = ref("411")

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const siswaNama = computed(() => {
  const map = new Map<number, string>()
  siswaList.value.forEach((s) => map.set(s.id, s.nama))
  return map
})

const { query: searchQuery, filtered: filteredRows } = useTableSearch(rows, (t) => [
  siswaNama.value.get(t.siswa) ?? String(t.siswa),
  BULAN[t.periode_bulan - 1],
  String(t.periode_tahun),
  t.status,
  formatRp(t.total),
])

const statusSeverity: Record<TagihanStatus, string> = {
  BELUM: "warn",
  SEBAGIAN: "info",
  LUNAS: "success",
}

const KATEGORI_ORDER: TagihanKategori[] = ["TAHUNAN", "BULANAN", "LAIN"]
const KATEGORI_LABEL: Record<TagihanKategori, string> = {
  TAHUNAN: "Biaya Tahunan",
  BULANAN: "Biaya Bulanan",
  LAIN: "Lain-lain",
}

function prevMonth(): { bulan: number; tahun: number } {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return { bulan: d.getMonth() + 1, tahun: d.getFullYear() }
}

async function load() {
  loading.value = true
  try {
    const data = await tagihanApi.list()
    rows.value = data.results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat tagihan.")
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
  try {
    const t = await tarifKateringApi.get(bulan, tahun)
    const tarif = Number(t.tarif_harian)
    genForm.tarif_katering = tarif
    if (batchDialog.value) batchForm.tarif_katering = tarif
  } catch {
    genForm.tarif_katering = 0
  }
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
  if (!genForm.siswa) return
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
  if (!genForm.siswa) return
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

async function runBatchPreview() {
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
  if (!editor.siswa || editor.lines.length === 0) return
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

function bayar(t: Tagihan) {
  confirm.require({
    message: `Catat pembayaran tagihan ${siswaNama.value.get(t.siswa) ?? ""} bulan ${BULAN[t.periode_bulan - 1]}? Sistem akan membuat jurnal pendapatan otomatis.`,
    header: "Konfirmasi Pembayaran",
    icon: "pi pi-wallet",
    rejectLabel: "Batal",
    acceptLabel: "Bayar",
    accept: async () => {
      try {
        const res = await tagihanApi.bayar(t.id)
        notifySuccess(toast, "Pembayaran tercatat", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal mencatat pembayaran.")
      }
    },
  })
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

function cetak() {
  document.body.classList.add("bee-print-struk")
  window.print()
  window.onafterprint = () => {
    document.body.classList.remove("bee-print-struk")
    window.onafterprint = null
  }
}

onMounted(async () => {
  await load()
  try {
    siswaList.value = await siswaApi.listAll()
  } catch {
    /* select siswa kosong jika gagal */
  }
  try {
    const coa = await coaApi.list()
    const pend = coa.find((c) => c.kode_akun.startsWith("41"))
    if (pend) defaultAkunPendapatan.value = pend.kode_akun
  } catch {
    /* fallback 411 */
  }
})
</script>

<template>
  <PageLayout title="Tagihan Siswa" subtitle="Generate, edit, bayar, dan cetak faktur untuk ortu">
    <template #actions>
      <Button label="Batch Generate" icon="pi pi-users" severity="secondary" @click="openBatch" />
      <Button label="Buat Tagihan" icon="pi pi-plus" @click="openGenerate" />
    </template>
    <template #filters>
      <SearchField
        v-model="searchQuery"
        hint="Cari siswa, periode, status, total tagihan"
      />
    </template>

    <DataTable :value="filteredRows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada tagihan.</template>
      <Column header="Siswa">
        <template #body="{ data }">{{ siswaNama.get(data.siswa) ?? `#${data.siswa}` }}</template>
      </Column>
      <Column header="Periode">
        <template #body="{ data }">{{ BULAN[data.periode_bulan - 1] }} {{ data.periode_tahun }}</template>
      </Column>
      <Column header="Total">
        <template #body="{ data }">{{ formatRp(data.total) }}</template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity[data.status as TagihanStatus]" />
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--xl" bodyClass="bee-col-actions--xl">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button
              v-if="data.status === 'BELUM'"
              label="Edit"
              size="small"
              text
              @click="editTagihan(data)"
            />
            <Button
              v-if="data.status !== 'LUNAS'"
              label="Bayar"
              size="small"
              text
              @click="bayar(data)"
            />
            <Button
              v-if="data.status === 'BELUM'"
              label="Batalkan"
              size="small"
              text
              severity="danger"
              @click="batalkanTagihan(data)"
            />
            <Button label="Cetak" size="small" text severity="secondary" @click="lihatStruk(data)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Generate -->
    <Dialog v-model:visible="genDialog" header="Buat Tagihan" modal :style="{ width: '32rem' }">
      <div class="form">
        <div class="field">
          <label>Siswa *</label>
          <Select
            v-model="genForm.siswa"
            :options="siswaList"
            option-label="nama"
            option-value="id"
            filter
            placeholder="Pilih siswa"
            fluid
          />
        </div>
        <div class="row">
          <div class="field">
            <label>Bulan (default: bulan lalu)</label>
            <Select
              v-model="genForm.periode_bulan"
              :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
              option-label="label"
              option-value="value"
              fluid
            />
          </div>
          <div class="field">
            <label>Tahun</label>
            <InputNumber v-model="genForm.periode_tahun" :min="2020" :max="2100" :use-grouping="false" fluid />
          </div>
        </div>
        <div class="field">
          <label>Tarif Katering / hari</label>
          <InputNumber v-model="genForm.tarif_katering" :min="0" fluid />
          <small>0 = otomatis dari tarif periode katering. Jemputan dihitung otomatis dari absensi × tarif pendaftaran.</small>
        </div>
        <Message severity="info" :closable="false">
          Komponen <strong>tahunan TP</strong> (uang masuk, kegiatan, dll.) otomatis muncul di <strong>Juli</strong> sesuai jenjang &amp; status siswa.
        </Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="genDialog = false" />
        <Button
          label="Generate Langsung"
          icon="pi pi-bolt"
          severity="secondary"
          :disabled="!genForm.siswa"
          :loading="previewLoading"
          @click="runGenerate"
        />
        <Button
          label="Preview & Edit"
          icon="pi pi-eye"
          :disabled="!genForm.siswa"
          :loading="previewLoading"
          @click="runPreview"
        />
      </template>
    </Dialog>

    <!-- Batch Generate -->
    <Dialog v-model:visible="batchDialog" header="Batch Generate Tagihan" modal :style="{ width: '36rem' }">
      <div class="form">
        <div class="row">
          <div class="field">
            <label>Jenjang</label>
            <Select
              v-model="batchForm.jenjang"
              :options="[{ id: null, kode: 'Semua' }, ...jenjangList]"
              option-label="kode"
              option-value="id"
              placeholder="Semua jenjang"
              show-clear
              fluid
            />
          </div>
          <div class="field">
            <label>Kelompok</label>
            <Select
              v-model="batchForm.kelompok"
              :options="kelompokList"
              option-label="nama"
              option-value="id"
              placeholder="Semua kelompok"
              show-clear
              :disabled="!batchForm.jenjang"
              fluid
            />
          </div>
        </div>
        <div class="row">
          <div class="field">
            <label>Bulan</label>
            <Select
              v-model="batchForm.periode_bulan"
              :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
              option-label="label"
              option-value="value"
              fluid
            />
          </div>
          <div class="field">
            <label>Tahun</label>
            <InputNumber v-model="batchForm.periode_tahun" :min="2020" :max="2100" :use-grouping="false" fluid />
          </div>
        </div>
        <Message v-if="batchResult" severity="info" :closable="false" class="batch-preview-msg">
          <p>
            Preview: <strong>{{ batchResult.count }}</strong> siswa siap di-tagih.
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
        <Button label="Batal" severity="secondary" text @click="batchDialog = false" />
        <Button label="Preview" icon="pi pi-eye" severity="secondary" :loading="batchLoading" @click="runBatchPreview" />
        <Button
          label="Generate Semua"
          icon="pi pi-check"
          :loading="batchLoading"
          :disabled="!batchResult || batchResult.count === 0"
          @click="runBatchGenerate"
        />
      </template>
    </Dialog>

    <!-- Editor -->
    <Dialog
      v-model:visible="editorDialog"
      :header="editor.id ? 'Edit Tagihan' : 'Preview Tagihan'"
      modal
      :style="{ width: '52rem', maxWidth: '96vw' }"
      :closable="false"
      class="tagihan-editor-dialog"
    >
      <div class="editor-wrap">
      <div class="editor-head">
        <div>
          <strong class="bee-card-name">{{ siswaNama.get(editor.siswa ?? 0) ?? "—" }}</strong>
          <div class="muted">{{ BULAN[editor.periode_bulan - 1] }} {{ editor.periode_tahun }}</div>
        </div>
        <div class="editor-total">
          <span class="muted">Grand Total</span>
          <strong>{{ formatRp(editorTotal) }}</strong>
        </div>
      </div>

      <div v-for="group in linesByKategori" :key="group.kategori" class="editor-section">
        <div class="editor-section-head">
          <h4 class="bee-field-label">{{ group.label }}</h4>
          <Button
            v-if="group.kategori !== 'BULANAN'"
            label="Tambah"
            icon="pi pi-plus"
            size="small"
            text
            @click="addLine(group.kategori)"
          />
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
                  <InputText v-model="line.keterangan" placeholder="Keterangan" fluid />
                </td>
                <td>
                  <InputNumber
                    :model-value="Number(line.nominal)"
                    mode="currency"
                    currency="IDR"
                    locale="id-ID"
                    :min="0"
                    fluid
                    @update:model-value="(v) => (line.nominal = String(v ?? 0))"
                  />
                </td>
                <td class="line-action">
                  <Button
                    v-if="group.kategori !== 'BULANAN'"
                    icon="pi pi-trash"
                    severity="danger"
                    text
                    size="small"
                    aria-label="Hapus baris"
                    @click="removeLine(index)"
                  />
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
          @click="cancelEditor"
        />
        <Button
          label="Simpan Tagihan"
          icon="pi pi-check"
          :disabled="editor.lines.length === 0"
          :loading="saving"
          @click="saveEditor"
        />
      </template>
    </Dialog>

    <!-- Struk / Cetak -->
    <Dialog
      v-model:visible="strukDialog"
      header="Faktur Tagihan"
      modal
      :style="{ width: '32rem' }"
      class="struk-dialog"
      :dismissable-mask="true"
    >
      <InvoicePreview v-if="struk" id="struk-print-area" :invoice="struk" printable />
      <template #footer>
        <Button label="Tutup" severity="secondary" text @click="strukDialog = false" />
        <Button label="Cetak" icon="pi pi-print" @click="cetak" />
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
  font-family: "Baloo 2", "Nunito Sans", system-ui, sans-serif;
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
  font-family: "Nunito Sans", system-ui, sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
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
  color: var(--bee-purple-700, #6b21a8);
}
</style>

<style>
.tagihan-editor-dialog .p-dialog-content {
  overflow-x: hidden;
}
</style>
