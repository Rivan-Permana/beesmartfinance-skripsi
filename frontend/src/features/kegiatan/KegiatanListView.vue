<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import ProgressBar from "primevue/progressbar"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { kegiatanApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import { periodeApi } from "@/features/anggaran-periode/api"
import { coaApi } from "@/features/jurnal/api"
import { filterCoaBeban } from "@/features/coa/filters"
import { pegawaiApi } from "@/features/kepegawaian/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type {
  Coa,
  Kegiatan,
  KegiatanStatus,
  LaporanKegiatan,
  Pegawai,
  PeriodeAkuntansi,
} from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Kegiatan[]>([])
const coaList = ref<Coa[]>([])
const coaBebanOptions = computed(() => filterCoaBeban(coaList.value))
const pegawaiList = ref<Pegawai[]>([])
const periodeList = ref<PeriodeAkuntansi[]>([])
const periodeFilter = ref<number | null>(null)
const loading = ref(false)

const canManage = computed(() => auth.hasRole(["SchoolPrincipal"]))
const canRealisasi = computed(() => auth.hasRole(["TeacherInCharge", "SchoolPrincipal"]))

const STATUS_OPTS: { label: string; value: KegiatanStatus }[] = [
  { label: "Rencana", value: "RENCANA" },
  { label: "Berjalan", value: "BERJALAN" },
  { label: "Selesai", value: "SELESAI" },
]
const statusSeverity: Record<KegiatanStatus, string> = {
  RENCANA: "secondary", BERJALAN: "info", SELESAI: "success",
}

function rp(v: string | number | null | undefined) {
  return formatRp(v)
}
function pct(v: number) {
  return Math.round(v * 100)
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {}
    if (periodeFilter.value) params.periode = periodeFilter.value
    rows.value = (await kegiatanApi.list(params)).results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data kegiatan.")
  } finally {
    loading.value = false
  }
}

// --- form: buat / edit kegiatan (Principal) ---
const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<{
  nama: string
  akun_beban: string | null
  pagu: number
  penanggung_jawab: number | null
  periode: number | null
  tanggal_mulai: Date | null
  tanggal_selesai: Date | null
  status: KegiatanStatus
}>({
  nama: "", akun_beban: null, pagu: 0, penanggung_jawab: null, periode: null,
  tanggal_mulai: null, tanggal_selesai: null, status: "RENCANA",
})

function openCreate() {
  editingId.value = null
  form.nama = ""; form.akun_beban = null; form.pagu = 0
  form.penanggung_jawab = null
  form.periode = periodeList.value.find((p) => p.status === "OPEN")?.id ?? null
  form.tanggal_mulai = null; form.tanggal_selesai = null
  form.status = "RENCANA"
  dialog.value = true
}

function openEdit(k: Kegiatan) {
  editingId.value = k.id
  form.nama = k.nama
  form.akun_beban = k.akun_beban
  form.pagu = Number(k.pagu)
  form.penanggung_jawab = k.penanggung_jawab
  form.periode = k.periode
  form.tanggal_mulai = k.tanggal_mulai ? new Date(k.tanggal_mulai + "T12:00:00") : null
  form.tanggal_selesai = k.tanggal_selesai ? new Date(k.tanggal_selesai + "T12:00:00") : null
  form.status = k.status
  dialog.value = true
}

async function save() {
  if (!form.nama || !form.akun_beban || form.pagu <= 0) return
  saving.value = true
  try {
    const payload = {
      nama: form.nama,
      akun_beban: form.akun_beban,
      pagu: String(form.pagu),
      penanggung_jawab: form.penanggung_jawab,
      periode: form.periode,
      tanggal_mulai: form.tanggal_mulai?.toISOString().slice(0, 10) ?? null,
      tanggal_selesai: form.tanggal_selesai?.toISOString().slice(0, 10) ?? null,
      status: form.status,
    }
    if (editingId.value) {
      await kegiatanApi.update(editingId.value, payload)
      notifySuccess(toast, "Kegiatan diperbarui")
    } else {
      await kegiatanApi.create(payload)
      notifySuccess(toast, "Kegiatan berhasil dibuat")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan kegiatan.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(k: Kegiatan) {
  confirm.require({
    message: `Hapus kegiatan "${k.nama}"? Hanya bisa jika belum ada realisasi.`,
    header: "Konfirmasi Hapus",
    icon: "pi pi-trash",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await kegiatanApi.remove(k.id)
        notifySuccess(toast, "Kegiatan dihapus.")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus kegiatan.")
      }
    },
  })
}

// --- realisasi (Teacher/Principal) ---
const realisasiDialog = ref(false)
const realisasiTarget = ref<Kegiatan | null>(null)
const realisasiSaving = ref(false)
const realisasiForm = reactive<{ tanggal: Date; deskripsi: string; nominal: number }>(
  { tanggal: new Date(), deskripsi: "", nominal: 0 },
)
function openRealisasi(k: Kegiatan) {
  realisasiTarget.value = k
  realisasiForm.tanggal = new Date()
  realisasiForm.deskripsi = ""
  realisasiForm.nominal = 0
  realisasiDialog.value = true
}
async function saveRealisasi() {
  if (!realisasiTarget.value || realisasiForm.nominal <= 0) return
  realisasiSaving.value = true
  try {
    const res = await kegiatanApi.realisasi(realisasiTarget.value.id, {
      tanggal: realisasiForm.tanggal.toISOString().slice(0, 10),
      deskripsi: realisasiForm.deskripsi,
      nominal: realisasiForm.nominal,
    })
    notifySuccess(toast, "Realisasi tercatat", res)
    realisasiDialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal mencatat realisasi.")
  } finally {
    realisasiSaving.value = false
  }
}

// --- laporan ---
const laporanDialog = ref(false)
const laporan = ref<LaporanKegiatan | null>(null)
async function lihatLaporan(k: Kegiatan) {
  try {
    laporan.value = await kegiatanApi.laporan(k.id)
    laporanDialog.value = true
  } catch (e) {
    notifyError(toast, e, "Gagal memuat laporan kegiatan.")
  }
}

onMounted(async () => {
  await load()
  try {
    coaList.value = await coaApi.list()
  } catch { /* fallback dropdown kosong */ }
  try {
    pegawaiList.value = (await pegawaiApi.list()).results
  } catch { /* fallback dropdown kosong */ }
  try {
    periodeList.value = (await periodeApi.list()).results
  } catch { /* fallback dropdown kosong */ }
})
</script>

<template>
  <PageLayout title="Kegiatan Sekolah" subtitle="Kelola pagu dan realisasi kegiatan per tahun pelajaran">
    <template #actions>
      <Select
        v-model="periodeFilter"
        :options="[{ label: 'Semua TA', value: null }, ...periodeList.map(p => ({ label: p.kode, value: p.id }))]"
        option-label="label"
        option-value="value"
        placeholder="Filter TA"
        show-clear
        @change="load"
      />
      <Button v-if="canManage" label="Buat Kegiatan" icon="pi pi-plus" @click="openCreate" />
    </template>

    <Message severity="info" :closable="false" class="kegiatan-hint">
      Realisasi kegiatan otomatis dijurnal ke <strong>akun beban</strong> yang dipilih dan terikat
      <strong>tahun pelajaran (periode akuntansi)</strong> jika diisi.
    </Message>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada kegiatan terdaftar.</template>
      <Column field="nama" header="Kegiatan" />
      <Column header="TA">
        <template #body="{ data }">{{ data.periode_kode ?? "—" }}</template>
      </Column>
      <Column header="Pagu"><template #body="{ data }">{{ rp(data.pagu) }}</template></Column>
      <Column header="Realisasi">
        <template #body="{ data }">{{ rp(data.realisasi) }}</template>
      </Column>
      <Column header="Sisa Pagu">
        <template #body="{ data }">{{ rp(data.sisa_pagu) }}</template>
      </Column>
      <Column header="Utilisasi" style="min-width: 12rem">
        <template #body="{ data }">
          <ProgressBar :value="pct(data.rasio_utilisasi)" />
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity[data.status as KegiatanStatus]" />
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--xl" bodyClass="bee-col-actions--xl">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button
              v-if="canManage"
              icon="pi pi-pencil"
              text
              rounded
              aria-label="Edit kegiatan"
              @click="openEdit(data)"
            />
            <Button
              v-if="canRealisasi"
              label="Realisasi"
              size="small"
              text
              @click="openRealisasi(data)"
            />
            <Button label="Laporan" size="small" text severity="secondary" @click="lihatLaporan(data)" />
            <Button
              v-if="canManage && Number(data.realisasi) === 0"
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              aria-label="Hapus kegiatan"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Buat / Edit Kegiatan -->
    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Kegiatan' : 'Buat Kegiatan'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Nama Kegiatan *</label>
          <InputText v-model="form.nama" fluid />
        </div>
        <div class="field span2">
          <label>Akun Beban *</label>
          <Select v-model="form.akun_beban" :options="coaBebanOptions" option-label="nama_akun" option-value="kode_akun" filter placeholder="Pilih akun beban" fluid />
        </div>
        <div class="field">
          <label>Pagu *</label>
          <InputNumber v-model="form.pagu" :min="0" fluid />
        </div>
        <div class="field">
          <label>Penanggung Jawab</label>
          <Select v-model="form.penanggung_jawab" :options="pegawaiList" option-label="nama" option-value="id" filter show-clear placeholder="Pilih guru" fluid />
        </div>
        <div class="field span2">
          <label>Tahun Pelajaran</label>
          <Select
            v-model="form.periode"
            :options="periodeList"
            option-label="kode"
            option-value="id"
            filter
            show-clear
            placeholder="Pilih periode TA"
            fluid
          />
        </div>
        <div class="field">
          <label>Tanggal Mulai</label>
          <DatePicker v-model="form.tanggal_mulai" date-format="yy-mm-dd" show-button-bar fluid />
        </div>
        <div class="field">
          <label>Tanggal Selesai</label>
          <DatePicker v-model="form.tanggal_selesai" date-format="yy-mm-dd" show-button-bar fluid />
        </div>
        <div class="field span2">
          <label>Status</label>
          <Select v-model="form.status" :options="STATUS_OPTS" option-label="label" option-value="value" fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan" :loading="saving" @click="save" />
      </template>
    </Dialog>

    <!-- Realisasi -->
    <Dialog v-model:visible="realisasiDialog" header="Catat Realisasi" modal :style="{ width: '28rem' }">
      <div v-if="realisasiTarget" class="form-grid">
        <div class="field span2 info">
          <strong>{{ realisasiTarget.nama }}</strong>
          <small>Sisa pagu: {{ rp(realisasiTarget.sisa_pagu) }}</small>
        </div>
        <div class="field">
          <label>Tanggal</label>
          <DatePicker v-model="realisasiForm.tanggal" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field">
          <label>Nominal *</label>
          <InputNumber v-model="realisasiForm.nominal" :min="0" fluid />
        </div>
        <div class="field span2">
          <label>Deskripsi</label>
          <InputText v-model="realisasiForm.deskripsi" placeholder="mis. sewa bus outing" fluid />
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="realisasiDialog = false" />
        <Button label="Catat" :loading="realisasiSaving" @click="saveRealisasi" />
      </template>
    </Dialog>

    <!-- Laporan -->
    <Dialog v-model:visible="laporanDialog" header="Laporan Kegiatan" modal :style="{ width: '34rem' }">
      <div v-if="laporan" class="laporan">
        <h3>{{ laporan.kegiatan }}</h3>
        <div class="lap-row"><span>Pagu</span><strong>{{ rp(laporan.pagu) }}</strong></div>
        <div class="lap-row"><span>Realisasi</span><strong>{{ rp(laporan.realisasi) }}</strong></div>
        <div class="lap-row"><span>Sisa Pagu</span><strong>{{ rp(laporan.sisa_pagu) }}</strong></div>
        <ProgressBar :value="pct(laporan.rasio_utilisasi)" />
        <h4>Rincian</h4>
        <table class="rincian">
          <thead><tr><th>Tanggal</th><th>Deskripsi</th><th class="num">Nominal</th></tr></thead>
          <tbody>
            <tr v-for="(r, i) in laporan.rincian" :key="i">
              <td>{{ r.tanggal }}</td>
              <td>{{ r.deskripsi || "-" }}</td>
              <td class="num">{{ rp(r.nominal) }}</td>
            </tr>
            <tr v-if="laporan.rincian.length === 0">
              <td colspan="3" class="muted">Belum ada realisasi.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.kegiatan-hint {
  margin-bottom: 1rem;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field label { font-weight: 600; font-size: 0.85rem; }
.field.info { background: var(--app-bg); padding: 0.6rem 0.75rem; border-radius: 8px; }
.field.info small { color: var(--app-text-muted); }
.laporan h3 { margin: 0 0 0.5rem; }
.laporan h4 { margin: 1rem 0 0.5rem; }
.lap-row { display: flex; justify-content: space-between; padding: 0.25rem 0; }
.rincian { width: 100%; border-collapse: collapse; }
.rincian th, .rincian td { padding: 0.4rem 0.3rem; text-align: left; border-bottom: 1px solid var(--app-border); }
.rincian .num { text-align: right; }
.muted { color: var(--app-text-muted); text-align: center; }
</style>
