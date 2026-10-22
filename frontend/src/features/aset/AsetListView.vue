<script setup lang="ts">
import BeePaginator from '@/shared/components/BeePaginator.vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { notifySuccess } from '@/core/errors'
import { coaApi } from '@/features/jurnal/api'
import { ambiguous, dateLabel, errorText, money } from '@/features/kepegawaian/payroll'
import EmployeeActionDialog from '@/features/kepegawaian/EmployeeActionDialog.vue'
import PageLayout from '@/shared/components/PageLayout.vue'
import SearchField from '@/shared/components/SearchField.vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { useTableSearch } from '@/shared/composables/useTableSearch'
import { useAuthStore } from '@/stores/auth'
import type { Coa, FixedAsset } from '@/types/api'
import { asetApi } from './api'
import AsetFormDialog from './AsetFormDialog.vue'
import '@/features/kepegawaian/employee-finance.css'
import './asset.css'

const auth = useAuthStore(), toast = useToast(), confirm = useConfirm()
const canWrite = computed(() => auth.hasRole(['Finance']))
const rows = ref<FixedAsset[]>([]), loading = ref(false), listError = ref(''), notice = ref('')
const accounts = ref<Coa[]>([]), accountsLoading = ref(false), accountsError = ref('')
const first = ref(0)
const { query, filtered } = useTableSearch(rows, row => [row.nama, account(row.akun_aset), account(row.akun_akumulasi), account(row.akun_beban_depr), row.tanggal_perolehan, dateLabel(row.tanggal_perolehan)])
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 15))
watch([query, rows], () => { first.value = 0 })
const busy = computed(() => loading.value || opening.value || saving.value || actionPending.value || checking.value)

async function load() {
  if (loading.value) return
  loading.value = true; listError.value = ''
  try { rows.value = await asetApi.listAll() }
  catch (error) { rows.value = []; listError.value = errorText(error, 'Daftar aset belum berhasil dimuat') }
  finally { loading.value = false }
}
async function loadAccounts() {
  if (accountsLoading.value) return
  accountsLoading.value = true; accountsError.value = ''
  try { accounts.value = await coaApi.list() }
  catch (error) { accounts.value = []; accountsError.value = errorText(error, 'Daftar akun belum berhasil dimuat') }
  finally { accountsLoading.value = false }
}
function account(code: string) { const name = accounts.value.find(item => item.kode_akun === code)?.nama_akun; return name ? `${code} · ${name}` : code }

const detail = ref<FixedAsset | null>(null), detailOpen = ref(false), opening = ref(false), detailError = ref('')
async function inspect(row: FixedAsset) {
  if (busy.value) return
  opening.value = true; detailError.value = ''; notice.value = ''
  try { detail.value = await asetApi.get(row.id); detailOpen.value = true }
  catch (error) { detailError.value = errorText(error, 'Rincian aset belum berhasil dimuat') }
  finally { opening.value = false }
}
const formOpen = ref(false), editing = ref<FixedAsset | null>(null), saving = ref(false), formError = ref(''), uncertainSave = ref(false), dirty = ref(false)
async function create() {
  if (!canWrite.value || busy.value) return
  editing.value = null; formError.value = ''; uncertainSave.value = false; formOpen.value = true
  if (!accounts.value.length) await loadAccounts()
}
async function edit() {
  if (!canWrite.value || !detail.value || busy.value) return
  opening.value = true; detailError.value = ''
  try {
    const latest = await asetApi.get(detail.value.id)
    detail.value = latest; editing.value = latest; formError.value = ''; uncertainSave.value = false; detailOpen.value = false; formOpen.value = true
    if (!accounts.value.length) await loadAccounts()
  } catch (error) { detailError.value = errorText(error, 'Aset terbaru belum dapat dibuka') }
  finally { opening.value = false }
}
async function save(payload: Partial<FixedAsset>) {
  if (!canWrite.value || saving.value || uncertainSave.value) return
  saving.value = true; formError.value = ''
  try {
    const result = editing.value ? await asetApi.update(editing.value.id, payload) : await asetApi.create(payload)
    formOpen.value = false; detail.value = result; detailOpen.value = true
    notifySuccess(toast, editing.value ? 'Perubahan aset disimpan' : 'Aset disimpan')
    await load()
  } catch (error) { formError.value = errorText(error, 'Aset belum berhasil disimpan'); uncertainSave.value = ambiguous(error) }
  finally { saving.value = false }
}
async function reviewSave() { formOpen.value = false; notice.value = 'Periksa aset pada daftar sebelum membuat atau mengubahnya lagi.'; await load() }

type AssetAction = 'depreciate' | 'delete'
const action = ref<AssetAction | null>(null), target = ref<FixedAsset | null>(null)
const actionReady = ref(false), actionPending = ref(false), checking = ref(false), actionError = ref(''), uncertainAction = ref(false)
const canDelete = (row: FixedAsset) => Number(row.akumulasi_penyusutan) === 0
async function startAction(kind: AssetAction) {
  if (!canWrite.value || !detail.value || busy.value) return
  target.value = detail.value; action.value = kind; actionReady.value = false; uncertainAction.value = false; actionError.value = ''; detailOpen.value = false
  await refreshAction()
}
async function refreshAction() {
  if (!target.value || checking.value || actionPending.value) return
  checking.value = true; actionError.value = ''; actionReady.value = false
  try {
    const latest = await asetApi.get(target.value.id)
    if (uncertainAction.value && action.value === 'depreciate') {
      if (latest.akumulasi_penyusutan !== target.value.akumulasi_penyusutan) {
        notice.value = 'Akumulasi penyusutan berubah. Periksa jurnal penyusutan sebelum mencatat lagi.'
        target.value = null; action.value = null; detail.value = latest; detailOpen.value = true; await load(); return
      }
      actionError.value = 'Hasil pencatatan belum dapat dipastikan dari data aset. Periksa jurnal penyusutan sebelum tindakan baru.'
      return
    }
    if (action.value === 'delete' && !canDelete(latest)) { actionError.value = 'Aset sudah memiliki akumulasi penyusutan dan tidak dapat dihapus dari layar ini.'; target.value = latest; return }
    target.value = latest; detail.value = latest; actionReady.value = true; uncertainAction.value = false
  } catch (error) {
    if ((error as { response?: { status?: number } }).response?.status === 404) { notice.value = 'Aset tidak lagi tersedia pada daftar.'; target.value = null; action.value = null; detail.value = null; detailOpen.value = false; await load() }
    else actionError.value = errorText(error, 'Data aset terbaru belum dapat diperiksa')
  } finally { checking.value = false }
}
async function confirmAction() {
  if (!target.value || !action.value || !actionReady.value || !canWrite.value || busy.value || uncertainAction.value) return
  actionPending.value = true; actionError.value = ''
  const current = target.value, kind = action.value
  try {
    if (kind === 'delete') {
      await asetApi.remove(current.id)
      target.value = null; action.value = null; detail.value = null; detailOpen.value = false
      notifySuccess(toast, 'Aset dihapus dari daftar')
    } else {
      await asetApi.susutkan(current.id)
      target.value = null; action.value = null
      notice.value = 'Jurnal penyusutan Draf dibuat. Periksa dan lanjutkan pencatatannya di Jurnal.'
      notifySuccess(toast, 'Penyusutan dicatat sebagai jurnal Draf')
    }
  } catch (error) { actionError.value = errorText(error, kind === 'delete' ? 'Aset belum berhasil dihapus' : 'Hasil penyusutan belum berhasil dipastikan'); uncertainAction.value = ambiguous(error); actionReady.value = false }
  finally { actionPending.value = false }
  if (!target.value && !action.value) {
    await load()
    if (kind === 'depreciate') {
      try { detail.value = await asetApi.get(current.id); detailOpen.value = true }
      catch (error) { detailError.value = errorText(error, 'Rincian terbaru belum berhasil dimuat') }
    }
  }
}
function closeAction() { if (actionPending.value || checking.value) return; if (uncertainAction.value) notice.value = action.value === 'delete' ? 'Hasil penghapusan belum pasti. Periksa daftar aset sebelum mencoba lagi.' : 'Hasil penyusutan belum pasti. Periksa jurnal penyusutan sebelum mencoba lagi.'; target.value = null; action.value = null; actionError.value = ''; uncertainAction.value = false; detailOpen.value = !!detail.value }
function askLeave() { return new Promise<boolean>(resolve => confirm.require({ header: 'Perubahan belum disimpan', message: 'Perubahan aset pada form ini belum disimpan. Tinggalkan halaman?', acceptLabel: 'Tinggalkan halaman', rejectLabel: 'Tetap di sini', acceptProps: { severity: 'danger' }, accept: () => resolve(true), reject: () => resolve(false), onHide: () => resolve(false) })) }
function beforeUnload(event: BeforeUnloadEvent) { if (saving.value || actionPending.value || dirty.value) { event.preventDefault(); event.returnValue = '' } }
onBeforeRouteLeave(async () => !saving.value && !actionPending.value && (!dirty.value || await askLeave()))
onMounted(() => { void load(); void loadAccounts(); window.addEventListener('beforeunload', beforeUnload) })
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

<template>
  <PageLayout title="Aset tetap" subtitle="Periksa nilai aset dan catat penyusutan bulanan." :surface="false"><template #actions><Button v-if="canWrite" label="Tambah aset" :disabled="busy" @click="create"><template #icon><Icon name="plus" /></template></Button></template>
    <section class="employee-panel asset-register" aria-label="Daftar aset tetap" :aria-busy="loading">
      <header class="employee-heading"><div><h2>Register aset</h2><p>Harga perolehan, akumulasi, dan penyusutan per bulan ditampilkan sesuai catatan aset.</p></div><Button label="Muat ulang daftar" severity="secondary" :disabled="busy" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></header>
      <div class="employee-toolbar"><div class="employee-field employee-search"><label for="asset-search">Cari aset</label><SearchField input-id="asset-search" v-model="query" placeholder="Nama, akun, atau tanggal perolehan" hint="Mencari seluruh aset yang dimuat" /></div></div>
      <div v-if="detailError || notice" class="employee-notice" role="status"><Message :severity="detailError ? 'error' : notice.startsWith('Jurnal penyusutan Draf') ? 'success' : 'warn'" :closable="false">{{ detailError || notice }} <RouterLink v-if="notice.toLowerCase().includes('jurnal')" to="/jurnal">Buka jurnal</RouterLink></Message></div>
      <div class="employee-results"><p role="status">{{ loading ? 'Memuat aset…' : listError ? 'Daftar belum tersedia' : `${filtered.length ? first + 1 : 0}–${Math.min(first + 15, filtered.length)} dari ${filtered.length} aset` }}</p><Button v-if="query.trim()" label="Hapus pencarian" severity="secondary" text @click="query = ''" /></div>
      <div v-if="loading" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan daftar aset</p></div>
      <div v-else-if="listError" class="employee-empty"><Icon name="warning-circle" /><h3>Daftar aset belum dapat ditampilkan</h3><p role="alert">{{ listError }}</p><Button label="Coba muat ulang aset" severity="secondary" @click="load" /></div>
      <div v-else-if="!filtered.length" class="employee-empty"><Icon :name="query.trim() ? 'magnifying-glass' : 'cube'" /><h3>{{ query.trim() ? 'Tidak ada aset yang cocok' : 'Belum ada aset tetap' }}</h3><p>{{ query.trim() ? 'Coba nama, kode akun, atau tanggal lain.' : 'Tambahkan aset untuk mencatat nilai perolehan dan penyusutannya.' }}</p><Button v-if="query.trim() || canWrite" :label="query.trim() ? 'Hapus pencarian' : 'Tambah aset'" severity="secondary" @click="query.trim() ? query = '' : create()" /></div>
      <template v-else>
        <table class="employee-table asset-table"><caption class="employee-sr-only">Register aset tetap, 15 aset per halaman</caption><thead><tr><th>Aset</th><th>Perolehan</th><th class="employee-number">Akumulasi</th><th class="employee-number">Penyusutan per bulan</th><th class="employee-action-column">Tindakan</th></tr></thead><tbody><tr v-for="row in pageRows" :key="row.id"><td><strong>{{ row.nama }}</strong><small>Akun {{ account(row.akun_aset) }}</small></td><td><time :datetime="row.tanggal_perolehan">{{ dateLabel(row.tanggal_perolehan) }}</time><small class="asset-money">{{ money(row.harga_perolehan) }}</small></td><td class="employee-number">{{ money(row.akumulasi_penyusutan) }}</td><td class="employee-number">{{ money(row.penyusutan_per_bulan) }}<small>{{ row.umur_manfaat_bulan }} bulan · garis lurus</small></td><td class="employee-action-column"><Button label="Periksa" severity="secondary" :aria-label="`Periksa ${row.nama}`" :disabled="busy" @click="inspect(row)" /></td></tr></tbody></table>
        <ul class="employee-cards asset-cards" aria-label="Daftar aset"><li v-for="row in pageRows" :key="row.id"><header><div><strong>{{ row.nama }}</strong><small>Akun {{ account(row.akun_aset) }}</small></div></header><dl><div><dt>Tanggal perolehan</dt><dd><time :datetime="row.tanggal_perolehan">{{ dateLabel(row.tanggal_perolehan) }}</time></dd></div><div><dt>Harga perolehan</dt><dd>{{ money(row.harga_perolehan) }}</dd></div><div><dt>Akumulasi</dt><dd>{{ money(row.akumulasi_penyusutan) }}</dd></div><div><dt>Penyusutan per bulan</dt><dd>{{ money(row.penyusutan_per_bulan) }}</dd></div><div><dt>Masa manfaat</dt><dd>{{ row.umur_manfaat_bulan }} bulan</dd></div></dl><div class="employee-card-actions"><Button label="Periksa aset" severity="secondary" :aria-label="`Periksa ${row.nama}`" :disabled="busy" @click="inspect(row)" /></div></li></ul>
        <BeePaginator v-model:first="first" :rows="15" :total-records="filtered.length" :always-show="filtered.length > 15" />
      </template>
      <p class="employee-footnote"><Icon name="info" />Mencatat penyusutan menambah akumulasi aset dan membuat jurnal Draf. Jurnal perlu diproses lewat alur pencatatan keuangan.</p>
    </section>
    <Dialog :visible="detailOpen" @update:visible="value => { if (!value) detailOpen = false }" header="Rincian aset" class="employee-form-dialog asset-detail-dialog" modal :draggable="false" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup rincian aset' }"><template #closeicon><Icon name="x" /></template>
      <template v-if="detail"><div class="employee-detail-heading"><h3>{{ detail.nama }}</h3><p>Diperoleh <time :datetime="detail.tanggal_perolehan">{{ dateLabel(detail.tanggal_perolehan) }}</time> · masa manfaat {{ detail.umur_manfaat_bulan }} bulan</p></div><dl class="employee-detail-list"><div><dt>Harga perolehan</dt><dd>{{ money(detail.harga_perolehan) }}</dd></div><div><dt>Akumulasi penyusutan</dt><dd>{{ money(detail.akumulasi_penyusutan) }}</dd></div><div><dt>Penyusutan per bulan</dt><dd>{{ money(detail.penyusutan_per_bulan) }}</dd></div><div><dt>Metode</dt><dd>Garis lurus</dd></div></dl><h3 class="asset-account-title">Akun jurnal</h3><dl class="employee-detail-list asset-account-list"><div><dt>Aset</dt><dd>{{ account(detail.akun_aset) }}</dd></div><div><dt>Akumulasi penyusutan</dt><dd>{{ account(detail.akun_akumulasi) }}</dd></div><div><dt>Beban penyusutan</dt><dd>{{ account(detail.akun_beban_depr) }}</dd></div></dl><p class="employee-small-note">Penyusutan memakai nominal bulanan pada catatan aset. Jurnal Draf dibuat dengan tanggal saat tindakan dicatat.</p><Message v-if="detailError" severity="error" :closable="false">{{ detailError }}</Message></template>
      <template #footer><Button label="Tutup" severity="secondary" @click="detailOpen = false" /><Button v-if="canWrite && detail && canDelete(detail)" label="Hapus aset" severity="danger" text :disabled="busy" @click="startAction('delete')" /><Button v-if="canWrite && detail" label="Ubah aset" severity="secondary" :disabled="busy" @click="edit" /><Button v-if="canWrite && detail" label="Catat penyusutan" :disabled="busy" @click="startAction('depreciate')" /></template>
    </Dialog>
    <AsetFormDialog v-model="formOpen" :row="editing" :accounts="accounts" :accounts-loading="accountsLoading" :accounts-error="accountsError" :saving="saving" :uncertain="uncertainSave" :error="formError" @save="save" @reload-accounts="loadAccounts" @review="reviewSave" @dirty="dirty = $event" />
    <EmployeeActionDialog :visible="!!target" :title="action === 'delete' ? 'Hapus aset dari daftar?' : 'Catat penyusutan aset?'" :label="target?.nama || ''" :amount="target ? money(action === 'delete' ? target.harga_perolehan : target.penyusutan_per_bulan) : ''" :description="action === 'delete' ? 'Aset tanpa akumulasi penyusutan akan dikeluarkan dari daftar. Periksa nama dan nilai perolehannya sebelum menghapus.' : 'Sistem menambah akumulasi aset dan membuat jurnal beban penyusutan berstatus Draf untuk bulan berjalan. Jurnal belum masuk buku besar. Periksa nominal sebelum melanjutkan.'" :confirm-label="action === 'delete' ? 'Hapus aset' : 'Catat penyusutan'" :danger="action === 'delete'" :pending="actionPending" :checking="checking" :error="actionError" :uncertain="uncertainAction" :ready="actionReady" @close="closeAction" @confirm="confirmAction" @refresh="refreshAction" />
  </PageLayout>
</template>
