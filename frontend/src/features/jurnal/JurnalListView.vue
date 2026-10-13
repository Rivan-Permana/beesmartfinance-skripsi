<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
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
import { useRoute } from "vue-router"

import { coaApi, jurnalApi } from "./api"
import { notifyError, notifySuccess, jurnalActionSuccessMessage } from "@/core/errors"
import { formatRp } from "@/core/format"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Coa, Jurnal, JurnalStatus } from "@/types/api"

const route = useRoute()

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Jurnal[]>([])
const coaList = ref<Coa[]>([])
const loading = ref(false)
const statusFilter = ref<JurnalStatus | null>(null)

const STATUS_OPTS: { label: string; value: JurnalStatus }[] = [
  { label: "Draft", value: "DRAFT" },
  { label: "Pending", value: "PENDING" },
  { label: "Posted", value: "POSTED" },
  { label: "Void", value: "VOID" },
]
const statusSeverity: Record<JurnalStatus, string> = {
  DRAFT: "secondary",
  PENDING: "warn",
  POSTED: "success",
  VOID: "danger",
}

const canCreate = computed(() => auth.hasRole(["Finance"]))
const canApprove = computed(() => auth.hasRole(["SchoolPrincipal"]))

const jenisFilter = computed(() => {
  const j = route.query.jenis
  return j === "masuk" || j === "keluar" ? j : null
})

const pageTitle = computed(() => {
  if (jenisFilter.value === "masuk") return "Pemasukan"
  if (jenisFilter.value === "keluar") return "Pengeluaran"
  return "Jurnal"
})

const pageSubtitle = computed(() => {
  if (jenisFilter.value === "masuk") return "Transaksi pendapatan (akun 4.x)"
  if (jenisFilter.value === "keluar") return "Transaksi beban (akun 5.x)"
  return "Catat, submit, dan approve jurnal akuntansi"
})

const filteredRows = computed(() => {
  if (!jenisFilter.value) return rows.value
  const prefix = jenisFilter.value === "masuk" ? "4" : "5"
  return rows.value.filter((j) =>
    (j.detail ?? []).some((d) => d.kode_akun.startsWith(prefix)),
  )
})

const coaOptionsForForm = computed(() => {
  if (jenisFilter.value === "masuk") {
    return coaList.value.filter((c) => c.kode_akun.startsWith("4"))
  }
  if (jenisFilter.value === "keluar") {
    return coaList.value.filter((c) => c.kode_akun.startsWith("5"))
  }
  return coaList.value
})

async function load() {
  loading.value = true
  try {
    const data = await jurnalApi.list(
      statusFilter.value ? { status: statusFilter.value } : {},
    )
    rows.value = data.results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat jurnal.")
  } finally {
    loading.value = false
  }
}

// --- form ---
const dialog = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive<{
  no_bukti: string
  tanggal: Date
  keterangan: string
  detail: { kode_akun: string | null; debit: number; kredit: number }[]
}>({ no_bukti: "", tanggal: new Date(), keterangan: "", detail: [] })

function openCreate() {
  editingId.value = null
  form.no_bukti = ""
  form.tanggal = new Date()
  form.keterangan = ""
  const preset = coaOptionsForForm.value[0]?.kode_akun ?? null
  form.detail = [
    { kode_akun: preset, debit: 0, kredit: 0 },
    { kode_akun: null, debit: 0, kredit: 0 },
  ]
  dialog.value = true
}

function openEdit(j: Jurnal) {
  editingId.value = j.id
  form.no_bukti = j.no_bukti
  form.tanggal = new Date(j.tanggal)
  form.keterangan = j.keterangan ?? ""
  form.detail = (j.detail ?? []).map((d) => ({
    kode_akun: d.kode_akun,
    debit: Number(d.debit) || 0,
    kredit: Number(d.kredit) || 0,
  }))
  if (form.detail.length < 2) {
    form.detail.push({ kode_akun: null, debit: 0, kredit: 0 })
  }
  dialog.value = true
}

const dialogTitle = computed(() =>
  editingId.value ? "Ubah Jurnal Draft" : "Buat Jurnal",
)

function addLine() {
  form.detail.push({ kode_akun: null, debit: 0, kredit: 0 })
}
function removeLine(i: number) {
  form.detail.splice(i, 1)
}

const totalDebit = computed(() =>
  form.detail.reduce((s, d) => s + (Number(d.debit) || 0), 0),
)
const totalKredit = computed(() =>
  form.detail.reduce((s, d) => s + (Number(d.kredit) || 0), 0),
)
const balanced = computed(
  () => totalDebit.value === totalKredit.value && totalDebit.value > 0,
)
const formValid = computed(
  () =>
    form.no_bukti.trim() !== "" &&
    balanced.value &&
    form.detail.every((d) => d.kode_akun),
)

function fmt(n: number) {
  return formatRp(n)
}

async function save() {
  saving.value = true
  try {
    const payload = {
      no_bukti: form.no_bukti,
      tanggal: form.tanggal.toISOString().slice(0, 10),
      keterangan: form.keterangan,
      detail: form.detail.map((d) => ({
        kode_akun: d.kode_akun as string,
        debit: String(d.debit || 0),
        kredit: String(d.kredit || 0),
      })),
    }
    if (editingId.value) {
      await jurnalApi.update(editingId.value, payload)
      notifySuccess(toast, "Jurnal draft diperbarui")
    } else {
      await jurnalApi.create(payload)
      notifySuccess(toast, "Jurnal dibuat sebagai DRAFT")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, editingId.value ? "Gagal menyimpan perubahan." : "Gagal membuat jurnal.")
  } finally {
    saving.value = false
  }
}

function removeDraft(j: Jurnal) {
  confirm.require({
    message: `Hapus jurnal draft ${j.no_bukti}?`,
    header: "Konfirmasi Hapus",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await jurnalApi.remove(j.id)
        notifySuccess(toast, "Jurnal draft dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus jurnal.")
      }
    },
  })
}

async function doAction(
  fn: () => Promise<unknown>,
  action?: "submit" | "approve" | "void",
) {
  try {
    const res = await fn()
    if (action) {
      const msg = jurnalActionSuccessMessage(action, res)
      notifySuccess(toast, msg.summary, { detail: msg.detail })
    } else {
      notifySuccess(toast, "Berhasil")
    }
    await load()
  } catch (e) {
    notifyError(toast, e, "Tindakan gagal diproses.")
  }
}

function submit(j: Jurnal) {
  doAction(() => jurnalApi.submit(j.id), "submit")
}
function approve(j: Jurnal) {
  doAction(() => jurnalApi.approve(j.id), "approve")
}
function voidJurnal(j: Jurnal) {
  confirm.require({
    message: `Batalkan jurnal ${j.no_bukti} via jurnal pembalik?`,
    header: "Konfirmasi Void",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Void",
    acceptClass: "p-button-danger",
    accept: () => doAction(() => jurnalApi.void(j.id), "void"),
  })
}

onMounted(async () => {
  await load()
  try {
    coaList.value = await coaApi.list()
  } catch {
    /* abaikan; select kosong */
  }
})
</script>

<template>
  <PageLayout :title="pageTitle" :subtitle="pageSubtitle">
    <template #actions>
      <Button
        v-if="canCreate"
        label="Buat Jurnal"
        icon="pi pi-plus"
        @click="openCreate"
      />
    </template>

    <template #filters>
      <Select
        v-model="statusFilter"
        :options="STATUS_OPTS"
        option-label="label"
        option-value="value"
        placeholder="Semua status"
        show-clear
        @change="load"
      />
    </template>

    <Message severity="info" :closable="false" class="jurnal-hint">
      <template v-if="jenisFilter === 'masuk'">
        Catat <strong>pemasukan</strong> (akun pendapatan 4.x). Draft bisa diedit sebelum diajukan ke Kepala Sekolah.
      </template>
      <template v-else-if="jenisFilter === 'keluar'">
        Catat <strong>pengeluaran</strong> (akun beban 5.x). Draft bisa diedit sebelum diajukan ke Kepala Sekolah.
      </template>
      <template v-else>
        Buat jurnal manual, submit untuk approval, lalu approve untuk masuk buku besar (POSTED).
      </template>
    </Message>

    <DataTable :value="filteredRows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada jurnal.</template>
      <Column field="no_bukti" header="No. Bukti" />
      <Column field="tanggal" header="Tanggal" />
      <Column field="keterangan" header="Keterangan" />
      <Column header="Sumber">
        <template #body="{ data }">
          <span class="muted">{{ data.tipe_sumber }}</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity[data.status as JurnalStatus]" />
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--xl" bodyClass="bee-col-actions--xl">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button
              v-if="data.status === 'DRAFT' && canCreate"
              label="Edit"
              size="small"
              text
              @click="openEdit(data)"
            />
            <Button
              v-if="data.status === 'DRAFT' && canCreate"
              label="Submit"
              size="small"
              text
              @click="submit(data)"
            />
            <Button
              v-if="data.status === 'DRAFT' && canCreate"
              icon="pi pi-trash"
              size="small"
              severity="danger"
              text
              rounded
              aria-label="Hapus draft"
              @click="removeDraft(data)"
            />
            <Button
              v-if="data.status === 'PENDING' && canApprove"
              label="Approve"
              size="small"
              severity="success"
              text
              @click="approve(data)"
            />
            <Button
              v-if="data.status === 'POSTED' && canApprove"
              label="Void"
              size="small"
              severity="danger"
              text
              @click="voidJurnal(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      :header="dialogTitle"
      modal
      :style="{ width: '56rem' }"
    >
      <div class="head-form">
        <div class="field">
          <label>No. Bukti *</label>
          <InputText v-model="form.no_bukti" fluid />
        </div>
        <div class="field">
          <label>Tanggal *</label>
          <DatePicker v-model="form.tanggal" date-format="yy-mm-dd" fluid />
        </div>
        <div class="field grow">
          <label>Keterangan</label>
          <InputText v-model="form.keterangan" fluid />
        </div>
      </div>

      <table class="lines">
        <thead>
          <tr>
            <th style="width: 45%">Akun</th>
            <th>Debit</th>
            <th>Kredit</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(d, i) in form.detail" :key="i">
            <td>
              <Select
                v-model="d.kode_akun"
                :options="coaOptionsForForm"
                option-label="nama_akun"
                option-value="kode_akun"
                filter
                placeholder="Pilih akun"
                fluid
              >
                <template #option="{ option }">
                  <span>{{ option.kode_akun }} — {{ option.nama_akun }}</span>
                </template>
              </Select>
            </td>
            <td><InputNumber v-model="d.debit" :min="0" fluid /></td>
            <td><InputNumber v-model="d.kredit" :min="0" fluid /></td>
            <td>
              <Button
                icon="pi pi-times"
                text
                rounded
                severity="danger"
                :disabled="form.detail.length <= 2"
                @click="removeLine(i)"
              />
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td><Button label="Tambah Baris" icon="pi pi-plus" text size="small" @click="addLine" /></td>
            <td :class="{ bad: !balanced }">{{ fmt(totalDebit) }}</td>
            <td :class="{ bad: !balanced }">{{ fmt(totalKredit) }}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
      <p v-if="!balanced" class="warn">Debit dan kredit harus seimbang dan &gt; 0.</p>
      <p v-else class="ok-hint">
        <i class="pi pi-check-circle" /> Jurnal seimbang — akan disimpan sebagai DRAFT, lalu Submit → Approve (Kepsek).
      </p>

      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan (DRAFT)" :disabled="!formValid" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.jurnal-hint {
  margin-bottom: 1rem;
}
.muted {
  color: var(--app-text-muted);
  font-size: 0.85rem;
}
.head-form {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.field.grow {
  flex: 1;
}
.field label {
  font-weight: 600;
  font-size: 0.85rem;
}
.lines {
  width: 100%;
  border-collapse: collapse;
}
.lines th,
.lines td {
  padding: 0.35rem 0.4rem;
  text-align: left;
}
.lines tfoot td {
  font-weight: 800;
  border-top: 2px solid var(--app-border);
}
.lines .bad {
  color: var(--bee-magenta);
}
.warn {
  color: var(--bee-magenta);
  font-size: 0.85rem;
  margin-top: 0.5rem;
}
.ok-hint {
  color: #2e9e5b;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}
</style>
