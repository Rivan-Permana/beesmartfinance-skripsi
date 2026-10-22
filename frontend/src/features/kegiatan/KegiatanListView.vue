<script setup lang="ts">
import Button from "primevue/button"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"
import { kegiatanApi } from "./api"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { formatLocalDate } from "@/core/format"
import { periodeApi } from "@/features/anggaran-periode/api"
import { coaApi } from "@/features/jurnal/api"
import { filterCoaBeban } from "@/features/coa/filters"
import { pegawaiApi } from "@/features/kepegawaian/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { useAuthStore } from "@/stores/auth"
import KegiatanDirectory from "./KegiatanDirectory.vue"
import KegiatanFormDialog from "./KegiatanFormDialog.vue"
import KegiatanRealisasiDialog from "./KegiatanRealisasiDialog.vue"
import KegiatanReportDialog from "./KegiatanReportDialog.vue"
import { realisasiValid, type RealisasiForm } from "./presentation"
import type { Coa, Kegiatan, LaporanKegiatan, Pegawai, PeriodeAkuntansi } from "@/types/api"
const auth=useAuthStore()
const toast=useToast()
const confirm=useConfirm()
const rows=ref<Kegiatan[]>([])
const coaList=ref<Coa[]>([])
const coaBebanOptions=computed(()=>filterCoaBeban(coaList.value))
const pegawaiList=ref<Pegawai[]>([])
const periodeList=ref<PeriodeAkuntansi[]>([])
const periodeFilter=ref<number|null>(null)
const loading=ref(false)
const loadError=ref("")
const periodError=ref(false)
const canManage=computed(()=>auth.hasRole(["SchoolPrincipal"]))
const canRealisasi=computed(()=>auth.hasRole(["TeacherInCharge","SchoolPrincipal"]))
let loadSequence=0
async function load(){
  const sequence=++loadSequence
  loading.value=true;loadError.value=""
  try {
    const data=await kegiatanApi.listAll(periodeFilter.value?{periode:periodeFilter.value}:{})
    if(sequence===loadSequence)rows.value=data
  } catch {
    if(sequence===loadSequence){rows.value=[];loadError.value="Kegiatan belum berhasil dimuat. Periksa koneksi, lalu coba lagi."}
  } finally {if(sequence===loadSequence)loading.value=false}
}
async function loadPeriods(){
  try{periodeList.value=(await periodeApi.list()).results;periodError.value=false}
  catch{periodError.value=true}
}
async function loadManagementOptions(){
  if(!canManage.value)return
  const [accounts,staff]=await Promise.allSettled([coaApi.list(),pegawaiApi.listAll()])
  if(accounts.status==="fulfilled")coaList.value=accounts.value
  else notifyError(toast,accounts.reason,"Pilihan akun beban belum berhasil dimuat.")
  if(staff.status==="fulfilled")pegawaiList.value=staff.value
  else notifyError(toast,staff.reason,"Daftar penanggung jawab belum berhasil dimuat.")
}
watch(periodeFilter,load)
const dialog=ref(false)
const editing=ref<Kegiatan|null>(null)
const saving=ref(false)
const saveError=ref("")
function openCreate(){if(!canManage.value)return;editing.value=null;saveError.value="";dialog.value=true}
function openEdit(row:Kegiatan){if(!canManage.value)return;editing.value=row;saveError.value="";dialog.value=true}
async function save(payload:Partial<Kegiatan>){
  if(!canManage.value||saving.value)return
  saving.value=true;saveError.value=""
  try {
    if(editing.value){await kegiatanApi.update(editing.value.id,payload);notifySuccess(toast,"Kegiatan diperbarui")}
    else{await kegiatanApi.create(payload);notifySuccess(toast,"Kegiatan berhasil dibuat")}
    dialog.value=false;await load()
  } catch(e){const error=friendlyError(e,"Kegiatan belum berhasil disimpan.");saveError.value=[error.summary,error.detail].filter(Boolean).join(". ")}
  finally{saving.value=false}
}
function confirmDelete(row:Kegiatan){
  if(!canManage.value)return
  confirm.require({header:"Hapus kegiatan?",message:`Hapus ${row.nama}? Kegiatan hanya dapat dihapus jika belum ada realisasi.`,rejectLabel:"Kembali",acceptLabel:"Hapus kegiatan",acceptProps:{severity:"danger"},accept:async()=>{
    try{await kegiatanApi.remove(row.id);notifySuccess(toast,"Kegiatan dihapus");await load()}
    catch(e){notifyError(toast,e,"Kegiatan belum berhasil dihapus.")}
  }})
}
const realisasiDialog=ref(false)
const realisasiTarget=ref<Kegiatan|null>(null)
const realisasiSaving=ref(false)
const realisasiError=ref("")
const realisasiForm=ref<RealisasiForm>({tanggal:new Date(),deskripsi:"",nominal:0})
function openRealisasi(row:Kegiatan){if(!canRealisasi.value)return;realisasiTarget.value=row;realisasiForm.value={tanggal:new Date(),deskripsi:"",nominal:0};realisasiError.value="";realisasiDialog.value=true}
async function saveRealisasi(){
  if(!canRealisasi.value||!realisasiTarget.value||!realisasiValid(realisasiForm.value,realisasiTarget.value)||realisasiSaving.value)return
  realisasiSaving.value=true;realisasiError.value=""
  try{
    const result=await kegiatanApi.realisasi(realisasiTarget.value.id,{tanggal:formatLocalDate(realisasiForm.value.tanggal),deskripsi:realisasiForm.value.deskripsi,nominal:realisasiForm.value.nominal})
    notifySuccess(toast,"Realisasi tercatat",result);realisasiDialog.value=false;await load()
  }catch(e){const error=friendlyError(e,"Realisasi belum terkonfirmasi.");realisasiError.value=[error.summary,error.detail].filter(Boolean).join(". ")}
  finally{realisasiSaving.value=false}
}
const laporanDialog=ref(false)
const laporan=ref<LaporanKegiatan|null>(null)
async function lihatLaporan(row:Kegiatan){try{laporan.value=await kegiatanApi.laporan(row.id)
  if(realisasiTarget.value?.id===row.id)realisasiTarget.value={...realisasiTarget.value,realisasi:laporan.value.realisasi,sisa_pagu:laporan.value.sisa_pagu,rasio_utilisasi:laporan.value.rasio_utilisasi}
  laporanDialog.value=true}catch(e){notifyError(toast,e,"Laporan kegiatan belum berhasil dimuat.")}}
onMounted(()=>Promise.all([load(),loadPeriods(),loadManagementOptions()]))
</script>
<template>
  <PageLayout title="Kegiatan sekolah" :subtitle="canManage?'Tetapkan pagu, kelola kegiatan, dan pantau realisasi anggaran.':'Pantau kegiatan dan catat penggunaan anggaran sesuai pagu.'" :surface="false"><template v-if="canManage" #actions><Button label="Buat kegiatan" @click="openCreate"><template #icon><Icon name="plus" /></template></Button></template>
    <KegiatanDirectory v-model:period="periodeFilter" :rows="rows" :periods="periodeList" :loading="loading" :error="loadError" :period-error="periodError" :can-manage="canManage" :can-record="canRealisasi" @create="openCreate" @edit="openEdit" @remove="confirmDelete" @record="openRealisasi" @report="lihatLaporan" @retry="load" @reload-periods="loadPeriods" />
    <KegiatanFormDialog v-if="canManage" v-model="dialog" :activity="editing" :accounts="coaBebanOptions" :staff="pegawaiList" :periods="periodeList" :saving="saving" :error="saveError" @save="save" @reload-options="loadManagementOptions" />
    <KegiatanRealisasiDialog v-if="canRealisasi" v-model="realisasiDialog" v-model:form="realisasiForm" :target="realisasiTarget" :saving="realisasiSaving" :error="realisasiError" @save="saveRealisasi" @report="realisasiTarget&&lihatLaporan(realisasiTarget)" />
    <KegiatanReportDialog v-model="laporanDialog" :report="laporan" />
  </PageLayout>
</template>
