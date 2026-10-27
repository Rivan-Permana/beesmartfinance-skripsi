<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, RouterLink } from 'vue-router'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import Message from 'primevue/message'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import PageLayout from '@/shared/components/PageLayout.vue'
import PeriodPicker from '@/shared/components/PeriodPicker.vue'
import SearchField from '@/shared/components/SearchField.vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useTableSearch } from '@/shared/composables/useTableSearch'
import { calendarTextMatches, formatLocalDate } from '@/core/format'
import { notifySuccess } from '@/core/errors'
import { downloadXlsx } from '@/core/export'
import type { AbsenPegawaiRekap, Pegawai } from '@/types/api'
import StaffAttendanceGrid from './StaffAttendanceGrid.vue'
import { absenPegawaiApi, pegawaiApi } from './api'
import { errorText, dateLabel, months } from './payroll'
import { attendanceFields, staffAttendance, staffChanged, staffNeedsSave, type StaffAttendanceRow } from './staff'
import './employee-finance.css'
import './staff.css'
const auth=useAuthStore(), confirm=useConfirm(), toast=useToast()
const canWrite=computed(()=>auth.hasRole(['Administration','Finance']))
const tab=ref('harian'), date=ref<Date|null>(new Date()), badDate=ref(false), attempted=ref(false)
const scope=ref(''), staff=ref<Pegawai[]>([]), roster=ref<Pegawai[]>([])
const attendance=ref<Record<number,StaffAttendanceRow>>({}), baseline=ref<Record<number,StaffAttendanceRow>>({})
const loading=ref(false), saving=ref(false), verifying=ref(false), choosing=ref(false), loadError=ref(''), saveError=ref(''), message=ref(''), needsVerify=ref(false)
const dateString=computed(()=>date.value&&Number.isFinite(date.value.getTime())?formatLocalDate(date.value):'')
const changed=computed(()=>Object.values(attendance.value).some(row=>staffChanged(row,baseline.value[row.pegawai]!)&&staffNeedsSave(row,baseline.value[row.pegawai]!)))
const pendingRows=computed(()=>Object.values(attendance.value).filter(row=>staffNeedsSave(row,baseline.value[row.pegawai]!)))
const locked=computed(()=>saving.value||verifying.value||needsVerify.value)
const {query,filtered}=useTableSearch(roster,row=>[row.nama,row.nip,row.jabatan])
const month=ref(new Date().getMonth()+1),year=ref(new Date().getFullYear()),recapScope=ref(''),recap=ref<AbsenPegawaiRekap[]>([]),recapLoading=ref(false),recapError=ref('')
const {query:recapQuery,filtered:recapRows}=useTableSearch(recap,row=>row.nama)
const byName=(a:{nama:string},b:{nama:string})=>a.nama.localeCompare(b.nama,'id',{sensitivity:'base'})
function ask(text:string) { return new Promise<boolean>(resolve=>confirm.require({header:'Perubahan belum disimpan',message:text,acceptLabel:'Lanjutkan tanpa menyimpan',rejectLabel:'Tetap di sini',acceptProps:{severity:'danger'},accept:()=>resolve(true),reject:()=>resolve(false),onHide:()=>resolve(false)})) }
async function loadDay(target:string) {
  loading.value=true;loadError.value='';saveError.value='';message.value='';scope.value=target;roster.value=[];attendance.value={};baseline.value={};query.value=''
  try {
    const [people,records]=await Promise.all([pegawaiApi.listAll(),absenPegawaiApi.listAll({tanggal:target})])
    staff.value=people
    const byId=new Map(records.map(record=>[record.pegawai,record]))
    roster.value=people.filter(person=>person.status_aktif||byId.has(person.id))
    // Keep recorded people even when their soft-deleted master profile is no longer returned.
    for (const record of records) if(!roster.value.some(person=>person.id===record.pegawai)) roster.value.push({id:record.pegawai,nama:`Pegawai #${record.pegawai}`,nip:null,jabatan:'Profil tidak tersedia',nomor_hp:null,alamat:null,status_aktif:false,tanggal_mulai_kerja:null,tanggal_selesai_kerja:null,user:null})
    roster.value.sort(byName)
    const values:Record<number,StaffAttendanceRow>={}
    for(const person of roster.value) values[person.id]=staffAttendance(person.id,byId.get(person.id))
    attendance.value=values;baseline.value=structuredClone(values);needsVerify.value=false
  } catch(e) { loadError.value=errorText(e,'Daftar absensi belum berhasil dimuat') }
  finally { loading.value=false }
}
async function apply() {
  if(loading.value||locked.value||choosing.value)return
  attempted.value=true
  if(!dateString.value||badDate.value)return
  choosing.value=true
  try { if(changed.value&&!await ask('Menampilkan tanggal lain akan membuang perubahan pada daftar saat ini.'))return;await loadDay(dateString.value) }
  finally { choosing.value=false }
}
async function refresh() {
  if(loading.value||locked.value||!scope.value)return
  if(changed.value&&!await ask('Muat ulang akan mengganti pilihan yang belum disimpan dengan catatan terbaru.'))return
  await loadDay(scope.value)
}
async function verify() {
  if(verifying.value||!scope.value)return
  verifying.value=true
  try {
    const records=await absenPegawaiApi.listAll({tanggal:scope.value}),byId=new Map(records.map(record=>[record.pegawai,record]))
    const actual:Record<number,StaffAttendanceRow>={}
    for(const desired of Object.values(attendance.value)) {
      const record=byId.get(desired.pegawai)
      actual[desired.pegawai]=record?staffAttendance(desired.pegawai,record):{...staffAttendance(desired.pegawai),hadir:0}
    }
    baseline.value=actual;needsVerify.value=false;saveError.value=''
    message.value=pendingRows.value.length?`${pendingRows.value.length} pilihan belum sesuai dengan catatan server. Periksa, lalu simpan sisa perubahan.`:'Seluruh pilihan sudah sesuai dengan catatan server.'
    if(!pendingRows.value.length) notifySuccess(toast,'Absensi pegawai terkonfirmasi',{detail:dateLabel(scope.value)})
  }catch(e){needsVerify.value=true;saveError.value=errorText(e,'Hasil simpan belum dapat diperiksa').replace(/[. ]+$/,'')+'. Pilihan tetap ada; belum ada pengiriman ulang.'}
  finally{verifying.value=false}
}
async function saveDay() {
  if(!canWrite.value||locked.value||loading.value||loadError.value||!scope.value||!pendingRows.value.length)return
  saving.value=true;saveError.value='';message.value=''
  const items=pendingRows.value.map(row=>({pegawai:row.pegawai,hadir:row.hadir,izin:row.izin,sakit:row.sakit,terlambat:row.terlambat}))
  try {
    await absenPegawaiApi.bulkSave(scope.value,items)
    needsVerify.value=true;await verify()
  }catch(e){needsVerify.value=true;saveError.value=errorText(e,'Hasil penyimpanan belum terkonfirmasi').replace(/[. ]+$/,'')+'. Sebagian catatan mungkin sudah tersimpan. Periksa hasil simpan sebelum mencoba kembali.'}
  finally{saving.value=false}
}
async function loadRecap() {
  if(recapLoading.value)return
  const selectedMonth=month.value,selectedYear=year.value
  recapLoading.value=true;recapError.value='';recap.value=[];recapQuery.value='';recapScope.value=`${months[selectedMonth-1]} ${selectedYear}`
  try{recap.value=(await absenPegawaiApi.rekapBulanan(selectedMonth,selectedYear)).map(row=>({...row,nama:recapName(row)})).sort(byName)}catch(e){recapError.value=errorText(e,'Rekap pegawai belum berhasil dimuat')}finally{recapLoading.value=false}
}
function recapName(row:AbsenPegawaiRekap){return staff.value.find(person=>person.id===row.pegawai)?.nama||row.nama}
function exportRecap(){
  const labels={hadir:'Hadir',izin:'Izin',sakit:'Sakit',terlambat:'Terlambat'}
  downloadXlsx(`rekap-absensi-pegawai-${year.value}-${String(month.value).padStart(2,'0')}.xlsx`,`Rekap ${recapScope.value}`,['No','Nama pegawai',...attendanceFields.map(key=>labels[key])],recap.value.map((row,index)=>[index+1,row.nama,...attendanceFields.map(key=>row[key])]))
}
function beforeUnload(event:BeforeUnloadEvent){if(saving.value||needsVerify.value||changed.value){event.preventDefault();event.returnValue=''}}
onBeforeRouteLeave(async()=>{if(saving.value||verifying.value)return false;return !(changed.value||needsVerify.value)||await ask('Pilihan absensi belum tersimpan atau hasilnya belum terkonfirmasi. Tinggalkan halaman?')})
onMounted(()=>{void loadDay(dateString.value);window.addEventListener('beforeunload',beforeUnload)})
onBeforeUnmount(()=>window.removeEventListener('beforeunload',beforeUnload))
</script>
<template>
  <PageLayout title="Absensi pegawai" subtitle="Catat kehadiran per tanggal dan periksa rekap bulanan pegawai." :surface="false"><template #actions><RouterLink class="staff-nav-link" to="/pegawai"><Icon name="users" />Data pegawai</RouterLink></template>
    <Tabs v-model:value="tab" class="staff-tabs"><TabList><Tab value="harian">Absensi harian</Tab><Tab value="rekap">Rekap bulanan</Tab></TabList><TabPanels><TabPanel value="harian">
      <section class="employee-panel staff-day-controls"><header class="employee-heading"><div><h2>Tanggal absensi</h2><p>Tampilkan tanggal yang ingin dicatat. Daftar mencakup pegawai aktif dan pegawai lain yang sudah memiliki catatan pada tanggal tersebut.</p></div></header><form class="employee-toolbar" @submit.prevent="apply"><div class="employee-field"><label for="staff-attendance-date">Tanggal</label><DatePicker :key="locked?'locked':'editable'" input-id="staff-attendance-date" v-model="date" date-format="dd/mm/yy" :disabled="locked" :invalid="attempted&&(!dateString||badDate)" :input-props="{'aria-invalid':attempted&&(!dateString||badDate)}" @input="badDate=!calendarTextMatches(($event.target as HTMLInputElement).value,date)" @update:model-value="badDate=false" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted&&(!dateString||badDate)" class="employee-field-error">Pilih tanggal yang valid.</small></div><Button label="Tampilkan absensi" severity="secondary" type="submit" :disabled="loading||locked||choosing" /></form><p v-if="dateString!==scope||badDate" class="employee-footnote" role="status">Pilihan tanggal belum diterapkan. Simpan tetap mengikuti tanggal daftar di bawah.</p></section>
      <section class="employee-panel staff-roster" :aria-busy="loading||saving"><header class="employee-heading"><div><h2>{{ scope?dateLabel(scope):'Daftar kehadiran' }}</h2><p v-if="!loading&&!loadError">{{ roster.length }} pegawai · {{ Object.values(baseline).filter(row=>row.stored).length }} memiliki catatan tersimpan · {{ needsVerify?'Hasil simpan perlu diperiksa':`${pendingRows.length} belum disimpan` }}</p></div></header>
        <div v-if="loading" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Memuat pegawai dan seluruh catatan pada tanggal ini…</p></div>
        <div v-else-if="loadError" class="employee-empty"><Icon name="warning-circle" /><h3>Daftar absensi belum dapat ditampilkan</h3><p role="alert">{{ loadError }}</p><Button label="Muat ulang absensi" severity="secondary" @click="refresh" /></div>
        <div v-else-if="!roster.length" class="employee-empty"><Icon name="users" /><h3>Belum ada pegawai pada daftar ini</h3><p>Tambahkan pegawai aktif di Data pegawai atau pilih tanggal yang memiliki catatan.</p></div>
        <template v-else>
          <div v-if="saveError" class="employee-notice staff-notice"><Message severity="error" :closable="false">{{ saveError }}</Message></div><p v-if="message" class="staff-saved-note" role="status"><Icon :name="pendingRows.length?'info':'check-circle'" />{{ message }}</p>
          <div class="employee-toolbar staff-search"><div class="employee-field employee-search"><label for="staff-attendance-search">Cari dalam daftar</label><SearchField input-id="staff-attendance-search" v-model="query" placeholder="Nama, NIP, atau jabatan" /></div></div>
          <p class="staff-result-note">{{ filtered.length }} dari {{ roster.length }} pegawai ditampilkan. Simpan mencakup seluruh pilihan, termasuk hasil yang tersembunyi oleh pencarian.</p>
          <div v-if="!filtered.length" class="employee-empty"><h3>Tidak ada pegawai yang cocok</h3><Button label="Hapus pencarian" severity="secondary" @click="query=''" /></div>
          <StaffAttendanceGrid v-else :staff="filtered" v-model="attendance" :baseline="baseline" :readonly="locked||!canWrite" />
          <div class="staff-savebar"><div><strong>{{ needsVerify?'Hasil simpan perlu diperiksa':`${pendingRows.length} catatan belum disimpan` }}</strong><p>Pegawai tanpa catatan disiapkan sebagai Hadir. Periksa semua pilihan sebelum menyimpan.</p></div><div><Button label="Muat ulang catatan" severity="secondary" text :disabled="locked" @click="refresh"><template #icon><Icon name="arrows-clockwise" /></template></Button><Button v-if="needsVerify" label="Periksa hasil simpan" :loading="verifying" :disabled="saving||verifying" @click="verify"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button><Button v-else :label="saving?'Menyimpan…':'Simpan absensi'" :disabled="!canWrite||!pendingRows.length||locked" :loading="saving" @click="saveDay"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></div></div>
          <p class="employee-footnote"><Icon name="info" />Tanpa catatan menghapus catatan tersimpan untuk tanggal ini. Terlambat dicatat terpisah dari Hadir. Perubahan absensi tidak menghitung ulang slip gaji.</p>
        </template>
      </section>
    </TabPanel><TabPanel value="rekap">
      <section class="employee-panel"><header class="employee-heading"><div><h2>Rekap kehadiran bulanan</h2><p>Jumlah mengikuti catatan yang tersimpan. Pegawai tanpa catatan pada bulan terpilih tidak ditampilkan.</p></div></header><form class="employee-toolbar" @submit.prevent="loadRecap"><div class="employee-field"><label>Periode rekap</label><PeriodPicker v-model:bulan="month" v-model:tahun="year" /></div><Button label="Tampilkan rekap" severity="secondary" type="submit" :loading="recapLoading"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></form>
        <div v-if="recapScope" class="employee-heading staff-recap-heading"><div><h2>{{ recapScope }}</h2><p>{{ recap.length }} pegawai memiliki catatan · urut abjad</p></div><Button v-if="!recapLoading&&!recapError&&recap.length" label="Unduh Excel" severity="secondary" :aria-label="`Unduh rekap ${recapScope} sebagai Excel`" @click="exportRecap"><template #icon><Icon name="download" /></template></Button></div>
        <div v-if="recapLoading" class="employee-empty" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><p>Menyiapkan rekap bulanan…</p></div>
        <div v-else-if="recapError" class="employee-empty"><Icon name="warning-circle" /><h3>Rekap belum dapat ditampilkan</h3><p role="alert">{{ recapError }}</p><Button label="Coba muat ulang rekap" severity="secondary" @click="loadRecap" /></div>
        <div v-else-if="!recapScope||!recap.length" class="employee-empty"><Icon name="calendar-blank" /><h3>{{ recapScope?'Belum ada catatan pada periode ini':'Pilih periode untuk melihat rekap' }}</h3><p>{{ recapScope?'Periksa bulan lain atau catat kehadiran pada tab Absensi harian.':'Pilih bulan dan tahun, lalu tampilkan rekap.' }}</p></div>
        <template v-else><div class="employee-toolbar"><div class="employee-field employee-search"><label for="staff-recap-search">Cari pegawai dalam rekap</label><SearchField input-id="staff-recap-search" v-model="recapQuery" placeholder="Nama pegawai" /></div></div><p v-if="!recapRows.length" class="employee-empty">Tidak ada pegawai yang cocok dengan pencarian.</p><template v-else><table class="employee-table"><caption class="employee-sr-only">Jumlah catatan kehadiran pegawai pada {{ recapScope }}</caption><thead><tr><th>Pegawai</th><th v-for="key in attendanceFields" :key="key" class="employee-number">{{ key==='hadir'?'Hadir':key==='izin'?'Izin':key==='sakit'?'Sakit':'Terlambat' }}</th></tr></thead><tbody><tr v-for="row in recapRows" :key="row.pegawai"><td><strong>{{ row.nama }}</strong></td><td v-for="key in attendanceFields" :key="key" class="employee-number">{{ row[key] }}</td></tr></tbody></table><ul class="employee-cards staff-recap-cards" aria-label="Rekap pegawai"><li v-for="row in recapRows" :key="row.pegawai"><strong>{{ row.nama }}</strong><dl><div v-for="key in attendanceFields" :key="key"><dt>{{ key==='hadir'?'Hadir':key==='izin'?'Izin':key==='sakit'?'Sakit':'Terlambat' }}</dt><dd>{{ row[key] }}</dd></div></dl></li></ul></template></template>
        <p class="employee-footnote"><Icon name="info" />Angka menunjukkan jumlah catatan, bukan persentase hari kerja. Tidak ada asumsi hari libur atau perhitungan ulang gaji.</p>
      </section>
    </TabPanel></TabPanels></Tabs>
  </PageLayout>
</template>
