<script setup lang="ts">
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import BeePaginator from "@/shared/components/BeePaginator.vue"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import Tabs from "primevue/tabs"
import Tag from "primevue/tag"
import ToggleSwitch from "primevue/toggleswitch"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue"

import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { useAuthStore } from "@/stores/auth"
import type { Coa, Golongan, SubGolongan } from "@/types/api"
import { coaManageApi } from "./api"
import "./coa.css"

type Kind = "akun" | "sub" | "golongan"
const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()
const canWrite = computed(() => auth.hasRole(["Finance"]))
const tab = ref<Kind>("akun")
const loading = ref(false)
const error = ref("")
const golongan = ref<Golongan[]>([])
const subGolongan = ref<SubGolongan[]>([])
const akun = ref<Coa[]>([])
const search = ref("")
const active = ref<"all" | "active" | "inactive">("all")
const parent = ref<string | number | null>(null)
const first = ref(0)

const golonganMap = computed(() => new Map(golongan.value.map((row) => [row.id, row])))
const subMap = computed(() => new Map(subGolongan.value.map((row) => [row.kode_sub, row])))
const subOptions = computed(() => subGolongan.value.map((row) => ({
  label: `${row.kode_sub} · ${row.nama_sub}`, value: row.kode_sub,
})))
const golOptions = computed(() => golongan.value.map((row) => ({
  label: `${row.kode_golongan} · ${row.nama_golongan}`, value: row.id,
})))
function parentName(row: Coa) {
  const sub = row.sub_golongan ? subMap.value.get(row.sub_golongan) : undefined
  const group = sub ? golonganMap.value.get(sub.golongan) : undefined
  return [group?.nama_golongan, sub?.nama_sub].filter(Boolean).join(" / ") || "Belum dikelompokkan"
}
function cents(value: string): bigint | null {
  const parts = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(value)
  if (!parts) return null
  const amount = BigInt(parts[2]!) * 100n + BigInt((parts[3] || "").padEnd(2, "0"))
  return parts[1] ? -amount : amount
}
function rupiah(value: bigint) {
  const amount = value < 0n ? -value : value
  return `Rp ${value < 0n ? "−" : ""}${(amount / 100n).toLocaleString("id-ID")}${amount % 100n ? `,${String(amount % 100n).padStart(2, "0")}` : ""}`
}
function saldoLabel(row: Coa) {
  const amount = cents(row.saldo_awal)
  return amount === null ? "Periksa nominal" : rupiah(amount)
}
function dateLabel(value: string | null) {
  return value ? value.split("-").reverse().join("/") : "Tanggal belum diisi"
}

const balance = computed(() => {
  let debit = 0n, kredit = 0n, invalid = 0, missingDate = 0
  for (const row of akun.value) {
    const amount = cents(row.saldo_awal)
    if (amount === null) { invalid++; continue }
    if (amount !== 0n && !row.tanggal_saldo_awal) missingDate++
    if (row.posisi_normal === "D") debit += amount
    else kredit += amount
  }
  return { debit, kredit, difference: debit - kredit, invalid, missingDate }
})
const filtered = computed(() => {
  const term = search.value.trim().toLocaleLowerCase("id-ID")
  if (tab.value === "akun") return akun.value.filter((row) =>
    (active.value === "all" || row.is_active === (active.value === "active"))
    && (!parent.value || row.sub_golongan === parent.value)
    && (!term || [row.kode_akun, row.nama_akun, parentName(row)].some((text) => text.toLocaleLowerCase("id-ID").includes(term))),
  )
  if (tab.value === "sub") return subGolongan.value.filter((row) =>
    (!parent.value || row.golongan === parent.value)
    && (!term || [row.kode_sub, row.nama_sub, golonganMap.value.get(row.golongan)?.nama_golongan || ""].some((text) => text.toLocaleLowerCase("id-ID").includes(term))),
  )
  return golongan.value.filter((row) =>
    !term || [row.kode_golongan, row.nama_golongan, row.deskripsi || ""].some((text) => text.toLocaleLowerCase("id-ID").includes(term)),
  )
})
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 15))
const hasFilter = computed(() => !!search.value.trim() || active.value !== "all" || !!parent.value)
watch([tab, search, active, parent], () => { first.value = 0 })
watch(tab, () => { search.value = ""; active.value = "all"; parent.value = null })
function clearFilters() { search.value = ""; active.value = "all"; parent.value = null }

async function loadAll() {
  if (loading.value) return
  loading.value = true
  error.value = ""
  try {
    const [g, s, a] = await Promise.all([
      coaManageApi.listGolongan(), coaManageApi.listSubGolongan(), coaManageApi.listCoa(),
    ])
    golongan.value = g.sort((x, y) => x.kode_golongan.localeCompare(y.kode_golongan))
    subGolongan.value = s.sort((x, y) => x.kode_sub.localeCompare(y.kode_sub))
    akun.value = a.sort((x, y) => x.kode_akun.localeCompare(y.kode_akun))
  } catch (cause) {
    golongan.value = []; subGolongan.value = []; akun.value = []
    const message = friendlyError(cause, "Daftar akun belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  } finally { loading.value = false }
}

const dialog = ref(false)
const dialogKind = ref<Kind>("akun")
const saving = ref(false)
const attempted = ref(false)
const editingKey = ref<string | number | null>(null)
const formError = ref("")
const formGolongan = reactive({ kode_golongan: "", nama_golongan: "", deskripsi: "" })
const formSub = reactive({ golongan: null as number | null, kode_sub: "", nama_sub: "" })
const formAkun = reactive({
  kode_akun: "", sub_golongan: null as string | null, nama_akun: "",
  posisi_normal: "D" as "D" | "K", is_active: true,
  saldo_awal: 0 as number | null, tanggal_saldo_awal: "",
})
const posisiOptions = [{ label: "Debit (D)", value: "D" }, { label: "Kredit (K)", value: "K" }]
const dialogTitle = computed(() => `${editingKey.value ? "Ubah" : "Tambah"} ${dialogKind.value === "akun" ? "akun" : dialogKind.value === "sub" ? "subgolongan" : "golongan"}`)

function openCreate(kind: Kind) {
  dialogKind.value = kind; editingKey.value = null; formError.value = ""; attempted.value = false
  Object.assign(formGolongan, { kode_golongan: "", nama_golongan: "", deskripsi: "" })
  Object.assign(formSub, { golongan: null, kode_sub: "", nama_sub: "" })
  Object.assign(formAkun, { kode_akun: "", sub_golongan: null, nama_akun: "", posisi_normal: "D", is_active: true, saldo_awal: 0, tanggal_saldo_awal: "" })
  dialog.value = true
}
function openEditGolongan(row: Golongan) {
  dialogKind.value = "golongan"; editingKey.value = row.id; formError.value = ""; attempted.value = false
  Object.assign(formGolongan, { kode_golongan: row.kode_golongan, nama_golongan: row.nama_golongan, deskripsi: row.deskripsi ?? "" })
  dialog.value = true
}
function openEditSub(row: SubGolongan) {
  dialogKind.value = "sub"; editingKey.value = row.id; formError.value = ""; attempted.value = false
  Object.assign(formSub, { golongan: row.golongan, kode_sub: row.kode_sub, nama_sub: row.nama_sub })
  dialog.value = true
}
function openEditAkun(row: Coa) {
  dialogKind.value = "akun"; editingKey.value = row.kode_akun; formError.value = ""; attempted.value = false
  Object.assign(formAkun, { ...row, saldo_awal: Number(row.saldo_awal), tanggal_saldo_awal: row.tanggal_saldo_awal ?? "" })
  dialog.value = true
}
async function save() {
  if (saving.value || !canWrite.value) return
  attempted.value = true
  formError.value = ""
  if (dialogKind.value === "golongan") {
    if (!formGolongan.kode_golongan.trim() || !formGolongan.nama_golongan.trim()) formError.value = "Isi kode dan nama golongan."
    else if (formGolongan.kode_golongan.length > 5 || formGolongan.nama_golongan.length > 50) formError.value = "Kode maksimal 5 karakter dan nama maksimal 50 karakter."
  } else if (dialogKind.value === "sub") {
    if (!formSub.golongan || !formSub.kode_sub.trim() || !formSub.nama_sub.trim()) formError.value = "Pilih golongan, lalu isi kode dan nama subgolongan."
    else if (formSub.kode_sub.length > 10 || formSub.nama_sub.length > 100) formError.value = "Kode maksimal 10 karakter dan nama maksimal 100 karakter."
  } else {
    if (!formAkun.kode_akun.trim() || !formAkun.nama_akun.trim()) formError.value = "Isi kode dan nama akun."
    else if (formAkun.kode_akun.length > 20 || formAkun.nama_akun.length > 255) formError.value = "Kode maksimal 20 karakter dan nama maksimal 255 karakter."
    else if (formAkun.saldo_awal === null || !Number.isFinite(formAkun.saldo_awal) || !Number.isSafeInteger(Math.round(formAkun.saldo_awal * 100))) formError.value = "Isi saldo awal dengan nominal yang dapat dihitung tepat sampai dua desimal."
    else if (formAkun.saldo_awal !== 0 && !formAkun.tanggal_saldo_awal) formError.value = "Isi tanggal acuan untuk saldo awal bukan nol."
  }
  if (formError.value) {
    await nextTick()
    document.querySelector<HTMLElement>('.coa-dialog input[aria-invalid="true"], .coa-dialog [role="combobox"][aria-invalid="true"]')?.focus()
    return
  }
  saving.value = true
  try {
    if (dialogKind.value === "golongan") {
      const payload = { kode_golongan: formGolongan.kode_golongan.trim(), nama_golongan: formGolongan.nama_golongan.trim(), deskripsi: formGolongan.deskripsi.trim() || null }
      if (editingKey.value !== null) await coaManageApi.updateGolongan(editingKey.value as number, payload)
      else await coaManageApi.createGolongan(payload)
    } else if (dialogKind.value === "sub") {
      const payload = { golongan: formSub.golongan!, kode_sub: formSub.kode_sub.trim(), nama_sub: formSub.nama_sub.trim() }
      if (editingKey.value !== null) await coaManageApi.updateSubGolongan(editingKey.value as number, payload)
      else await coaManageApi.createSubGolongan(payload)
    } else {
      const payload = { kode_akun: formAkun.kode_akun.trim(), sub_golongan: formAkun.sub_golongan, nama_akun: formAkun.nama_akun.trim(), posisi_normal: formAkun.posisi_normal, is_active: formAkun.is_active, saldo_awal: formAkun.saldo_awal!.toFixed(2), tanggal_saldo_awal: formAkun.tanggal_saldo_awal || null }
      if (editingKey.value !== null) await coaManageApi.updateCoa(editingKey.value as string, payload)
      else await coaManageApi.createCoa(payload)
    }
    dialog.value = false
    notifySuccess(toast, editingKey.value !== null ? "Perubahan disimpan" : "Data ditambahkan")
    await loadAll()
  } catch (cause) { notifyError(toast, cause, "Belum dapat memastikan perubahan tersimpan. Periksa daftar sebelum mencoba lagi.") }
  finally { saving.value = false }
}
function confirmRemove(kind: Kind, key: string | number, label: string) {
  const dependent = kind === "golongan"
    ? subGolongan.value.filter((row) => row.golongan === key).length
    : kind === "sub" ? akun.value.filter((row) => row.sub_golongan === subGolongan.value.find((sub) => sub.id === key)?.kode_sub).length : 0
  const title = kind === "akun" ? "akun" : kind === "sub" ? "subgolongan" : "golongan"
  if (kind === "akun" && cents(akun.value.find((row) => row.kode_akun === key)?.saldo_awal ?? "0") !== 0n) {
    toast.add({ severity: "warn", summary: "Belum bisa dihapus", detail: `${label} memiliki saldo awal. Kosongkan saldo awal atau nonaktifkan akun bila riwayat perlu dipertahankan.`, life: 6000 })
    return
  }
  if (dependent) {
    toast.add({ severity: "warn", summary: "Belum bisa dihapus", detail: `${label} masih memiliki ${dependent} ${kind === "golongan" ? "subgolongan" : "akun"}. Pindahkan atau hapus data tersebut lebih dulu.`, life: 6000 })
    return
  }
  confirm.require({
    header: `Hapus ${title}?`,
    message: `Hapus ${label}? ${kind === "akun" ? "Akun yang sudah digunakan di jurnal atau memiliki saldo awal tidak dapat dihapus." : "Perubahan ini tidak dapat dibatalkan."}`,
    rejectLabel: "Batal", acceptLabel: "Hapus", acceptClass: "p-button-danger",
    accept: async () => {
      try {
        if (kind === "golongan") await coaManageApi.removeGolongan(key as number)
        else if (kind === "sub") await coaManageApi.removeSubGolongan(key as number)
        else await coaManageApi.removeCoa(key as string)
        notifySuccess(toast, `${label} dihapus`)
        await loadAll()
      } catch (cause) { notifyError(toast, cause, "Data belum dihapus.") }
    },
  })
}
async function showSub(row: Golongan) { tab.value = "sub"; await nextTick(); parent.value = row.id }
async function showAccounts(row: SubGolongan) { tab.value = "akun"; await nextTick(); parent.value = row.kode_sub }
onMounted(loadAll)
</script>

<template>
  <PageLayout title="Daftar akun" subtitle="Susunan golongan, subgolongan, dan akun untuk pencatatan sekolah." :surface="false">
    <div class="coa-intro"><Icon name="tree-structure" /><p>Golongan <span>→</span> subgolongan <span>→</span> akun. Pilih tingkatnya untuk melihat atau mengubah susunan.</p></div>
    <section class="coa-panel" aria-label="Daftar akun akuntansi" :aria-busy="loading">
      <header class="coa-heading">
        <div><h2>Struktur akun</h2><p>{{ canWrite ? "Perubahan di sini memengaruhi pilihan akun pada pencatatan berikutnya." : "Daftar ini dapat dilihat. Perubahan dilakukan oleh Staf Keuangan." }}</p></div>
        <Button label="Muat ulang" severity="secondary" :disabled="loading" :loading="loading" @click="loadAll"><template #icon><Icon name="arrows-clockwise" /></template></Button>
      </header>
      <Tabs v-model:value="tab" class="coa-tabs">
        <TabList><Tab value="akun">Akun <span>{{ error || loading ? "—" : akun.length }}</span></Tab><Tab value="sub">Subgolongan <span>{{ error || loading ? "—" : subGolongan.length }}</span></Tab><Tab value="golongan">Golongan <span>{{ error || loading ? "—" : golongan.length }}</span></Tab></TabList>
      </Tabs>
      <div :key="tab" class="bee-subpage">
      <div v-if="tab === 'akun' && !error && !loading" class="coa-balance" aria-label="Ringkasan saldo awal">
        <div><span>Saldo awal debit</span><strong>{{ balance.invalid ? '—' : rupiah(balance.debit) }}</strong></div>
        <div><span>Saldo awal kredit</span><strong>{{ balance.invalid ? '—' : rupiah(balance.kredit) }}</strong></div>
        <div :class="{ 'coa-balance-alert': balance.difference !== 0n }"><span>Selisih debit − kredit</span><strong>{{ balance.invalid ? '—' : rupiah(balance.difference) }}</strong></div>
      </div>
      <p v-if="tab === 'akun' && !error && !loading" class="coa-balance-scope">Ringkasan seluruh akun tanpa memisahkan tanggal acuan. Periksa laporan untuk saldo per periode.</p>
      <Message v-if="tab === 'akun' && !error && !loading && (balance.difference !== 0n || balance.invalid || balance.missingDate)" severity="warn" :closable="false" class="coa-warning"><template #icon><Icon name="warning-circle" /></template>
        <span v-if="balance.difference !== 0n && !balance.invalid">Saldo awal seluruh akun belum seimbang. Selisih {{ rupiah(balance.difference < 0n ? -balance.difference : balance.difference) }}. Periksa saldo awal sebelum memakai laporan sebagai angka final. </span>
        <span v-if="balance.invalid">{{ balance.invalid }} nominal belum dapat dibaca. </span><span v-if="balance.missingDate">{{ balance.missingDate }} akun bersaldo belum memiliki tanggal acuan.</span>
      </Message>
      <div class="coa-toolbar">
        <div class="coa-field coa-search"><label for="coa-search">Cari {{ tab === 'akun' ? 'akun' : tab === 'sub' ? 'subgolongan' : 'golongan' }}</label><SearchField input-id="coa-search" v-model="search" :placeholder="tab === 'akun' ? 'Kode, nama, atau kelompok' : 'Kode atau nama'" hint="Mencari seluruh data yang telah dimuat" /></div>
        <div v-if="tab === 'akun'" class="coa-field"><label for="coa-active">Status akun</label><Select input-id="coa-active" v-model="active" :options="[{ label: 'Semua status', value: 'all' }, { label: 'Aktif', value: 'active' }, { label: 'Nonaktif', value: 'inactive' }]" option-label="label" option-value="value" :disabled="loading || !!error" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div v-if="tab !== 'golongan'" class="coa-field"><label for="coa-parent">{{ tab === 'akun' ? 'Subgolongan' : 'Golongan' }}</label><Select input-id="coa-parent" v-model="parent" :options="tab === 'akun' ? subOptions : golOptions" option-label="label" option-value="value" :placeholder="tab === 'akun' ? 'Semua subgolongan' : 'Semua golongan'" show-clear filter :disabled="loading || !!error" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
        <Button v-if="canWrite" :label="tab === 'akun' ? 'Tambah akun' : tab === 'sub' ? 'Tambah subgolongan' : 'Tambah golongan'" class="coa-add" :disabled="loading || !!error || (tab === 'sub' && !golongan.length)" @click="openCreate(tab)"><template #icon><Icon name="plus" /></template></Button>
      </div>
      <div v-if="tab === 'akun' && canWrite && !loading && !error && !subGolongan.length" class="coa-note"><Icon name="info" />Belum ada subgolongan. Buat golongan dan subgolongan agar akun baru dapat dikelompokkan.</div>
      <div v-if="error" class="coa-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang" severity="secondary" @click="loadAll" /></div>
      <div class="coa-results"><p role="status">{{ loading ? 'Memuat struktur akun…' : error ? 'Daftar belum tersedia' : filtered.length ? `${first + 1}–${Math.min(first + 15, filtered.length)} dari ${filtered.length} ${tab === 'akun' ? 'akun' : tab === 'sub' ? 'subgolongan' : 'golongan'}` : 'Tidak ada data ditampilkan' }}</p><Button v-if="hasFilter" label="Hapus filter" text severity="secondary" @click="clearFilters" /></div>
      <div v-if="loading" class="coa-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan struktur akun</p></div>
      <div v-else-if="!error && !filtered.length" class="coa-empty"><Icon :name="hasFilter ? 'magnifying-glass' : 'tree-structure'" /><h3>{{ hasFilter ? 'Tidak ada data yang cocok' : 'Belum ada data pada tingkat ini' }}</h3><p>{{ hasFilter ? 'Ubah pencarian atau filter untuk melihat data lain.' : canWrite ? 'Gunakan tombol Tambah untuk mulai menyusun akun.' : 'Minta Staf Keuangan memeriksa daftar akun.' }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" @click="clearFilters" /></div>
      <template v-else-if="!error">
        <table class="coa-table"><caption class="coa-sr-only">{{ tab === 'akun' ? 'Daftar akun' : tab === 'sub' ? 'Daftar subgolongan' : 'Daftar golongan' }}</caption><thead><tr v-if="tab === 'akun'"><th>Kode dan nama akun</th><th>Pengelompokan</th><th>Posisi normal</th><th>Aktif</th><th class="coa-number">Saldo Awal</th><th v-if="canWrite" class="coa-actions">Aksi</th></tr><tr v-else-if="tab === 'sub'"><th>Kode dan nama subgolongan</th><th>Golongan</th><th>Jumlah akun</th><th v-if="canWrite" class="coa-actions">Aksi</th></tr><tr v-else><th>Kode dan nama golongan</th><th>Deskripsi</th><th>Jumlah subgolongan</th><th v-if="canWrite" class="coa-actions">Aksi</th></tr></thead>
          <tbody v-if="tab === 'akun'"><tr v-for="row in pageRows as Coa[]" :key="row.kode_akun"><td><strong>{{ row.nama_akun }}</strong><small class="coa-code">{{ row.kode_akun }}</small></td><td>{{ parentName(row) }}</td><td>{{ row.posisi_normal === 'D' ? 'Debit' : 'Kredit' }}</td><td><Tag :value="row.is_active ? 'Aktif' : 'Nonaktif'" :severity="row.is_active ? 'success' : 'secondary'" /></td><td class="coa-number"><strong>{{ saldoLabel(row) }}</strong><small>{{ cents(row.saldo_awal) === 0n ? 'Tanpa saldo awal' : dateLabel(row.tanggal_saldo_awal) }}</small></td><td v-if="canWrite" class="coa-actions"><Button label="Ubah" severity="secondary" text aria-label="Edit akun" @click="openEditAkun(row)" /><Button label="Hapus" severity="danger" text :aria-label="`Hapus akun ${row.nama_akun}`" @click="confirmRemove('akun', row.kode_akun, row.nama_akun)" /></td></tr></tbody>
          <tbody v-else-if="tab === 'sub'"><tr v-for="row in pageRows as SubGolongan[]" :key="row.id"><td><strong>{{ row.nama_sub }}</strong><small class="coa-code">{{ row.kode_sub }}</small></td><td>{{ golonganMap.get(row.golongan)?.nama_golongan ?? 'Golongan tidak ditemukan' }}</td><td><Button :label="`${akun.filter((a) => a.sub_golongan === row.kode_sub).length} akun`" text severity="secondary" @click="showAccounts(row)" /></td><td v-if="canWrite" class="coa-actions"><Button label="Ubah" severity="secondary" text @click="openEditSub(row)" /><Button label="Hapus" severity="danger" text @click="confirmRemove('sub', row.id, row.nama_sub)" /></td></tr></tbody>
          <tbody v-else><tr v-for="row in pageRows as Golongan[]" :key="row.id"><td><strong>{{ row.nama_golongan }}</strong><small class="coa-code">{{ row.kode_golongan }}</small></td><td>{{ row.deskripsi || '—' }}</td><td><Button :label="`${subGolongan.filter((sub) => sub.golongan === row.id).length} subgolongan`" text severity="secondary" @click="showSub(row)" /></td><td v-if="canWrite" class="coa-actions"><Button label="Ubah" severity="secondary" text @click="openEditGolongan(row)" /><Button label="Hapus" severity="danger" text @click="confirmRemove('golongan', row.id, row.nama_golongan)" /></td></tr></tbody></table>
        <ul class="coa-cards"><li v-for="row in pageRows" :key="tab === 'akun' ? (row as Coa).kode_akun : (row as SubGolongan).id"><template v-if="tab === 'akun'"><div class="coa-card-title"><span>{{ (row as Coa).kode_akun }}</span><Tag :value="(row as Coa).is_active ? 'Aktif' : 'Nonaktif'" :severity="(row as Coa).is_active ? 'success' : 'secondary'" /></div><h3>{{ (row as Coa).nama_akun }}</h3><p>{{ parentName(row as Coa) }}</p><dl><div><dt>Posisi normal</dt><dd>{{ (row as Coa).posisi_normal === 'D' ? 'Debit' : 'Kredit' }}</dd></div><div><dt>Saldo awal</dt><dd>{{ saldoLabel(row as Coa) }}<small>{{ cents((row as Coa).saldo_awal) === 0n ? 'Tanpa saldo awal' : dateLabel((row as Coa).tanggal_saldo_awal) }}</small></dd></div></dl><div v-if="canWrite" class="coa-card-actions"><Button label="Ubah" severity="secondary" @click="openEditAkun(row as Coa)" /><Button label="Hapus" text severity="danger" @click="confirmRemove('akun', (row as Coa).kode_akun, (row as Coa).nama_akun)" /></div></template>
          <template v-else-if="tab === 'sub'"><div class="coa-card-title"><span>{{ (row as SubGolongan).kode_sub }}</span></div><h3>{{ (row as SubGolongan).nama_sub }}</h3><p>{{ golonganMap.get((row as SubGolongan).golongan)?.nama_golongan ?? 'Golongan tidak ditemukan' }}</p><div class="coa-card-actions"><Button :label="`${akun.filter((a) => a.sub_golongan === (row as SubGolongan).kode_sub).length} akun`" text severity="secondary" @click="showAccounts(row as SubGolongan)" /><Button v-if="canWrite" label="Ubah" severity="secondary" @click="openEditSub(row as SubGolongan)" /><Button v-if="canWrite" label="Hapus" text severity="danger" @click="confirmRemove('sub', (row as SubGolongan).id, (row as SubGolongan).nama_sub)" /></div></template>
          <template v-else><div class="coa-card-title"><span>{{ (row as Golongan).kode_golongan }}</span></div><h3>{{ (row as Golongan).nama_golongan }}</h3><p>{{ (row as Golongan).deskripsi || 'Tanpa deskripsi' }}</p><div class="coa-card-actions"><Button :label="`${subGolongan.filter((sub) => sub.golongan === (row as Golongan).id).length} subgolongan`" text severity="secondary" @click="showSub(row as Golongan)" /><Button v-if="canWrite" label="Ubah" severity="secondary" @click="openEditGolongan(row as Golongan)" /><Button v-if="canWrite" label="Hapus" text severity="danger" @click="confirmRemove('golongan', (row as Golongan).id, (row as Golongan).nama_golongan)" /></div></template></li></ul>
        <BeePaginator v-if="filtered.length > 15" v-model:first="first" :rows="15" :total-records="filtered.length" />
      </template>
      </div>
    </section>

    <Dialog v-model:visible="dialog" :header="dialogTitle" modal class="coa-dialog" :closable="!saving" :dismissable-mask="!saving" :close-on-escape="!saving">
      <form id="coa-form" class="coa-form" @submit.prevent="save">
        <p class="coa-form-intro">{{ dialogKind === 'akun' ? 'Kode akun tetap setelah dibuat. Saldo awal mengikuti posisi normal akun.' : dialogKind === 'sub' ? 'Pilih golongan induk secara sengaja sebelum menyimpan.' : 'Golongan adalah tingkat paling atas dalam daftar akun.' }}</p>
        <template v-if="dialogKind === 'golongan'"><div class="coa-field"><label for="coa-code-gol">Kode golongan (wajib)</label><InputText id="coa-code-gol" v-model="formGolongan.kode_golongan" maxlength="5" :invalid="attempted && !formGolongan.kode_golongan.trim()" :aria-invalid="attempted && !formGolongan.kode_golongan.trim()" :aria-describedby="attempted && !formGolongan.kode_golongan.trim() ? 'coa-form-error' : undefined" :disabled="saving || editingKey !== null" fluid /></div><div class="coa-field"><label for="coa-name-gol">Nama golongan (wajib)</label><InputText id="coa-name-gol" v-model="formGolongan.nama_golongan" maxlength="50" :invalid="attempted && !formGolongan.nama_golongan.trim()" :aria-invalid="attempted && !formGolongan.nama_golongan.trim()" :aria-describedby="attempted && !formGolongan.nama_golongan.trim() ? 'coa-form-error' : undefined" :disabled="saving" fluid /></div><div class="coa-field"><label for="coa-desc-gol">Deskripsi</label><InputText id="coa-desc-gol" v-model="formGolongan.deskripsi" :disabled="saving" fluid /></div></template>
        <template v-else-if="dialogKind === 'sub'"><div class="coa-field"><label for="coa-parent-sub">Golongan induk (wajib)</label><Select input-id="coa-parent-sub" v-model="formSub.golongan" :options="golOptions" option-label="label" option-value="value" placeholder="Pilih golongan" :invalid="attempted && !formSub.golongan" :aria-invalid="attempted && !formSub.golongan" :pt="{ label: { 'aria-describedby': attempted && !formSub.golongan ? 'coa-form-error' : undefined } }" :disabled="saving" fluid /></div><div class="coa-field"><label for="coa-code-sub">Kode subgolongan (wajib)</label><InputText id="coa-code-sub" v-model="formSub.kode_sub" maxlength="10" :invalid="attempted && !formSub.kode_sub.trim()" :aria-invalid="attempted && !formSub.kode_sub.trim()" :aria-describedby="attempted && !formSub.kode_sub.trim() ? 'coa-form-error' : undefined" :disabled="saving || editingKey !== null" fluid /></div><div class="coa-field"><label for="coa-name-sub">Nama subgolongan (wajib)</label><InputText id="coa-name-sub" v-model="formSub.nama_sub" maxlength="100" :invalid="attempted && !formSub.nama_sub.trim()" :aria-invalid="attempted && !formSub.nama_sub.trim()" :aria-describedby="attempted && !formSub.nama_sub.trim() ? 'coa-form-error' : undefined" :disabled="saving" fluid /></div></template>
        <template v-else><div class="coa-field"><label for="coa-code-akun">Kode akun (wajib)</label><InputText id="coa-code-akun" v-model="formAkun.kode_akun" maxlength="20" :invalid="attempted && !formAkun.kode_akun.trim()" :aria-invalid="attempted && !formAkun.kode_akun.trim()" :aria-describedby="attempted && !formAkun.kode_akun.trim() ? 'coa-form-error' : undefined" :disabled="saving || editingKey !== null" fluid /></div><div class="coa-field"><label for="coa-parent-akun">Subgolongan</label><Select input-id="coa-parent-akun" v-model="formAkun.sub_golongan" :options="subOptions" option-label="label" option-value="value" placeholder="Belum dikelompokkan" show-clear filter :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div><div class="coa-field"><label for="coa-name-akun">Nama akun (wajib)</label><InputText id="coa-name-akun" v-model="formAkun.nama_akun" maxlength="255" :invalid="attempted && !formAkun.nama_akun.trim()" :aria-invalid="attempted && !formAkun.nama_akun.trim()" :aria-describedby="attempted && !formAkun.nama_akun.trim() ? 'coa-form-error' : undefined" :disabled="saving" fluid /></div><div class="coa-field"><label for="coa-position">Posisi normal</label><Select input-id="coa-position" v-model="formAkun.posisi_normal" :options="posisiOptions" option-label="label" option-value="value" :disabled="saving" fluid /></div><div class="coa-field coa-switch"><label for="coa-active-form">Akun aktif</label><ToggleSwitch input-id="coa-active-form" v-model="formAkun.is_active" :disabled="saving" /></div><div class="coa-field"><label for="akun-saldo-awal">Saldo awal</label><InputNumber input-id="akun-saldo-awal" v-model="formAkun.saldo_awal" mode="currency" currency="IDR" locale="id-ID" :min-fraction-digits="0" :max-fraction-digits="2" :invalid="attempted && formAkun.saldo_awal === null" :input-props="{ 'aria-invalid': attempted && formAkun.saldo_awal === null, 'aria-describedby': formAkun.saldo_awal === null && attempted ? 'saldo-awal-help coa-form-error' : 'saldo-awal-help' }" :disabled="saving" fluid /><small id="saldo-awal-help">Gunakan nilai minus jika saldo berlawanan dengan posisi normal.</small></div><div class="coa-field"><label for="akun-tanggal-saldo-awal">Tanggal saldo awal</label><InputText id="akun-tanggal-saldo-awal" v-model="formAkun.tanggal_saldo_awal" type="date" :invalid="attempted && formAkun.saldo_awal !== null && formAkun.saldo_awal !== 0 && !formAkun.tanggal_saldo_awal" :aria-invalid="attempted && formAkun.saldo_awal !== null && formAkun.saldo_awal !== 0 && !formAkun.tanggal_saldo_awal" :aria-describedby="attempted && formAkun.saldo_awal !== null && formAkun.saldo_awal !== 0 && !formAkun.tanggal_saldo_awal ? 'tanggal-saldo-help coa-form-error' : 'tanggal-saldo-help'" :disabled="saving" fluid /><small id="tanggal-saldo-help">Saldo pada awal tanggal ini, sebelum transaksi hari tersebut. Wajib jika saldo bukan nol.</small></div></template>
        <Message v-if="formError" id="coa-form-error" severity="error" :closable="false" role="alert">{{ formError }}</Message>
      </form>
      <template #footer><Button label="Batal" severity="secondary" text :disabled="saving" @click="dialog = false" /><Button v-if="canWrite" type="submit" form="coa-form" label="Simpan" :loading="saving" :disabled="saving" /></template>
    </Dialog>
  </PageLayout>
</template>
