<script setup lang="ts">
import { computed, ref } from "vue"
import Button from "primevue/button"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import Icon from "@/shared/components/PhosphorIcon.vue"
import KegiatanDirectory from "@/features/kegiatan/KegiatanDirectory.vue"
import KegiatanFormDialog from "@/features/kegiatan/KegiatanFormDialog.vue"
import KegiatanRealisasiDialog from "@/features/kegiatan/KegiatanRealisasiDialog.vue"
import KegiatanReportDialog from "@/features/kegiatan/KegiatanReportDialog.vue"
import { realisasiValid, type RealisasiForm } from "@/features/kegiatan/presentation"
import { formatLocalDate } from "@/core/format"
import type { Kegiatan, LaporanKegiatan } from "@/types/api"
import { activityAccounts, activityDetails, activityPeriods, activitySamples, activityStaff } from "./activity-fixtures"
const rows=ref(structuredClone(activitySamples))
const details=ref(structuredClone(activityDetails))
const role=ref<"teacher"|"principal">("teacher")
const period=ref<number|null>(null)
const filtered=computed(()=>rows.value.filter(row=>!period.value||row.periode===period.value))
const toast=useToast()
const confirm=useConfirm()
const dialog=ref(false)
const editing=ref<Kegiatan|null>(null)
const realisasiDialog=ref(false)
const target=ref<Kegiatan|null>(null)
const form=ref<RealisasiForm>({tanggal:new Date(),deskripsi:"",nominal:0})
const reportDialog=ref(false)
const report=ref<LaporanKegiatan|null>(null)
function notify(){toast.add({severity:"success",summary:"Contoh kegiatan diperbarui",detail:"Hanya mengubah data fiktif di halaman ini.",life:4000})}
function create(){editing.value=null;dialog.value=true}
function edit(row:Kegiatan){editing.value=row;dialog.value=true}
function save(payload:Partial<Kegiatan>){
  const current=editing.value??{...activitySamples[1]!,id:Math.max(0,...rows.value.map(row=>row.id))+1}
  const realized=editing.value?Number(current.realisasi):0
  const next={...current,...payload,periode_kode:activityPeriods.find(item=>item.id===payload.periode)?.kode??null,realisasi:realized.toFixed(2),sisa_pagu:((Math.round(Number(payload.pagu)*100)-Math.round(realized*100))/100).toFixed(2),rasio_utilisasi:realized/Number(payload.pagu)}
  rows.value=editing.value?rows.value.map(row=>row.id===current.id?next:row):[...rows.value,next]
  if(!editing.value)details.value[next.id]=[]
  dialog.value=false;notify()
}
function remove(row:Kegiatan){confirm.require({header:"Hapus kegiatan contoh?",message:"Hanya menghapus contoh kegiatan tanpa realisasi ini.",rejectLabel:"Kembali",acceptLabel:"Hapus contoh",acceptProps:{severity:"danger"},accept:()=>{rows.value=rows.value.filter(item=>item.id!==row.id)}})}
function record(row:Kegiatan){target.value=row;form.value={tanggal:new Date(),deskripsi:"",nominal:0};realisasiDialog.value=true}
function saveRealisasi(){
  const current=target.value
  if(!current||!realisasiValid(form.value,current))return
  const cents=Math.round(Number(current.realisasi)*100)+Math.round(form.value.nominal*100)
  rows.value=rows.value.map(row=>row.id!==current.id?row:{...row,realisasi:(cents/100).toFixed(2),sisa_pagu:((Math.round(Number(row.pagu)*100)-cents)/100).toFixed(2),rasio_utilisasi:cents/(Number(row.pagu)*100)})
  details.value[current.id]=[...(details.value[current.id]??[]),{tanggal:formatLocalDate(form.value.tanggal),deskripsi:form.value.deskripsi,nominal:form.value.nominal.toFixed(2)}]
  realisasiDialog.value=false;notify()
}
function showReport(row:Kegiatan){report.value={kegiatan:row.nama,pagu:row.pagu,realisasi:row.realisasi,sisa_pagu:row.sisa_pagu,rasio_utilisasi:row.rasio_utilisasi,rincian:details.value[row.id]??[]};reportDialog.value=true}
function reset(){rows.value=structuredClone(activitySamples);details.value=structuredClone(activityDetails);period.value=null}
</script>
<template>
  <section id="layar-kegiatan" class="system-section"><header class="system-section-heading"><h2>Anggaran jelas, peran tetap berbeda.</h2><p>Guru mencatat realisasi dan membaca laporan. Kepala sekolah juga mengelola kegiatan serta pagunya. Komponen di sini sama dengan aplikasi; pilihan peran hanya mengubah contoh dan tidak mengganti izin akun.</p></header>
    <div class="activity-sample-toolbar"><div class="bee-segmented" role="group" aria-label="Peran contoh kegiatan"><button :aria-pressed="role==='teacher'" @click="role='teacher'">Guru PIC</button><button :aria-pressed="role==='principal'" @click="role='principal'">Kepala sekolah</button></div><Button v-if="role==='principal'" label="Buat kegiatan" @click="create"><template #icon><Icon name="plus" /></template></Button></div>
    <KegiatanDirectory v-model:period="period" :rows="filtered" :periods="activityPeriods" :can-manage="role==='principal'" can-record @create="create" @edit="edit" @remove="remove" @record="record" @report="showReport" />
    <Button class="activity-reset" label="Pulihkan kegiatan contoh" severity="secondary" text @click="reset" />
    <KegiatanFormDialog v-model="dialog" :activity="editing" :accounts="activityAccounts" :staff="activityStaff" :periods="activityPeriods" @save="save" />
    <KegiatanRealisasiDialog v-model="realisasiDialog" v-model:form="form" :target="target" @save="saveRealisasi" @report="target&&showReport(target)" />
    <KegiatanReportDialog v-model="reportDialog" :report="report" />
  </section>
</template>
<style scoped>
.activity-sample-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--bee-space-4); margin-bottom: var(--bee-space-5); }.activity-reset { margin-top: var(--bee-space-3); }
</style>
