<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { coaApi, jurnalApi } from "./api"
import { notifyError } from "@/core/errors"
import { useAuthStore } from "@/stores/auth"
import type { Coa, Jurnal, JurnalStatus } from "@/types/api"

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
const saving = ref(false)
const form = reactive<{
  no_bukti: string
  tanggal: Date
  keterangan: string
  detail: { kode_akun: string | null; debit: number; kredit: number }[]
}>({ no_bukti: "", tanggal: new Date(), keterangan: "", detail: [] })

function openCreate() {
  form.no_bukti = ""
  form.tanggal = new Date()
  form.keterangan = ""
  form.detail = [
    { kode_akun: null, debit: 0, kredit: 0 },
    { kode_akun: null, debit: 0, kredit: 0 },
  ]
  dialog.value = true
}

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
  return "Rp " + Number(n).toLocaleString("id-ID")
}

async function save() {
  saving.value = true
  try {
    await jurnalApi.create({
      no_bukti: form.no_bukti,
      tanggal: form.tanggal.toISOString().slice(0, 10),
      keterangan: form.keterangan,
      detail: form.detail.map((d) => ({
        kode_akun: d.kode_akun as string,
        debit: String(d.debit || 0),
        kredit: String(d.kredit || 0),
      })),
    })
    toast.add({ severity: "success", summary: "Jurnal dibuat (DRAFT)", life: 2500 })
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal membuat jurnal.")
  } finally {
    saving.value = false
  }
}

async function doAction(fn: () => Promise<unknown>, ok: string) {
  try {
    await fn()
    toast.add({ severity: "success", summary: ok, life: 2500 })
    await load()
  } catch (e) {
    notifyError(toast, e, "Tindakan gagal diproses.")
  }
}

function submit(j: Jurnal) {
  doAction(() => jurnalApi.submit(j.id), "Diajukan (PENDING)")
}
function approve(j: Jurnal) {
  doAction(() => jurnalApi.approve(j.id), "Disetujui (POSTED)")
}
function voidJurnal(j: Jurnal) {
  confirm.require({
    message: `Batalkan jurnal ${j.no_bukti} via jurnal pembalik?`,
    header: "Konfirmasi Void",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Batal",
    acceptLabel: "Void",
    acceptClass: "p-button-danger",
    accept: () => doAction(() => jurnalApi.void(j.id), "Jurnal dibalik (VOID)"),
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
  <div class="page">
    <div class="page-head">
      <h1>Jurnal</h1>
      <Button
        v-if="canCreate"
        label="Buat Jurnal"
        icon="pi pi-plus"
        @click="openCreate"
      />
    </div>

    <div class="toolbar">
      <Select
        v-model="statusFilter"
        :options="STATUS_OPTS"
        option-label="label"
        option-value="value"
        placeholder="Semua status"
        show-clear
        @change="load"
      />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
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
      <Column header="Aksi" style="width: 11rem">
        <template #body="{ data }">
          <Button
            v-if="data.status === 'DRAFT' && canCreate"
            label="Submit"
            size="small"
            text
            @click="submit(data)"
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
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      header="Buat Jurnal"
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
                :options="coaList"
                option-label="nama_akun"
                option-value="kode_akun"
                filter
                placeholder="Pilih akun"
                fluid
              />
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

      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan (DRAFT)" :disabled="!formValid" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.toolbar {
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
</style>
