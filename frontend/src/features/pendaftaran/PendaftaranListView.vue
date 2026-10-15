<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import Checkbox from "primevue/checkbox"
import DataTable from "primevue/datatable"
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
import { useRouter } from "vue-router"

import { pendaftaranSiswaApi } from "./api"
import { jenjangApi } from "@/features/absensi/api"
import { coaApi } from "@/features/jurnal/api"
import { formatRp } from "@/core/format"
import { notifyError, notifySuccess } from "@/core/errors"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import SearchField from "@/shared/components/SearchField.vue"
import { useTableSearch } from "@/shared/composables/useTableSearch"
import type { Coa, Jenjang, PendaftaranSiswa, PendaftaranSiswaStatus } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()
const router = useRouter()

const rows = ref<PendaftaranSiswa[]>([])
const jenjangList = ref<Jenjang[]>([])
const loading = ref(false)
const filterStatus = ref<PendaftaranSiswaStatus | null>(null)

const STATUS_OPTIONS = [
  { label: "Semua status", value: null as PendaftaranSiswaStatus | null },
  { label: "Sit-in / Trial", value: "TRIAL" as const },
  { label: "Terdaftar", value: "REGISTERED" as const },
  { label: "Batal", value: "BATAL" as const },
]

const statusLabel: Record<PendaftaranSiswaStatus, string> = {
  TRIAL: "Sit-in / Trial",
  REGISTERED: "Terdaftar",
  BATAL: "Batal",
}

const statusSeverity: Record<PendaftaranSiswaStatus, string> = {
  TRIAL: "warn",
  REGISTERED: "success",
  BATAL: "danger",
}

const jenjangMap = computed(() => {
  const m = new Map<number, string>()
  jenjangList.value.forEach((j) => m.set(j.id, j.kode))
  return m
})

const filteredRows = computed(() =>
  filterStatus.value ? rows.value.filter((r) => r.status === filterStatus.value) : rows.value,
)

const { query: searchQuery, filtered: displayRows } = useTableSearch(filteredRows, (row) => [
  row.nama_calon,
  row.jenjang ? jenjangMap.value.get(row.jenjang) ?? String(row.jenjang) : "",
  formatDate(row.tanggal_daftar),
  formatRp(row.biaya_sitin),
  formatRp(row.biaya_pendaftaran),
  statusLabel[row.status],
  row.jurnal_sitin ? "jurnal sit-in sudah" : "jurnal sit-in belum",
  row.jurnal_pendaftaran ? "jurnal daftar sudah" : "jurnal daftar belum",
])

function toDateStr(d: Date | null): string {
  if (!d) return ""
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

async function load() {
  loading.value = true
  try {
    const [data, jenjangs] = await Promise.all([
      pendaftaranSiswaApi.listAll(),
      jenjangApi.list(),
    ])
    rows.value = data
    jenjangList.value = jenjangs
  } catch (e) {
    notifyError(toast, e, "Gagal memuat pendaftaran siswa.")
  } finally {
    loading.value = false
  }
}

// --- form CRUD ---
const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  nama_calon: "",
  jenjang: null as number | null,
  tanggal_daftar: new Date() as Date | null,
  biaya_sitin: null as number | null,
  biaya_formulir: null as number | null,
})
const formError = ref("")
const editingRow = ref<PendaftaranSiswa | null>(null)
const totalForm = computed(() => form.biaya_sitin === null || form.biaya_formulir === null ? null
  : (Math.round(form.biaya_sitin * 100) + Math.round(form.biaya_formulir * 100)) / 100)

function openCreate() {
  formError.value = ""
  editingRow.value = null
  editingId.value = null
  Object.assign(form, {
    nama_calon: "",
    jenjang: jenjangList.value[0]?.id ?? null,
    tanggal_daftar: new Date(),
    biaya_sitin: null,
    biaya_formulir: null,
  })
  dialog.value = true
}

function openEdit(row: PendaftaranSiswa) {
  formError.value = ""
  editingRow.value = row
  editingId.value = row.id
  Object.assign(form, {
    nama_calon: row.nama_calon,
    jenjang: row.jenjang,
    tanggal_daftar: new Date(row.tanggal_daftar + "T00:00:00"),
    biaya_sitin: Number(row.biaya_sitin),
    biaya_formulir: row.biaya_formulir === null ? null : Number(row.biaya_formulir),
  })
  dialog.value = true
}

async function save() {
  if (saving.value) return
  formError.value = ""
  if (!form.nama_calon.trim() || !form.tanggal_daftar || form.biaya_sitin === null || form.biaya_formulir === null
      || !Number.isFinite(form.biaya_sitin) || !Number.isFinite(form.biaya_formulir)
      || form.biaya_sitin < 0 || form.biaya_formulir < 0) {
    formError.value = "Isi nama, tanggal daftar, dan kedua komponen biaya. Isi 0 jika komponen memang tidak dikenakan."
    return
  }
  saving.value = true
  try {
    const payload = {
      nama_calon: form.nama_calon.trim(),
      jenjang: form.jenjang,
      tanggal_daftar: toDateStr(form.tanggal_daftar),
      biaya_sitin: form.biaya_sitin.toFixed(2),
      biaya_formulir: form.biaya_formulir.toFixed(2),
    }
    if (editingId.value) {
      await pendaftaranSiswaApi.update(editingId.value, payload)
      notifySuccess(toast, "Pendaftaran diperbarui.")
    } else {
      await pendaftaranSiswaApi.create(payload)
      notifySuccess(toast, "Calon siswa ditambahkan.", {
        detail: "Status awal: Sit-in / Trial.",
      })
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan pendaftaran.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: PendaftaranSiswa) {
  confirm.require({
    header: "Hapus pendaftaran?",
    message: `Hapus data calon "${row.nama_calon}"?`,
    acceptLabel: "Hapus",
    rejectLabel: "Batal",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await pendaftaranSiswaApi.remove(row.id)
        notifySuccess(toast, "Pendaftaran dihapus.")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus pendaftaran.")
      }
    },
  })
}

const rincianTarget = ref<PendaftaranSiswa | null>(null)
const bayarDialog = ref(false)
const bayarTarget = ref<PendaftaranSiswa | null>(null)
const bayarSaving = ref(false)
const bayarError = ref("")
const loadingKas = ref(false)
const akunKas = ref<Coa[]>([])
const bayarForm = reactive({ tanggal: new Date() as Date | null, no_bukti: "", akun_kas: null as string | null })
const komponenBayar = ref<("FORMULIR" | "SITIN")[]>([])
const opsiKomponen = computed(() => bayarTarget.value ? [
  { kode: "FORMULIR" as const, label: "Formulir", nominal: Number(bayarTarget.value.biaya_formulir), dibayar: bayarTarget.value.formulir_terbayar },
  { kode: "SITIN" as const, label: "Sit-in / observasi", nominal: Number(bayarTarget.value.biaya_sitin), dibayar: bayarTarget.value.sitin_terbayar },
] : [])
const totalBayar = computed(() => opsiKomponen.value.filter((o) => komponenBayar.value.includes(o.kode))
  .reduce((total, o) => total + Math.round(o.nominal * 100), 0) / 100)

async function openBayar(row: PendaftaranSiswa) {
  bayarTarget.value = row
  bayarError.value = ""
  Object.assign(bayarForm, { tanggal: new Date(), no_bukti: "", akun_kas: null })
  komponenBayar.value = opsiKomponen.value.filter((o) => !o.dibayar && o.nominal > 0).map((o) => o.kode)
  bayarDialog.value = true
  loadingKas.value = true
  try {
    akunKas.value = (await coaApi.list()).filter((a) => a.is_active && ["111", "112", "1011", "1101", "1102"].includes(a.kode_akun))
  } catch (e) {
    akunKas.value = []
    notifyError(toast, e, "Gagal memuat Kas/Bank.")
  } finally {
    loadingKas.value = false
  }
}

async function runBayar() {
  if (!bayarTarget.value || bayarSaving.value) return
  bayarError.value = ""
  if (!bayarForm.tanggal || !bayarForm.no_bukti.trim() || !bayarForm.akun_kas || totalBayar.value <= 0) {
    bayarError.value = "Pilih komponen, tanggal, nomor bukti, dan Kas/Bank penerimaan."
    return
  }
  bayarSaving.value = true
  try {
    await pendaftaranSiswaApi.bayar(bayarTarget.value.id, {
      komponen: [...komponenBayar.value], tanggal: toDateStr(bayarForm.tanggal), no_bukti: bayarForm.no_bukti.trim(),
      akun_kas: bayarForm.akun_kas, nominal: totalBayar.value.toFixed(2),
    })
    notifySuccess(toast, "Penerimaan tersimpan; jurnal menunggu pencatatan Finance.")
    bayarDialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal mencatat penerimaan pendaftaran.")
  } finally {
    bayarSaving.value = false
  }
}

// --- finalisasi ---
const finalDialog = ref(false)
const finalSaving = ref(false)
const finalTarget = ref<PendaftaranSiswa | null>(null)
const sppNominal = ref<number | null>(null)
const finalError = ref("")

function openFinalisasi(row: PendaftaranSiswa) {
  finalTarget.value = row
  sppNominal.value = null
  finalError.value = ""
  finalDialog.value = true
}

async function runFinalisasi() {
  if (!finalTarget.value || finalSaving.value) return
  finalError.value = ""
  if (sppNominal.value === null || !Number.isFinite(sppNominal.value) || sppNominal.value < 0) {
    finalError.value = "Isi nominal SPP bulanan yang disepakati. Isi 0 jika memang tidak dikenakan."
    return
  }
  finalSaving.value = true
  try {
    const res = await pendaftaranSiswaApi.finalisasi(
      finalTarget.value.id,
      sppNominal.value.toFixed(2),
    )
    notifySuccess(toast, `${finalTarget.value.nama_calon} resmi terdaftar sebagai siswa.`, {
      detail: "Finalisasi tidak mencatat penerimaan uang."
    })
    finalDialog.value = false
    finalTarget.value = null
    await load()
    if (res.siswa) {
      confirm.require({
        header: "Lanjut ke data siswa?",
        message: "Calon sudah jadi siswa aktif. Buka halaman Data Siswa untuk melengkapi profil?",
        acceptLabel: "Buka Data Siswa",
        rejectLabel: "Nanti",
        accept: () => router.push("/siswa"),
      })
    }
  } catch (e) {
    notifyError(toast, e, "Gagal finalisasi pendaftaran.")
  } finally {
    finalSaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <PageLayout
    title="Pendaftaran Siswa"
    subtitle="Rincian biaya formulir dan sit-in, penerimaan, serta finalisasi siswa"
  >
    <template #actions>
      <Button label="Daftar Calon Baru" icon="pi pi-user-plus" @click="openCreate" />
    </template>

    <template #filters>
      <SearchField
        v-model="searchQuery"
        hint="Cari nama calon, jenjang, status, biaya"
      />
      <Select
        v-model="filterStatus"
        :options="STATUS_OPTIONS"
        option-label="label"
        option-value="value"
        placeholder="Filter status"
        class="bee-filter-field"
      />
    </template>

    <Message severity="info" :closable="false" class="bee-mb">
      <strong>Alur pendaftaran calon siswa:</strong>
      <ol class="info-steps">
        <li><strong>Daftar calon</strong> — isi biaya formulir dan sit-in/observasi sesuai kesepakatan. Total dijumlahkan otomatis.</li>
        <li><strong>Catat penerimaan</strong> — pilih komponen yang benar-benar dibayar, tanggal, bukti, serta Kas/Bank.</li>
        <li><strong>Finalisasi</strong> — calon resmi jadi siswa dan nominal SPP ditetapkan. Finalisasi tidak mencatat pembayaran.</li>
      </ol>
      Setiap pembayaran otomatis membuat jurnal akuntansi berstatus <strong>DRAFT</strong> (perlu diposting di menu Jurnal).
    </Message>
    <Message v-if="rows.some((row) => row.perlu_rekonsiliasi)" severity="warn" :closable="false" class="bee-mb">
      Data lama yang rincian biayanya belum dicocokkan ditandai <strong>Perlu dicocokkan</strong>.
      Jumlah dibayar dan sisa belum ditetapkan; penerimaan baru diblokir agar tidak ditagih ulang.
    </Message>

    <DataTable
      :value="displayRows"
      :loading="loading"
      data-key="id"
      paginator :rows="15"
      striped-rows
    >
      <template #empty>
        <EmptyState message="Belum ada calon siswa. Klik Daftar Calon Baru untuk memulai." />
      </template>

      <Column field="nama_calon" header="Nama Calon" sortable />
      <Column field="jenjang" header="Jenjang">
        <template #body="{ data }">
          {{ data.jenjang ? jenjangMap.get(data.jenjang) ?? `#${data.jenjang}` : "—" }}
        </template>
      </Column>
      <Column field="tanggal_daftar" header="Tanggal Daftar">
        <template #body="{ data }">
          {{ formatDate(data.tanggal_daftar) }}
        </template>
      </Column>
      <Column header="Rincian Biaya">
        <template #body="{ data }">
          <div>Formulir: {{ data.biaya_formulir === null ? 'Belum dipetakan' : formatRp(data.biaya_formulir) }}</div>
          <div>Sit-in: {{ formatRp(data.biaya_sitin) }}</div>
        </template>
      </Column>
      <Column header="Total Pendaftaran">
        <template #body="{ data }">
          {{ data.total_biaya === null ? 'Perlu dicocokkan' : formatRp(data.total_biaya) }}
        </template>
      </Column>
      <Column header="Status" style="width: 7rem">
        <template #body="{ data }">
          <Tag :value="statusLabel[data.status as PendaftaranSiswaStatus]" :severity="statusSeverity[data.status as PendaftaranSiswaStatus]" />
        </template>
      </Column>
      <Column header="Penerimaan">
        <template #body="{ data }">
          {{ data.total_terbayar === null ? 'Belum diketahui' : formatRp(data.total_terbayar) }}
        </template>
      </Column>
      <Column header="Sisa">
        <template #body="{ data }">
          <Tag v-if="data.perlu_rekonsiliasi" value="Perlu dicocokkan" severity="warn" />
          <span v-else>{{ formatRp(data.sisa_biaya) }}</span>
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--xl" bodyClass="bee-col-actions--xl">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button label="Rincian" size="small" text @click="rincianTarget = data" />
            <Button v-if="data.status !== 'BATAL' && !data.perlu_rekonsiliasi && Number(data.sisa_biaya) > 0"
              label="Catat Penerimaan" size="small" severity="success" outlined @click="openBayar(data)" />
            <template v-if="data.status === 'TRIAL'">
              <Button
                label="Finalisasi"
                size="small"
                @click="openFinalisasi(data)"
              />
              <Button
                v-if="!data.jurnal_sitin && !data.jurnal_pendaftaran"
                icon="pi pi-pencil"
                aria-label="Edit pendaftaran"
                size="small"
                text
                severity="secondary"
                @click="openEdit(data)"
              />
              <Button
                v-if="!data.jurnal_sitin && !data.jurnal_pendaftaran"
                icon="pi pi-trash"
                aria-label="Hapus pendaftaran"
                size="small"
                text
                severity="danger"
                @click="confirmDelete(data)"
              />
            </template>
            <template v-else-if="data.status === 'REGISTERED' && data.siswa">
              <Button
                label="Lihat Siswa"
                size="small"
                text
                @click="router.push('/siswa')"
              />
            </template>
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Form calon -->
    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Pendaftaran' : 'Daftar Calon Siswa'"
      modal
      :style="{ width: 'min(480px, 96vw)' }"
    >
      <div class="bee-form-stack">
        <Message v-if="editingRow?.perlu_rekonsiliasi" severity="warn" :closable="false">
          Nilai biaya pendaftaran lama {{ formatRp(editingRow.biaya_pendaftaran) }} dipertahankan sebagai catatan.
          Isi biaya formulir yang benar setelah mencocokkan rincian; nilainya tidak disalin otomatis.
        </Message>
        <div class="bee-field">
          <label for="nama-calon">Nama calon</label>
          <InputText id="nama-calon" v-model="form.nama_calon" fluid />
        </div>
        <div class="bee-field">
          <label for="jenjang">Jenjang</label>
          <Select
            input-id="jenjang"
            v-model="form.jenjang"
            :options="jenjangList"
            option-label="kode"
            option-value="id"
            placeholder="Pilih jenjang"
            show-clear
            fluid
          />
        </div>
        <div class="bee-field">
          <label for="tanggal">Tanggal daftar</label>
          <DatePicker
            input-id="tanggal"
            v-model="form.tanggal_daftar"
            date-format="dd/mm/yy"
            show-icon
            fluid
          />
        </div>
        <div class="bee-field">
          <label for="sitin">Biaya sit-in</label>
          <InputNumber input-id="sitin" v-model="form.biaya_sitin" :min="0" :max-fraction-digits="2" locale="id-ID" fluid />
        </div>
        <div class="bee-field">
          <label for="formulir">Biaya formulir</label>
          <InputNumber input-id="formulir" v-model="form.biaya_formulir" :min="0" :max-fraction-digits="2" locale="id-ID" fluid />
        </div>
        <p><strong>Total biaya pendaftaran: {{ totalForm === null ? 'Isi kedua komponen' : formatRp(totalForm) }}</strong></p>
        <small>Tarif mengikuti kesepakatan sekolah. Isi 0 jika komponen memang tidak dikenakan.</small>
        <Message v-if="formError" severity="error" :closable="false" role="alert">{{ formError }}</Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button
          label="Simpan"
          :loading="saving"
          :disabled="saving"
          @click="save"
        />
      </template>
    </Dialog>

    <!-- Finalisasi -->
    <Dialog
      v-model:visible="finalDialog"
      header="Finalisasi Pendaftaran"
      modal
      :style="{ width: 'min(420px, 96vw)' }"
    >
      <p v-if="finalTarget" class="bee-final-intro">
        Finalisasi <strong>{{ finalTarget.nama_calon }}</strong> menjadi siswa resmi.
        Finalisasi tidak mencatat penerimaan uang atau menganggap biaya sudah lunas.
      </p>
      <div class="bee-field">
        <label for="spp">Nominal SPP bulanan</label>
        <InputNumber input-id="spp" v-model="sppNominal" :min="0" :max-fraction-digits="2" locale="id-ID" fluid />
      </div>
      <Message v-if="finalError" severity="error" :closable="false" role="alert">{{ finalError }}</Message>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="finalDialog = false" />
        <Button label="Finalisasi" :loading="finalSaving" :disabled="finalSaving" @click="runFinalisasi" />
      </template>
    </Dialog>

    <Dialog v-model:visible="bayarDialog" header="Catat Penerimaan Pendaftaran" modal :closable="!bayarSaving" :style="{ width: 'min(480px, 96vw)' }">
      <div class="bee-form-stack">
        <p>{{ bayarTarget?.nama_calon }}</p>
        <div v-for="opsi in opsiKomponen" :key="opsi.kode">
          <Checkbox v-model="komponenBayar" :input-id="`bayar-${opsi.kode}`" :value="opsi.kode" :disabled="bayarSaving || !!opsi.dibayar || opsi.nominal <= 0" />
          <label :for="`bayar-${opsi.kode}`"> {{ opsi.label }} — {{ formatRp(opsi.nominal) }}{{ opsi.dibayar ? ' (sudah diterima)' : '' }}</label>
        </div>
        <strong>Jumlah diterima: {{ formatRp(totalBayar) }}</strong>
        <small>Penerimaan mencakup seluruh nilai komponen yang dipilih. Komponen yang sudah diterima tidak ditagih lagi.</small>
        <div class="bee-field"><label for="bayar-tanggal">Tanggal penerimaan</label><DatePicker input-id="bayar-tanggal" v-model="bayarForm.tanggal" date-format="dd/mm/yy" :disabled="bayarSaving" show-icon fluid /></div>
        <div class="bee-field"><label for="bayar-bukti">Nomor bukti penerimaan</label><InputText id="bayar-bukti" v-model="bayarForm.no_bukti" :maxlength="50" :disabled="bayarSaving" fluid /></div>
        <div class="bee-field"><label for="bayar-kas">Kas / Bank penerimaan</label><Select input-id="bayar-kas" v-model="bayarForm.akun_kas" :options="akunKas" option-label="nama_akun" option-value="kode_akun" placeholder="Pilih Kas/Bank" :loading="loadingKas" :disabled="bayarSaving" fluid /></div>
        <Message v-if="bayarError" severity="error" :closable="false" role="alert">{{ bayarError }}</Message>
      </div>
      <template #footer>
        <Button label="Batal" text severity="secondary" :disabled="bayarSaving" @click="bayarDialog = false" />
        <Button label="Simpan Penerimaan" :loading="bayarSaving" :disabled="bayarSaving || loadingKas" @click="runBayar" />
      </template>
    </Dialog>

    <Dialog :visible="!!rincianTarget" header="Rincian Pendaftaran" modal :style="{ width: 'min(560px, 96vw)' }" @update:visible="rincianTarget = null">
      <div v-if="rincianTarget" class="bee-form-stack">
        <strong>{{ rincianTarget.nama_calon }}</strong>
        <Message v-if="rincianTarget.perlu_rekonsiliasi" severity="warn" :closable="false">
          Biaya/penerimaan lama perlu dicocokkan dengan bukti. Nilai biaya pendaftaran lama: {{ formatRp(rincianTarget.biaya_pendaftaran) }}.
          Total, jumlah dibayar, dan sisa belum dapat dipastikan.
        </Message>
        <p v-else>Total {{ formatRp(rincianTarget.total_biaya) }} · Diterima {{ formatRp(rincianTarget.total_terbayar) }} · Sisa {{ formatRp(rincianTarget.sisa_biaya) }}</p>
        <p v-if="!rincianTarget.pembayaran.length">Belum ada catatan penerimaan.</p>
        <div v-for="p in rincianTarget.pembayaran" :key="p.jurnal_id">
          <strong>{{ p.no_bukti }} — {{ formatRp(p.nominal) }}</strong>
          <div>{{ formatDate(p.tanggal) }} · {{ p.komponen.join(' + ') }}</div>
          <Tag :value="p.dibatalkan ? 'Dibatalkan' : `Jurnal ${p.status}`" :severity="p.dibatalkan ? 'warn' : 'info'" />
        </div>
        <small>Penerimaan yang jurnalnya masih DRAFT/PENDING menunggu pencatatan Finance ke buku besar.</small>
      </div>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.bee-filter-field {
  min-width: 12rem;
}

.bee-mb {
  margin-bottom: 1rem;
}

.info-steps {
  margin: 0.5rem 0 0.5rem 1.25rem;
  padding: 0;
  line-height: 1.55;
}

.info-steps li {
  margin-bottom: 0.25rem;
}

.bee-form-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bee-field label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
  color: var(--bee-navy-700);
}

.muted {
  color: var(--app-text-muted);
  font-size: 0.85rem;
}

.bee-final-intro {
  margin: 0 0 1rem;
  line-height: 1.5;
}
</style>
