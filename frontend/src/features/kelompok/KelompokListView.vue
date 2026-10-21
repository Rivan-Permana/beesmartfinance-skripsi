<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import MultiSelect from "primevue/multiselect"
import Paginator from "primevue/paginator"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"

import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { jenjangApi, kelompokApi } from "@/features/absensi/api"
import { siswaApi } from "@/features/siswa/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import SearchField from "@/shared/components/SearchField.vue"
import type { Jenjang, Kelompok, Siswa } from "@/types/api"
import "./kelompok.css"

const toast = useToast()
const confirm = useConfirm()
const tab = ref("kelompok")
const levels = ref<Jenjang[]>([])
const groups = ref<Kelompok[]>([])
const loading = ref(false)
const listError = ref("")
const query = ref("")
const levelFilter = ref<number | null>(null)
const first = ref(0)
const levelFirst = ref(0)

const levelOptions = computed(() => levels.value.map((level) => ({
  label: level.kode + " — " + level.nama, value: level.id,
})))
const groupOptions = computed(() => groups.value.map((group) => ({
  label: (group.jenjang_kode || levelName(group.jenjang)) + " · " + group.nama,
  value: group.id,
})))
const filteredGroups = computed(() => groups.value.filter((group) =>
  (levelFilter.value === null || group.jenjang === levelFilter.value)
  && (!query.value.trim() || [group.nama, group.jenjang_kode, group.jenjang_nama]
    .some((value) => value?.toLocaleLowerCase("id-ID").includes(query.value.trim().toLocaleLowerCase("id-ID")))),
))
const pageGroups = computed(() => filteredGroups.value.slice(first.value, first.value + 12))
const pageLevels = computed(() => levels.value.slice(levelFirst.value, levelFirst.value + 10))
const activeStudents = computed(() => groups.value.reduce((total, group) => total + (group.siswa_aktif || 0), 0))
watch([query, levelFilter, groups], () => { first.value = 0 })
watch(levels, () => { levelFirst.value = 0 })

function levelName(id: number) { return levels.value.find((level) => level.id === id)?.kode || "Jenjang belum dimuat" }
function groupName(id: number | null) { return groupOptions.value.find((group) => group.value === id)?.label || "Kelompok belum dipilih" }
function errorText(error: unknown, fallback: string) {
  const message = friendlyError(error, fallback)
  return [message.summary, message.detail].filter(Boolean).join(". ")
}
function uncertain(error: unknown) {
  const status = (error as { response?: { status?: number } })?.response?.status
  return status == null || status >= 500
}

async function loadAll() {
  if (loading.value) return
  loading.value = true
  listError.value = ""
  try {
    const [loadedLevels, loadedGroups] = await Promise.all([jenjangApi.listAll(), kelompokApi.listAll()])
    levels.value = loadedLevels
    groups.value = loadedGroups
  } catch (error) {
    levels.value = []
    groups.value = []
    listError.value = errorText(error, "Jenjang dan kelompok belum berhasil dimuat")
  } finally { loading.value = false }
}
function resetFilter() { query.value = ""; levelFilter.value = null }
function showLevelGroups(level: Jenjang) { query.value = ""; levelFilter.value = level.id; tab.value = "kelompok" }

type FormKind = "jenjang" | "kelompok"
const formKind = ref<FormKind | null>(null)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref("")
const uncertainSave = ref(false)
const levelForm = reactive({ kode: "", nama: "" })
const groupForm = reactive({ jenjang: null as number | null, nama: "" })
const formInvalid = computed(() => formKind.value === "jenjang"
  ? !levelForm.kode.trim() || levelForm.kode.trim().length > 10 || !levelForm.nama.trim() || levelForm.nama.trim().length > 100
  : !groupForm.jenjang || !groupForm.nama.trim() || groupForm.nama.trim().length > 50)
const editingGroup = computed(() => groups.value.find((group) => group.id === editingId.value))
function openForm(kind: FormKind, row?: Jenjang | Kelompok) {
  formKind.value = kind
  editingId.value = row?.id ?? null
  formError.value = ""
  uncertainSave.value = false
  if (kind === "jenjang") {
    const level = row as Jenjang | undefined
    levelForm.kode = level?.kode || ""
    levelForm.nama = level?.nama || ""
  } else {
    const group = row as Kelompok | undefined
    groupForm.jenjang = group?.jenjang ?? levelFilter.value ?? null
    groupForm.nama = group?.nama || ""
  }
}
async function saveForm() {
  if (!formKind.value || formInvalid.value || saving.value || uncertainSave.value) return
  saving.value = true
  formError.value = ""
  try {
    const kind = formKind.value
    const id = editingId.value
    if (kind === "jenjang") {
      const payload = { kode: levelForm.kode.trim().toUpperCase(), nama: levelForm.nama.trim() }
      if (id) await jenjangApi.update(id, { nama: payload.nama })
      else await jenjangApi.create(payload)
    } else {
      const payload = { nama: groupForm.nama.trim(), jenjang: groupForm.jenjang! }
      if (id) await kelompokApi.update(id, payload)
      else await kelompokApi.create(payload)
    }
    formKind.value = null
    notifySuccess(toast, id ? "Perubahan disimpan" : kind === "jenjang" ? "Jenjang ditambahkan" : "Kelompok ditambahkan")
    await loadAll()
  } catch (error) {
    formError.value = errorText(error, "Data belum berhasil disimpan")
    uncertainSave.value = uncertain(error)
  } finally { saving.value = false }
}
function removeLevel(level: Jenjang) {
  if (groups.value.some((group) => group.jenjang === level.id)) return
  confirm.require({
    header: "Hapus jenjang?",
    message: level.kode + " — " + level.nama + " akan dihapus. Pendaftaran yang masih merujuk ke jenjang ini dapat kehilangan penanda jenjang. Tindakan ini tidak dapat dibatalkan.",
    acceptLabel: "Hapus jenjang", rejectLabel: "Batal", acceptClass: "p-button-danger",
    accept: async () => {
      try { await jenjangApi.remove(level.id); notifySuccess(toast, "Jenjang dihapus"); await loadAll() }
      catch (error) { notifyError(toast, error, "Jenjang belum berhasil dihapus") }
    },
  })
}
function removeGroup(group: Kelompok) {
  if ((group.siswa_aktif || 0) > 0) return
  confirm.require({
    header: "Hapus kelompok?",
    message: groupName(group.id) + " akan dihapus. Siswa nonaktif yang masih tercatat di kelompok ini akan kehilangan penanda kelompok. Tindakan ini tidak dapat dibatalkan.",
    acceptLabel: "Hapus kelompok", rejectLabel: "Batal", acceptClass: "p-button-danger",
    accept: async () => {
      try { await kelompokApi.remove(group.id); notifySuccess(toast, "Kelompok dihapus"); await loadAll() }
      catch (error) { notifyError(toast, error, "Kelompok belum berhasil dihapus") }
    },
  })
}

const source = ref<number | null>(null)
const target = ref<number | null>(null)
const sourceStudents = ref<Siswa[]>([])
const selectedIds = ref<number[]>([])
const loadingStudents = ref(false)
const moving = ref(false)
const moveError = ref("")
const uncertainMove = ref(false)
const reviewOpen = ref(false)
let sourceRequest = 0
const availableTargets = computed(() => groupOptions.value.filter((group) => group.value !== source.value))
const selectedStudents = computed(() => sourceStudents.value.filter((student) => selectedIds.value.includes(student.id)))
const canReview = computed(() => !!source.value && !!target.value && source.value !== target.value
  && selectedIds.value.length > 0 && !loadingStudents.value && !moving.value && !uncertainMove.value)
function showMove(group: Kelompok) {
  tab.value = "pindah"
  if (source.value === group.id) void loadSource()
  else source.value = group.id
}
watch(source, () => { target.value = null; void loadSource() })
watch(target, () => { reviewOpen.value = false; moveError.value = "" })
watch(selectedIds, () => { reviewOpen.value = false; moveError.value = "" })
async function loadSource() {
  const request = ++sourceRequest
  sourceStudents.value = []
  selectedIds.value = []
  moveError.value = ""
  uncertainMove.value = false
  reviewOpen.value = false
  if (!source.value) { loadingStudents.value = false; return }
  loadingStudents.value = true
  try {
    const students = await siswaApi.listAll({ kelompok: source.value, status: "aktif" })
    if (request === sourceRequest) sourceStudents.value = students
  } catch (error) {
    if (request === sourceRequest) moveError.value = errorText(error, "Siswa di kelompok asal belum berhasil dimuat")
  } finally { if (request === sourceRequest) loadingStudents.value = false }
}
async function currentSelection() {
  if (!source.value || !target.value || source.value === target.value) return false
  const current = await siswaApi.listAll({ kelompok: source.value, status: "aktif" })
  const available = new Set(current.map((student) => student.id))
  sourceStudents.value = current
  if (selectedIds.value.some((id) => !available.has(id))) {
    selectedIds.value = selectedIds.value.filter((id) => available.has(id))
    moveError.value = "Daftar siswa berubah. Periksa pilihan yang tersisa lalu ulangi."
    reviewOpen.value = false
    return false
  }
  return true
}
async function reviewMove() {
  if (!canReview.value) return
  loadingStudents.value = true
  moveError.value = ""
  try {
    if (await currentSelection()) reviewOpen.value = true
  } catch (error) { moveError.value = errorText(error, "Pilihan siswa belum dapat diperiksa") }
  finally { loadingStudents.value = false }
}
async function moveStudents() {
  if (!reviewOpen.value || !canReview.value || !target.value) return
  moving.value = true
  moveError.value = ""
  const count = selectedIds.value.length
  try {
    if (!await currentSelection()) return
    const result = await kelompokApi.pindahSiswa(target.value, [...selectedIds.value])
    reviewOpen.value = false
    notifySuccess(toast, result.updated === count ? count + " siswa dipindah" : result.updated + " dari " + count + " siswa dipindah")
    await Promise.all([loadSource(), loadAll()])
    if (result.updated !== count) moveError.value = "Jumlah yang dipindah berbeda dari pilihan awal. Periksa daftar siswa sebelum tindakan lain."
  } catch (error) {
    reviewOpen.value = false
    moveError.value = errorText(error, "Siswa belum berhasil dipindah")
    uncertainMove.value = uncertain(error)
  } finally { moving.value = false }
}
onMounted(loadAll)
</script>

<template>
  <PageLayout title="Kelompok belajar" subtitle="Atur jenjang dan rombongan belajar, lalu pindahkan siswa saat diperlukan." :surface="false">
    <div class="kelompok-summary" aria-label="Ringkasan kelompok belajar">
      <div><strong>{{ loading || listError ? "—" : levels.length }}</strong><span>Jenjang</span></div>
      <div><strong>{{ loading || listError ? "—" : groups.length }}</strong><span>Kelompok</span></div>
      <div><strong>{{ loading || listError ? "—" : activeStudents }}</strong><span>Siswa aktif dalam kelompok</span></div>
    </div>

    <Tabs v-model:value="tab" class="kelompok-tabs">
      <TabList aria-label="Pengelolaan kelompok">
        <Tab value="kelompok">Kelompok</Tab>
        <Tab value="jenjang">Jenjang</Tab>
        <Tab value="pindah">Pindah siswa</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="kelompok">
          <section class="kelompok-panel" aria-label="Daftar kelompok" :aria-busy="loading">
            <header class="kelompok-heading"><div><h2>Daftar kelompok</h2><p>Lihat jumlah siswa aktif dan kelola rombongan belajar per jenjang.</p></div><Button label="Tambah kelompok" :disabled="loading || !!listError || !levels.length" @click="openForm('kelompok')"><template #icon><Icon name="plus" /></template></Button></header>
            <div class="kelompok-toolbar">
              <div class="kelompok-field kelompok-search"><label for="kelompok-search">Cari kelompok</label><SearchField input-id="kelompok-search" v-model="query" placeholder="Nama kelompok atau jenjang" /></div>
              <div class="kelompok-field"><label for="kelompok-level-filter">Jenjang</label><Select input-id="kelompok-level-filter" v-model="levelFilter" :options="[{ label: 'Semua jenjang', value: null }, ...levelOptions]" option-label="label" option-value="value" placeholder="Semua jenjang" :disabled="loading || !!listError"><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
            </div>
            <div v-if="listError" class="kelompok-notice"><Message severity="error" :closable="false">{{ listError }}</Message><Button label="Muat ulang daftar" severity="secondary" @click="loadAll" /></div>
            <div class="kelompok-results"><p role="status">{{ loading ? "Memuat kelompok…" : listError ? "Daftar belum tersedia" : filteredGroups.length ? (first + 1) + "–" + Math.min(first + 12, filteredGroups.length) + " dari " + filteredGroups.length + " kelompok" : "Tidak ada kelompok ditampilkan" }}</p><Button v-if="query || levelFilter !== null" label="Hapus filter" severity="secondary" text @click="resetFilter" /></div>
            <div v-if="loading" class="kelompok-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan daftar kelompok</p></div>
            <div v-else-if="!listError && !filteredGroups.length" class="kelompok-empty"><Icon :name="query || levelFilter !== null ? 'magnifying-glass' : 'users-three'" /><h3>{{ query || levelFilter !== null ? "Tidak ada kelompok yang cocok" : "Belum ada kelompok" }}</h3><p>{{ query || levelFilter !== null ? "Coba kata kunci atau jenjang lain." : "Tambahkan jenjang terlebih dahulu, lalu buat kelompok belajar." }}</p><Button :label="query || levelFilter !== null ? 'Hapus filter' : levels.length ? 'Tambah kelompok' : 'Buka jenjang'" severity="secondary" @click="query || levelFilter !== null ? resetFilter() : levels.length ? openForm('kelompok') : tab = 'jenjang'" /></div>
            <template v-else-if="!listError">
              <table class="kelompok-table"><caption class="kelompok-sr-only">Daftar kelompok belajar</caption><thead><tr><th>Kelompok</th><th>Jenjang</th><th class="kelompok-number">Siswa aktif</th><th class="kelompok-actions">Tindakan</th></tr></thead><tbody><tr v-for="group in pageGroups" :key="group.id"><td><strong>{{ group.nama }}</strong></td><td>{{ group.jenjang_kode || levelName(group.jenjang) }}<small>{{ group.jenjang_nama || levels.find(level => level.id === group.jenjang)?.nama }}</small></td><td class="kelompok-number">{{ group.siswa_aktif ?? "—" }}</td><td class="kelompok-actions"><Button label="Ubah" severity="secondary" :aria-label="'Ubah ' + groupName(group.id)" @click="openForm('kelompok', group)" /><Button v-if="group.siswa_aktif" label="Pindahkan siswa" severity="secondary" text :aria-label="'Pindahkan siswa dari ' + groupName(group.id)" @click="showMove(group)" /><Button v-else label="Hapus" severity="secondary" text :aria-label="'Hapus ' + groupName(group.id)" @click="removeGroup(group)" /></td></tr></tbody></table>
              <ul class="kelompok-cards" aria-label="Daftar kelompok belajar"><li v-for="group in pageGroups" :key="group.id"><div><strong>{{ group.nama }}</strong><span>{{ group.jenjang_kode || levelName(group.jenjang) }} · {{ group.jenjang_nama }}</span></div><p><strong>{{ group.siswa_aktif ?? "—" }}</strong> siswa aktif</p><div class="kelompok-card-actions"><Button label="Ubah kelompok" severity="secondary" @click="openForm('kelompok', group)" /><Button v-if="group.siswa_aktif" label="Pindahkan siswa" severity="secondary" text @click="showMove(group)" /><Button v-else label="Hapus" severity="secondary" text @click="removeGroup(group)" /></div></li></ul>
              <Paginator v-if="filteredGroups.length > 12" v-model:first="first" :rows="12" :total-records="filteredGroups.length" template="PrevPageLink PageLinks NextPageLink"><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></Paginator>
            </template>
            <p class="kelompok-footnote"><Icon name="info" />Jumlah di sini hanya siswa berstatus aktif. Kelompok dengan siswa aktif baru dapat dihapus setelah siswanya dipindah.</p>
          </section>
        </TabPanel>

        <TabPanel value="jenjang">
          <section class="kelompok-panel" aria-label="Daftar jenjang" :aria-busy="loading">
            <header class="kelompok-heading"><div><h2>Jenjang sekolah</h2><p>Setiap kelompok berada dalam satu jenjang. Kode jenjang tidak dapat diubah setelah dibuat.</p></div><Button label="Tambah jenjang" :disabled="loading || !!listError" @click="openForm('jenjang')"><template #icon><Icon name="plus" /></template></Button></header>
            <div v-if="listError" class="kelompok-notice"><Message severity="error" :closable="false">{{ listError }}</Message><Button label="Muat ulang daftar" severity="secondary" @click="loadAll" /></div>
            <div class="kelompok-results"><p role="status">{{ loading ? "Memuat jenjang…" : listError ? "Daftar belum tersedia" : levels.length + " jenjang tersedia" }}</p></div>
            <div v-if="loading" class="kelompok-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan jenjang</p></div>
            <div v-else-if="!listError && !levels.length" class="kelompok-empty"><Icon name="tree-structure" /><h3>Belum ada jenjang</h3><p>Mulai dengan jenjang yang dipakai sekolah, misalnya PG, TKA, atau TKB.</p><Button label="Tambah jenjang" severity="secondary" @click="openForm('jenjang')" /></div>
            <template v-else-if="!listError">
              <table class="kelompok-table kelompok-level-table"><caption class="kelompok-sr-only">Jenjang sekolah</caption><thead><tr><th>Kode</th><th>Nama jenjang</th><th class="kelompok-number">Kelompok</th><th class="kelompok-actions">Tindakan</th></tr></thead><tbody><tr v-for="level in pageLevels" :key="level.id"><td><strong>{{ level.kode }}</strong></td><td>{{ level.nama }}</td><td class="kelompok-number">{{ groups.filter(group => group.jenjang === level.id).length }}</td><td class="kelompok-actions"><Button label="Ubah" severity="secondary" :aria-label="'Ubah jenjang ' + level.kode" @click="openForm('jenjang', level)" /><Button v-if="groups.some(group => group.jenjang === level.id)" label="Lihat kelompok" severity="secondary" text :aria-label="'Lihat kelompok jenjang ' + level.kode" @click="showLevelGroups(level)" /><Button v-else label="Hapus" severity="secondary" text :aria-label="'Hapus jenjang ' + level.kode" @click="removeLevel(level)" /></td></tr></tbody></table>
              <ul class="kelompok-cards" aria-label="Jenjang sekolah"><li v-for="level in pageLevels" :key="level.id"><div><strong>{{ level.kode }}</strong><span>{{ level.nama }}</span></div><p><strong>{{ groups.filter(group => group.jenjang === level.id).length }}</strong> kelompok</p><div class="kelompok-card-actions"><Button label="Ubah jenjang" severity="secondary" @click="openForm('jenjang', level)" /><Button v-if="groups.some(group => group.jenjang === level.id)" label="Lihat kelompok" severity="secondary" text @click="showLevelGroups(level)" /><Button v-else label="Hapus" severity="secondary" text @click="removeLevel(level)" /></div></li></ul>
              <Paginator v-if="levels.length > 10" v-model:first="levelFirst" :rows="10" :total-records="levels.length" template="PrevPageLink PageLinks NextPageLink"><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></Paginator>
            </template>
          </section>
        </TabPanel>

        <TabPanel value="pindah">
          <section class="kelompok-panel kelompok-move" aria-label="Pindah siswa">
            <header class="kelompok-heading"><div><h2>Pindah siswa</h2><p>Pilih kelompok asal, siswa aktif, lalu kelompok tujuan. Periksa pilihan sebelum menyimpan.</p></div></header>
            <div v-if="listError" class="kelompok-notice"><Message severity="error" :closable="false">{{ listError }}</Message><Button label="Muat ulang kelompok" severity="secondary" @click="loadAll" /></div>
            <div class="kelompok-move-body">
              <div class="kelompok-move-fields">
                <div class="kelompok-field"><label for="kelompok-source">Kelompok asal</label><Select input-id="kelompok-source" v-model="source" :options="groupOptions" option-label="label" option-value="value" placeholder="Pilih kelompok asal" filter fluid :disabled="loading || !!listError || moving"><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select></div>
                <div class="kelompok-field"><label for="kelompok-students">Siswa aktif yang dipindah</label><MultiSelect input-id="kelompok-students" v-model="selectedIds" :options="sourceStudents" option-label="nama" option-value="id" placeholder="Pilih siswa" filter fluid :max-selected-labels="2" :selected-items-label="'{0} siswa dipilih'" :disabled="!source || loadingStudents || moving || !!moveError && !sourceStudents.length"><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template><template #option="{ option }"><span>{{ option.nama }} <small v-if="option.nis">· NIS {{ option.nis }}</small></span></template></MultiSelect><small v-if="source && !loadingStudents">{{ sourceStudents.length }} siswa aktif tersedia di kelompok asal.</small></div>
                <div class="kelompok-field"><label for="kelompok-target">Kelompok tujuan</label><Select input-id="kelompok-target" v-model="target" :options="availableTargets" option-label="label" option-value="value" placeholder="Pilih kelompok tujuan" filter fluid :disabled="!source || loadingStudents || moving"><template #dropdownicon><Icon name="caret-down" /></template><template #filtericon><Icon name="magnifying-glass" /></template></Select></div>
                <div v-if="moveError" role="alert"><Message :severity="uncertainMove ? 'warn' : 'error'" :closable="false">{{ moveError }}{{ uncertainMove ? " Muat ulang siswa asal dan periksa kelompok tujuan sebelum mencoba lagi." : "" }}</Message><Button v-if="source" label="Muat ulang siswa asal" severity="secondary" :disabled="moving" @click="loadSource" /></div>
                <div v-if="loadingStudents" role="status" class="kelompok-loading"><Icon name="arrows-clockwise" class="bee-spin" />Memuat siswa aktif…</div>
                <Button label="Periksa perpindahan" :disabled="!canReview" :loading="loadingStudents" @click="reviewMove"><template #icon><Icon name="arrow-right" /></template></Button>
              </div>
              <aside class="kelompok-move-note"><Icon name="info" /><div><strong>Yang berubah</strong><p>Kelompok pada profil siswa akan menjadi kelompok tujuan. Tagihan yang sudah dibuat dan tarif SPP siswa tidak otomatis berubah. Periksa administrasi terkait setelah perpindahan.</p></div></aside>
            </div>
          </section>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog :visible="!!formKind" @update:visible="value => { if (!value && !saving) formKind = null }" :header="formKind === 'jenjang' ? editingId ? 'Ubah jenjang' : 'Tambah jenjang' : editingId ? 'Ubah kelompok' : 'Tambah kelompok'" class="kelompok-dialog" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup formulir' }"><template #closeicon><Icon name="x" /></template>
      <form v-if="formKind" id="kelompok-form" @submit.prevent="saveForm">
        <p class="kelompok-dialog-intro">{{ formKind === "jenjang" ? "Jenjang mengelompokkan rombongan belajar sekolah." : "Kelompok dipakai di profil siswa dan pencatatan absensi." }}</p>
        <div v-if="formKind === 'jenjang'" class="kelompok-field"><label for="jenjang-kode">Kode jenjang <span>(wajib)</span></label><InputText id="jenjang-kode" v-model="levelForm.kode" :disabled="!!editingId || saving" maxlength="10" fluid placeholder="Contoh: TKA" /><small v-if="editingId">Kode tidak dapat diubah setelah jenjang dibuat.</small></div>
        <div v-else class="kelompok-field"><label for="kelompok-jenjang">Jenjang <span>(wajib)</span></label><Select input-id="kelompok-jenjang" v-model="groupForm.jenjang" :options="levelOptions" option-label="label" option-value="value" placeholder="Pilih jenjang" :disabled="saving" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <Message v-if="formKind === 'kelompok' && editingGroup && editingGroup.jenjang !== groupForm.jenjang && editingGroup.siswa_aktif" severity="warn" :closable="false">Mengubah jenjang kelompok juga mengubah jenjang yang terlihat pada profil {{ editingGroup.siswa_aktif }} siswa aktif di dalamnya.</Message>
        <div class="kelompok-field"><label for="kelompok-nama">{{ formKind === "jenjang" ? "Nama jenjang" : "Nama kelompok" }} <span>(wajib)</span></label><InputText v-if="formKind === 'jenjang'" id="kelompok-nama" v-model="levelForm.nama" maxlength="100" :disabled="saving" fluid placeholder="Contoh: Taman Kanak-kanak A" /><InputText v-else id="kelompok-nama" v-model="groupForm.nama" maxlength="50" :disabled="saving" fluid placeholder="Contoh: Melati" /></div>
        <Message v-if="formError" :severity="uncertainSave ? 'warn' : 'error'" :closable="false" role="alert">{{ formError }}{{ uncertainSave ? " Periksa daftar terbaru sebelum mencoba lagi." : "" }}</Message>
      </form>
      <template #footer><Button label="Batal" severity="secondary" :disabled="saving" @click="formKind = null" /><Button v-if="uncertainSave" label="Periksa daftar" severity="secondary" @click="formKind = null; loadAll()" /><Button v-else label="Simpan" type="submit" form="kelompok-form" :disabled="formInvalid || saving" :loading="saving"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
    </Dialog>

    <Dialog :visible="reviewOpen" @update:visible="value => { if (!value && !moving) reviewOpen = false }" header="Periksa perpindahan siswa" class="kelompok-dialog" modal :draggable="false" :closable="!moving" :close-on-escape="!moving" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup pemeriksaan' }"><template #closeicon><Icon name="x" /></template>
      <p class="kelompok-dialog-intro">{{ selectedIds.length }} siswa akan dipindah dari <strong>{{ groupName(source) }}</strong> ke <strong>{{ groupName(target) }}</strong>.</p>
      <ul class="kelompok-review-list"><li v-for="student in selectedStudents" :key="student.id">{{ student.nama }}<small v-if="student.nis">NIS {{ student.nis }}</small></li></ul>
      <Message severity="info" :closable="false">Tagihan yang sudah dibuat dan tarif SPP tidak otomatis berubah.</Message>
      <template #footer><Button label="Kembali" severity="secondary" :disabled="moving" @click="reviewOpen = false" /><Button label="Pindahkan siswa" :disabled="!canReview || moving" :loading="moving" @click="moveStudents"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
    </Dialog>
  </PageLayout>
</template>
