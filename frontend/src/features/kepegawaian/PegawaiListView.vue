<script setup lang="ts">
import BeePaginator from '@/shared/components/BeePaginator.vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import PageLayout from '@/shared/components/PageLayout.vue'
import SearchField from '@/shared/components/SearchField.vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { useTableSearch } from '@/shared/composables/useTableSearch'
import { useAuthStore } from '@/stores/auth'
import { notifySuccess } from '@/core/errors'
import type { Pegawai, PegawaiInput } from '@/types/api'
import { pegawaiApi } from './api'
import { ambiguous, errorText } from './payroll'
import { employeeStatus, employeeStatuses, staffPeriod } from './staff'
import type { PegawaiStatus } from '@/types/api'
import PegawaiFormDialog from './PegawaiFormDialog.vue'
import EmployeeActionDialog from './EmployeeActionDialog.vue'
import './employee-finance.css'
import './staff.css'
const auth = useAuthStore(), toast = useToast(), confirm = useConfirm()
const canWrite = computed(() => auth.hasRole(['Administration','Finance']))
const rows = ref<Pegawai[]>([]), loading = ref(false), error = ref(''), actionError = ref('')
const status = ref<PegawaiStatus | null>(null), first = ref(0)
const scoped = computed(() => rows.value.filter(row => status.value == null || row.status === status.value))
const { query, filtered } = useTableSearch(scoped, row => [row.nama,row.nip,row.jabatan,row.nomor_hp])
const pageRows = computed(() => filtered.value.slice(first.value,first.value+15))
const hasFilter = computed(() => !!query.value.trim() || status.value != null)
const formOpen = ref(false), editing = ref<Pegawai | null>(null), saving = ref(false), opening = ref(false), formError = ref(''), uncertainSave = ref(false), dirty = ref(false)
const target = ref<Pegawai | null>(null), pending = ref(false), checking = ref(false), deleteError = ref(''), uncertainDelete = ref(false), ready = ref(false)
const busy = computed(() => saving.value || opening.value || pending.value || checking.value)
const menu = ref<InstanceType<typeof Menu> | null>(null), menuTarget = ref<Pegawai | null>(null), menuOpen = ref(false)
const items = computed(() => menuTarget.value && canWrite.value ? [{ label:'Hapus pegawai',icon:'trash',class:'employee-action-danger',command:() => startDelete(menuTarget.value!) }] : [])
watch([query,status,rows], () => { first.value=0; menu.value?.hide() })
function reset() { query.value=''; status.value=null }
async function load() {
  if (loading.value) return
  loading.value=true; error.value=''
  try { rows.value=await pegawaiApi.listAll() }
  catch(e) { rows.value=[]; error.value=errorText(e,'Daftar pegawai belum berhasil dimuat') }
  finally { loading.value=false }
}
function create() { if (!canWrite.value || busy.value) return; editing.value=null; formError.value=''; uncertainSave.value=false; formOpen.value=true }
async function edit(row: Pegawai) {
  if (!canWrite.value || busy.value) return
  opening.value=true; actionError.value=''
  try { editing.value=await pegawaiApi.get(row.id); formError.value=''; uncertainSave.value=false; formOpen.value=true }
  catch(e) { actionError.value=errorText(e,'Profil terbaru belum dapat dibuka. Coba kembali.') }
  finally { opening.value=false }
}
async function save(payload: Partial<PegawaiInput>) {
  if (!canWrite.value || saving.value || uncertainSave.value) return
  saving.value=true; formError.value=''
  try {
    if (editing.value) await pegawaiApi.update(editing.value.id,payload)
    else await pegawaiApi.create(payload)
    formOpen.value=false; notifySuccess(toast,'Data pegawai disimpan'); await load()
  } catch(e) { formError.value=errorText(e,'Data pegawai belum berhasil disimpan'); uncertainSave.value=ambiguous(e) }
  finally { saving.value=false }
}
async function startDelete(row: Pegawai) { if (!canWrite.value || busy.value) return; target.value=row; ready.value=false; uncertainDelete.value=false; await refreshDelete() }
async function refreshDelete() {
  if (!target.value || checking.value || pending.value) return
  checking.value=true; deleteError.value=''; ready.value=false
  try { target.value=await pegawaiApi.get(target.value.id); ready.value=true; uncertainDelete.value=false }
  catch(e) { if ((e as {response?:{status?:number}}).response?.status===404) { target.value=null; await load() } else deleteError.value=errorText(e,'Profil terbaru belum dapat diperiksa') }
  finally { checking.value=false }
}
async function remove() {
  if (!target.value || !canWrite.value || busy.value || !ready.value || uncertainDelete.value) return
  pending.value=true; deleteError.value=''
  try { await pegawaiApi.remove(target.value.id); target.value=null; notifySuccess(toast,'Pegawai dihapus dari daftar'); await load() }
  catch(e) { deleteError.value=errorText(e,'Pegawai belum berhasil dihapus'); uncertainDelete.value=ambiguous(e) }
  finally { pending.value=false }
}
function askLeave() { return new Promise<boolean>(resolve => confirm.require({header:'Perubahan belum disimpan',message:'Perubahan profil pada form ini belum disimpan. Tinggalkan halaman?',acceptLabel:'Tinggalkan halaman',rejectLabel:'Tetap di sini',acceptProps:{severity:'danger'},accept:()=>resolve(true),reject:()=>resolve(false),onHide:()=>resolve(false)})) }
function beforeUnload(event: BeforeUnloadEvent) { if (saving.value || pending.value || dirty.value) { event.preventDefault(); event.returnValue='' } }
onBeforeRouteLeave(async () => !saving.value && !pending.value && (!dirty.value || await askLeave()))
onMounted(() => { void load(); window.addEventListener('beforeunload',beforeUnload) })
onBeforeUnmount(() => window.removeEventListener('beforeunload',beforeUnload))
</script>
<template>
  <PageLayout title="Data pegawai" subtitle="Kelola profil, masa kerja, dan status pegawai sekolah." :surface="false"><template #actions><Button v-if="canWrite" label="Tambah pegawai" :disabled="busy" @click="create"><template #icon><Icon name="plus" /></template></Button></template>
    <section class="employee-panel" aria-label="Daftar pegawai" :aria-busy="loading">
      <header class="employee-heading"><div><h2>Direktori pegawai</h2><p>{{ rows.filter(row=>row.status==='aktif').length }} aktif, {{ rows.filter(row=>row.status==='cuti').length }} cuti, dari {{ rows.length }} pegawai. Hanya pegawai Aktif yang masuk daftar absensi harian.</p></div><Button label="Muat ulang daftar" severity="secondary" :disabled="busy" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></header>
      <div class="employee-toolbar"><div class="employee-field employee-search"><label for="staff-search">Cari pegawai</label><SearchField input-id="staff-search" v-model="query" placeholder="Nama, NIP, jabatan, atau telepon" hint="Mencari seluruh pegawai yang dimuat" /></div><div class="employee-field"><label for="staff-status">Status pegawai</label><Select input-id="staff-status" v-model="status" :options="[{label:'Semua status',value:null},...employeeStatuses]" option-label="label" option-value="value" placeholder="Semua status"><template #dropdownicon><Icon name="caret-down" /></template></Select></div></div>
      <div v-if="actionError" class="employee-notice"><Message severity="error" :closable="false">{{ actionError }}</Message></div>
      <div class="employee-results"><p role="status">{{ loading?'Memuat pegawai…':error?'Daftar belum tersedia':`${filtered.length?first+1:0}–${Math.min(first+15,filtered.length)} dari ${filtered.length} pegawai` }}</p><Button v-if="hasFilter" label="Hapus filter" severity="secondary" text @click="reset" /></div>
      <div v-if="loading" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan direktori pegawai</p></div>
      <div v-else-if="error" class="employee-empty"><Icon name="warning-circle" /><h3>Daftar pegawai belum dapat ditampilkan</h3><p role="alert">{{ error }}</p><Button label="Coba muat ulang pegawai" severity="secondary" @click="load" /></div>
      <div v-else-if="!filtered.length" class="employee-empty"><Icon :name="hasFilter?'magnifying-glass':'users'" /><h3>{{ hasFilter?'Tidak ada pegawai yang cocok':'Belum ada data pegawai' }}</h3><p>{{ hasFilter?'Coba kata pencarian atau status lain.':'Tambahkan profil untuk mulai mencatat absensi dan penggajian.' }}</p><Button v-if="hasFilter||canWrite" :label="hasFilter?'Hapus filter':'Tambah pegawai'" severity="secondary" @click="hasFilter?reset():create()" /></div>
      <template v-else>
        <table class="employee-table"><caption class="employee-sr-only">Direktori pegawai, 15 pegawai per halaman</caption><thead><tr><th>Pegawai</th><th>Kontak</th><th>Masa kerja</th><th>Status dan akun</th><th class="employee-action-column">Tindakan</th></tr></thead><tbody><tr v-for="row in pageRows" :key="row.id"><td><strong>{{ row.nama }}</strong><small>{{ row.jabatan || 'Jabatan belum dicatat' }}</small><small>{{ row.nip ? `NIP ${row.nip}` : 'NIP belum dicatat' }}</small></td><td>{{ row.nomor_hp || 'Belum dicatat' }}</td><td>{{ staffPeriod(row) }}</td><td><Tag :value="employeeStatus(row).label" :severity="employeeStatus(row).severity" /><small>{{ row.user ? 'Akun terhubung' : 'Tanpa akun aplikasi' }}</small></td><td class="employee-action-column"><div v-if="canWrite" class="employee-row-actions"><Button label="Ubah" severity="secondary" :aria-label="`Ubah ${row.nama}`" :disabled="busy" @click="edit(row)" /><Button severity="secondary" text :aria-label="`Tindakan ${row.nama}`" aria-haspopup="menu" aria-controls="staff-actions" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="menuTarget=row;menu?.toggle($event)"><template #icon><Icon name="caret-down" /></template></Button></div></td></tr></tbody></table>
        <ul class="employee-cards" aria-label="Daftar pegawai"><li v-for="row in pageRows" :key="row.id"><header><div><strong>{{ row.nama }}</strong><small>{{ row.jabatan || 'Jabatan belum dicatat' }}</small></div><Tag :value="employeeStatus(row).label" :severity="employeeStatus(row).severity" /></header><dl><div><dt>NIP</dt><dd>{{ row.nip || 'Belum dicatat' }}</dd></div><div><dt>Telepon</dt><dd>{{ row.nomor_hp || 'Belum dicatat' }}</dd></div><div><dt>Masa kerja</dt><dd>{{ staffPeriod(row) }}</dd></div><div><dt>Akun aplikasi</dt><dd>{{ row.user?'Akun terhubung':'Belum terhubung' }}</dd></div></dl><div v-if="canWrite" class="employee-card-actions"><Button label="Ubah pegawai" severity="secondary" :aria-label="`Ubah ${row.nama}`" :disabled="busy" @click="edit(row)" /><Button label="Tindakan" severity="secondary" text :aria-label="`Tindakan ${row.nama}`" aria-haspopup="menu" aria-controls="staff-actions" :aria-expanded="menuOpen&&menuTarget?.id===row.id" :disabled="busy" @click="menuTarget=row;menu?.toggle($event)"><template #icon><Icon name="caret-down" /></template></Button></div></li></ul>
        <BeePaginator v-model:first="first" :rows="15" :total-records="filtered.length" :always-show="filtered.length>15" />
      </template>
      <p class="employee-footnote"><Icon name="info" />Nonaktifkan pegawai yang sudah tidak bertugas agar riwayat tetap mudah ditemukan. <RouterLink to="/absensi-pegawai">Buka absensi pegawai</RouterLink></p>
    </section>
    <Menu id="staff-actions" ref="menu" :model="items" class="employee-action-menu" popup @show="menuOpen=true" @hide="menuOpen=false"><template #item="{item,props:itemProps}"><a v-bind="itemProps.action"><Icon v-if="item.icon" :name="item.icon" /><span>{{ item.label }}</span></a></template></Menu>
    <PegawaiFormDialog v-model="formOpen" :row="editing" :saving="saving" :error="formError" :uncertain="uncertainSave" @save="save" @dirty="dirty=$event" @review="formOpen=false;load()" />
    <EmployeeActionDialog :visible="!!target" title="Hapus pegawai dari daftar?" :label="target?.nama||''" :amount="target?.nip?`NIP ${target.nip}`:'NIP belum dicatat'" description="Pegawai akan dikeluarkan dari direktori dan pilihan pegawai. Jika hanya berhenti bertugas, ubah status menjadi Nonaktif agar profil tetap mudah ditemukan. Penghapusan profil tidak menghapus akun aplikasi yang tertaut." confirm-label="Hapus pegawai" danger :pending="pending" :checking="checking" :error="deleteError" :uncertain="uncertainDelete" :ready="ready" @close="target=null" @confirm="remove" @refresh="refreshDelete" />
  </PageLayout>
</template>
