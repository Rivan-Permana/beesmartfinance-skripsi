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
import { computed, onMounted, reactive, ref } from "vue"

import { tagihanApi } from "./api"
import { notifyError } from "@/core/errors"
import { siswaApi } from "@/features/siswa/api"
import type { Siswa, StrukTagihan, Tagihan, TagihanStatus } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const rows = ref<Tagihan[]>([])
const siswaList = ref<Siswa[]>([])
const loading = ref(false)

const siswaNama = computed(() => {
  const map = new Map<number, string>()
  siswaList.value.forEach((s) => map.set(s.id, s.nama))
  return map
})

const statusSeverity: Record<TagihanStatus, string> = {
  BELUM: "warn",
  SEBAGIAN: "info",
  LUNAS: "success",
}
const BULAN = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

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

// --- generate dialog ---
const dialog = ref(false)
const saving = ref(false)
const form = reactive<{
  siswa: number | null
  periode_bulan: number
  periode_tahun: number
  tarif_katering: number
}>({
  siswa: null,
  periode_bulan: new Date().getMonth() + 1,
  periode_tahun: new Date().getFullYear(),
  tarif_katering: 0,
})

function openGenerate() {
  form.siswa = null
  form.periode_bulan = new Date().getMonth() + 1
  form.periode_tahun = new Date().getFullYear()
  form.tarif_katering = 0
  dialog.value = true
}

async function generate() {
  if (!form.siswa) return
  saving.value = true
  try {
    await tagihanApi.generate({
      siswa: form.siswa,
      periode_bulan: form.periode_bulan,
      periode_tahun: form.periode_tahun,
      tarif_katering: form.tarif_katering || 0,
    })
    toast.add({ severity: "success", summary: "Tagihan dibuat", life: 2500 })
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Gagal membuat tagihan.")
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
        await tagihanApi.bayar(t.id)
        toast.add({ severity: "success", summary: "Pembayaran tercatat (jurnal DRAFT dibuat)", life: 3000 })
        await load()
      } catch (e) {
        notifyError(toast, e, "Gagal mencatat pembayaran.")
      }
    },
  })
}

// --- struk ---
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
function rp(v: string | number) {
  return "Rp " + Number(v).toLocaleString("id-ID")
}
function cetak() {
  window.print()
}

onMounted(async () => {
  await load()
  try {
    siswaList.value = (await siswaApi.list()).results
  } catch {
    /* select siswa kosong jika gagal */
  }
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>Tagihan Siswa</h1>
      <Button label="Buat Tagihan" icon="pi pi-plus" @click="openGenerate" />
    </div>

    <DataTable :value="rows" :loading="loading" paginator :rows="10" data-key="id" striped-rows>
      <template #empty>Belum ada tagihan.</template>
      <Column header="Siswa">
        <template #body="{ data }">{{ siswaNama.get(data.siswa) ?? `#${data.siswa}` }}</template>
      </Column>
      <Column header="Periode">
        <template #body="{ data }">{{ BULAN[data.periode_bulan - 1] }} {{ data.periode_tahun }}</template>
      </Column>
      <Column header="Total">
        <template #body="{ data }">{{ rp(data.total) }}</template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity[data.status as TagihanStatus]" />
        </template>
      </Column>
      <Column header="Aksi" style="width: 12rem">
        <template #body="{ data }">
          <Button
            v-if="data.status !== 'LUNAS'"
            label="Bayar"
            size="small"
            text
            @click="bayar(data)"
          />
          <Button label="Struk" size="small" text severity="secondary" @click="lihatStruk(data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Generate -->
    <Dialog v-model:visible="dialog" header="Buat Tagihan" modal :style="{ width: '30rem' }">
      <div class="form">
        <div class="field">
          <label>Siswa *</label>
          <Select
            v-model="form.siswa"
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
        </div>
        <div class="field">
          <label>Tarif Katering / hari (opsional)</label>
          <InputNumber v-model="form.tarif_katering" :min="0" fluid />
          <small>Dihitung dari jumlah hari ikut katering pada absensi.</small>
        </div>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text @click="dialog = false" />
        <Button label="Buat" :disabled="!form.siswa" :loading="saving" @click="generate" />
      </template>
    </Dialog>

    <!-- Struk -->
    <Dialog v-model:visible="strukDialog" header="Struk Tagihan" modal :style="{ width: '26rem' }">
      <div v-if="struk" class="struk">
        <div class="struk-head">
          <strong>🐝 Sekolah Lebah Madu</strong>
          <div>{{ struk.siswa }} · {{ struk.nis ?? "-" }}</div>
          <div>Periode {{ struk.periode }}</div>
        </div>
        <table class="struk-lines">
          <tr v-for="(r, i) in struk.rincian" :key="i">
            <td>{{ r.komponen }}</td>
            <td class="num">{{ rp(r.nominal) }}</td>
          </tr>
          <tr class="total">
            <td>Total</td>
            <td class="num">{{ rp(struk.total) }}</td>
          </tr>
        </table>
        <div class="struk-foot">
          <Tag :value="struk.status" :severity="statusSeverity[struk.status]" />
          <span v-if="struk.no_jurnal" class="muted">Jurnal: {{ struk.no_jurnal.slice(0, 8) }}…</span>
        </div>
      </div>
      <template #footer>
        <Button label="Cetak" icon="pi pi-print" @click="cetak" />
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
.field small {
  color: var(--app-text-muted);
}
.struk-head {
  text-align: center;
  margin-bottom: 0.75rem;
  line-height: 1.4;
}
.struk-lines {
  width: 100%;
  border-collapse: collapse;
}
.struk-lines td {
  padding: 0.35rem 0;
  border-bottom: 1px dashed var(--app-border);
}
.struk-lines .num {
  text-align: right;
}
.struk-lines .total td {
  font-weight: 800;
  border-bottom: none;
}
.struk-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
}
.muted {
  color: var(--app-text-muted);
  font-size: 0.8rem;
}
</style>
