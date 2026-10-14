<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Select from "primevue/select"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref, watch } from "vue"

import GajiSlipPreview from "./GajiSlipPreview.vue"
import { gajiApi, pegawaiApi, pinjamanApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import PageLayout from "@/shared/components/PageLayout.vue"
import { useAuthStore } from "@/stores/auth"
import type { Gaji, Pegawai, Pinjaman } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<Gaji[]>([])
const pegawaiList = ref<Pegawai[]>([])
const pinjamanList = ref<Pinjaman[]>([])
const loading = ref(false)

const canWrite = computed(() => auth.hasRole(["Finance"]))
const pegawaiMap = computed(() => {
  const map = new Map<number, Pegawai>()
  pegawaiList.value.forEach((p) => map.set(p.id, p))
  return map
})

const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const NUM_FIELDS = [
  "gaji_pokok", "tunjangan_jabatan", "tunjangan_pengabdian", "transport",
  "bonus_insentif", "thr", "potongan_pinjaman", "potongan_asuransi",
] as const

type NumField = (typeof NUM_FIELDS)[number]

async function load() {
  loading.value = true
  try {
    rows.value = (await gajiApi.list()).results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data gaji.")
  } finally {
    loading.value = false
  }
}

// --- form ---
const dialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<Record<NumField, number> & { pegawai?: number; periode_bulan: number; periode_tahun: number }>({
  pegawai: undefined,
  periode_bulan: new Date().getMonth() + 1,
  periode_tahun: new Date().getFullYear(),
  gaji_pokok: 0,
  tunjangan_jabatan: 0,
  tunjangan_pengabdian: 0,
  transport: 0,
  bonus_insentif: 0,
  thr: 0,
  potongan_pinjaman: 0,
  potongan_asuransi: 0,
})

const brutoPreview = computed(() =>
  form.gaji_pokok + form.tunjangan_jabatan + form.tunjangan_pengabdian
    + form.transport + form.bonus_insentif + form.thr,
)
const potonganPreview = computed(() => form.potongan_pinjaman + form.potongan_asuransi)
const nettoPreview = computed(() => brutoPreview.value - potonganPreview.value)

function openCreate() {
  editingId.value = null
  const now = new Date()
  Object.assign(form, {
    pegawai: undefined,
    periode_bulan: now.getMonth() + 1,
    periode_tahun: now.getFullYear(),
    gaji_pokok: 0, tunjangan_jabatan: 0, tunjangan_pengabdian: 0,
    transport: 0, bonus_insentif: 0, thr: 0,
    potongan_pinjaman: 0, potongan_asuransi: 0,
  })
  dialog.value = true
}

function openEdit(g: Gaji) {
  editingId.value = g.id
  form.pegawai = g.pegawai
  form.periode_bulan = g.periode_bulan
  form.periode_tahun = g.periode_tahun
  for (const k of NUM_FIELDS) {
    form[k] = Number(g[k])
  }
  dialog.value = true
}

async function save() {
  if (!form.pegawai) return
  saving.value = true
  try {
    const payload: Partial<Gaji> = {
      pegawai: form.pegawai,
      periode_bulan: form.periode_bulan,
      periode_tahun: form.periode_tahun,
    }
    for (const k of NUM_FIELDS) {
      payload[k] = String(form[k])
    }
    if (editingId.value) {
      await gajiApi.update(editingId.value, payload)
      notifySuccess(toast, "Slip gaji diperbarui")
    } else {
      await gajiApi.create(payload)
      notifySuccess(toast, "Data gaji disimpan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan data gaji.")
  } finally {
    saving.value = false
  }
}

function confirmDelete(g: Gaji) {
  confirm.require({
    message: "Hapus slip gaji ini? Hanya slip yang belum dijurnal.",
    header: "Konfirmasi Hapus",
    icon: "pi pi-trash",
    rejectLabel: "Batal",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await gajiApi.remove(g.id)
        notifySuccess(toast, "Slip gaji dihapus.")
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus slip gaji.")
      }
    },
  })
}

watch(() => form.pegawai, (pid) => {
  if (!pid || editingId.value) return
  const loans = pinjamanList.value.filter(
    (p) => p.pegawai === pid && Number(p.sisa_pinjaman) > 0,
  )
  form.potongan_pinjaman = loans.reduce((s, p) => s + Number(p.angsuran_per_bulan), 0)
})

async function posting(g: Gaji) {
  try {
    const res = await gajiApi.posting(g.id)
    notifySuccess(toast, "Payroll diposting", res)
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal memposting gaji.")
  }
}

// --- slip ---
const slipDialog = ref(false)
const slip = ref<Gaji | null>(null)

async function lihatSlip(g: Gaji) {
  try {
    slip.value = await gajiApi.get(g.id)
    slipDialog.value = true
  } catch (e) {
    notifyError(toast, e, "Gagal memuat slip gaji.")
  }
}

function cetak() {
  window.print()
}

onMounted(async () => {
  await load()
  try {
    const [pegawai, pinjaman] = await Promise.all([
      pegawaiApi.listAll(),
      pinjamanApi.list(),
    ])
    pegawaiList.value = pegawai
    pinjamanList.value = pinjaman.results
  } catch (e) {
    notifyError(toast, e, "Gagal memuat daftar pegawai atau pinjaman.")
  }
})
</script>

<template>
  <PageLayout title="Penggajian" subtitle="Buat slip gaji lengkap dan posting ke jurnal">
    <template #actions>
      <Button v-if="canWrite" label="Buat Slip Gaji" icon="pi pi-plus" @click="openCreate" />
    </template>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada data gaji.</template>
      <Column header="Pegawai">
        <template #body="{ data }">{{ pegawaiMap.get(data.pegawai)?.nama ?? `#${data.pegawai}` }}</template>
      </Column>
      <Column header="Periode">
        <template #body="{ data }">{{ BULAN[data.periode_bulan - 1] }} {{ data.periode_tahun }}</template>
      </Column>
      <Column header="Bruto"><template #body="{ data }">{{ formatRp(data.total_bruto) }}</template></Column>
      <Column header="Netto"><template #body="{ data }">{{ formatRp(data.total_netto) }}</template></Column>
      <Column header="Status Jurnal">
        <template #body="{ data }">
          <Tag
            :value="data.jurnal ? 'Sudah dijurnal' : 'Belum dijurnal'"
            :severity="data.jurnal ? 'success' : 'warn'"
          />
        </template>
      </Column>
      <Column header="Aksi" headerClass="bee-col-actions--lg" bodyClass="bee-col-actions--lg">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button label="Slip" size="small" text @click="lihatSlip(data)" />
            <Button
              v-if="canWrite && !data.jurnal"
              icon="pi pi-pencil"
              text
              rounded
              aria-label="Edit slip"
              @click="openEdit(data)"
            />
            <Button
              v-if="canWrite && !data.jurnal"
              label="Posting"
              size="small"
              text
              @click="posting(data)"
            />
            <Button
              v-if="canWrite && !data.jurnal"
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              aria-label="Hapus slip"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialog"
      :header="editingId ? 'Edit Slip Gaji' : 'Buat Slip Gaji'"
      modal
      :style="{ width: '40rem' }"
    >
      <div class="form-grid">
        <div class="field span2">
          <label>Pegawai *</label>
          <Select
            v-model="form.pegawai"
            :options="pegawaiList.filter((p) => p.status_aktif)"
            option-label="nama"
            option-value="id"
            filter
            placeholder="Pilih pegawai"
            :disabled="!!editingId"
            fluid
          />
        </div>
        <div class="field">
          <label>Bulan</label>
          <Select
            v-model="form.periode_bulan"
            :options="BULAN.map((b, i) => ({ label: b, value: i + 1 }))"
            option-label="label"
            option-value="value"
            fluid
          />
        </div>
        <div class="field">
          <label>Tahun</label>
          <InputNumber v-model="form.periode_tahun" :min="2020" :max="2100" :use-grouping="false" fluid />
        </div>

        <div class="section span2">Pendapatan</div>
        <div class="field"><label>Gaji Pokok</label><InputNumber v-model="form.gaji_pokok" :min="0" fluid /></div>
        <div class="field"><label>Tunjangan Jabatan</label><InputNumber v-model="form.tunjangan_jabatan" :min="0" fluid /></div>
        <div class="field"><label>Tunjangan Pengabdian</label><InputNumber v-model="form.tunjangan_pengabdian" :min="0" fluid /></div>
        <div class="field"><label>Transport / Uang Makan</label><InputNumber v-model="form.transport" :min="0" fluid /></div>
        <div class="field"><label>Bonus / Insentif</label><InputNumber v-model="form.bonus_insentif" :min="0" fluid /></div>
        <div class="field"><label>THR</label><InputNumber v-model="form.thr" :min="0" fluid /></div>

        <div class="section span2">Potongan</div>
        <div class="field"><label>Potongan Pinjaman (Kasbon)</label><InputNumber v-model="form.potongan_pinjaman" :min="0" fluid /></div>
        <div class="field"><label>Potongan Asuransi</label><InputNumber v-model="form.potongan_asuransi" :min="0" fluid /></div>
      </div>

      <div class="totals">
        <div><span>Bruto</span><strong>{{ formatRp(brutoPreview) }}</strong></div>
        <div><span>Potongan</span><strong>{{ formatRp(potonganPreview) }}</strong></div>
        <div class="net"><span>Netto</span><strong>{{ formatRp(nettoPreview) }}</strong></div>
      </div>

      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Simpan" :disabled="!form.pegawai" :loading="saving" @click="save" />
      </template>
    </Dialog>

    <Dialog v-model:visible="slipDialog" header="Slip Gaji" modal :style="{ width: '32rem' }" class="slip-dialog">
      <GajiSlipPreview
        v-if="slip"
        :slip="slip"
        :pegawai="pegawaiMap.get(slip.pegawai) ?? null"
        :bulan-label="BULAN[slip.periode_bulan - 1]"
      />
      <template #footer>
        <Button label="Tutup" severity="secondary" text @click="slipDialog = false" />
        <Button label="Cetak" icon="pi pi-print" @click="cetak" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field label { font-weight: 600; font-size: 0.85rem; }
.section {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--app-text-muted); font-weight: 700; margin-top: 0.25rem;
}
.totals {
  margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--app-border);
  display: grid; gap: 0.35rem;
}
.totals div { display: flex; justify-content: space-between; }
.totals .net strong { color: #2e9e5b; font-size: 1.05rem; }
</style>

<style>
@media print {
  .slip-dialog .p-dialog-header,
  .slip-dialog .p-dialog-footer { display: none !important; }
  .slip-dialog .p-dialog { width: 100% !important; box-shadow: none !important; }
}
</style>
