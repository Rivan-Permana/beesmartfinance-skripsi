<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Message from 'primevue/message'
import { useConfirm } from 'primevue/useconfirm'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { calendarTextMatches, formatLocalDate } from '@/core/format'
import type { Pegawai, PegawaiInput } from '@/types/api'
const props = defineProps<{ row: Pegawai | null; saving: boolean; error: string; uncertain: boolean }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ save: [payload: Partial<PegawaiInput>]; review: []; dirty: [value: boolean] }>()
const confirm = useConfirm()
const form = reactive({ nama: '', nip: '', jabatan: '', nomor_hp: '', alamat: '', status_aktif: true, mulai: null as Date | null, selesai: null as Date | null })
const attempted = ref(false), badStart = ref(false), badEnd = ref(false), initial = ref(''), element = ref<HTMLFormElement | null>(null), errorElement = ref<HTMLElement | null>(null)
const locked = computed(() => props.saving || props.uncertain)
const invalidStart = computed(() => badStart.value || !!form.mulai && !Number.isFinite(form.mulai.getTime()))
const invalidEnd = computed(() => badEnd.value || !!form.selesai && !Number.isFinite(form.selesai.getTime()) || !!form.mulai && !!form.selesai && form.selesai < form.mulai)
const invalid = computed(() => !form.nama.trim() || form.nama.trim().length > 100 || form.nip.length > 20 || form.jabatan.length > 50 || form.nomor_hp.length > 20 || invalidStart.value || invalidEnd.value)
const dirty = computed(() => visible.value && JSON.stringify(form) !== initial.value)
watch(dirty, value => emit('dirty', value))
watch(visible, open => {
  if (!open) return
  const row = props.row
  Object.assign(form, { nama: row?.nama ?? '', nip: row?.nip ?? '', jabatan: row?.jabatan ?? '', nomor_hp: row?.nomor_hp ?? '', alamat: row?.alamat ?? '', status_aktif: row?.status_aktif ?? true, mulai: row?.tanggal_mulai_kerja ? new Date(row.tanggal_mulai_kerja+'T12:00:00') : null, selesai: row?.tanggal_selesai_kerja ? new Date(row.tanggal_selesai_kerja+'T12:00:00') : null })
  attempted.value = false; badStart.value = false; badEnd.value = false; initial.value = JSON.stringify(form)
}, { immediate: true })
watch(() => props.error, async error => { if (error) { await nextTick(); errorElement.value?.focus() } })
function close() {
  if (props.saving) return
  if (!dirty.value || props.uncertain) { visible.value = false; return }
  confirm.require({ header: 'Tutup tanpa menyimpan?', message: 'Perubahan profil pegawai pada form ini belum disimpan.', acceptLabel: 'Tutup tanpa menyimpan', rejectLabel: 'Lanjutkan mengisi', acceptProps: { severity: 'danger' }, accept: () => { visible.value = false } })
}
function dateInput(event: Event, key: 'mulai' | 'selesai') { const valid = calendarTextMatches((event.target as HTMLInputElement).value, form[key]); if (key === 'mulai') badStart.value = !valid; else badEnd.value = !valid }
async function save() {
  if (locked.value) return
  attempted.value = true
  if (invalid.value) { await nextTick(); element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(); return }
  emit('save', { nama: form.nama.trim(), nip: form.nip.trim() || null, jabatan: form.jabatan.trim() || null, nomor_hp: form.nomor_hp.trim() || null, alamat: form.alamat.trim() || null, status_aktif: form.status_aktif, tanggal_mulai_kerja: form.mulai ? formatLocalDate(form.mulai) : null, tanggal_selesai_kerja: form.selesai ? formatLocalDate(form.selesai) : null })
}
</script>
<template>
  <Dialog :visible="visible" @update:visible="value => { if (!value) close() }" :header="row ? 'Ubah data pegawai' : 'Tambah pegawai'" class="employee-form-dialog staff-profile-dialog" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup form pegawai'}"><template #closeicon><Icon name="x" /></template>
    <p class="employee-intro">Profil ini dipakai pada absensi, slip gaji, dan kasbon pegawai.</p>
    <form id="staff-profile" ref="element" novalidate @submit.prevent="save" :aria-busy="saving">
      <fieldset class="employee-form-section" :disabled="locked"><legend>Identitas dan kontak</legend><div class="employee-fields">
        <div class="employee-field employee-full"><label for="staff-name">Nama lengkap (wajib)</label><InputText id="staff-name" v-model="form.nama" maxlength="100" :disabled="locked" :invalid="attempted&&!form.nama.trim()" :aria-invalid="attempted&&!form.nama.trim()" :aria-describedby="attempted&&!form.nama.trim()?'staff-name-error':undefined" fluid /><small v-if="attempted&&!form.nama.trim()" id="staff-name-error" class="employee-field-error">Isi nama lengkap pegawai.</small></div>
        <div class="employee-field"><label for="staff-nip">Nomor induk pegawai (NIP)</label><InputText id="staff-nip" v-model="form.nip" maxlength="20" :disabled="locked" aria-describedby="staff-nip-help" fluid /><small id="staff-nip-help">Opsional. Gunakan nomor yang unik jika diisi.</small></div>
        <div class="employee-field"><label for="staff-position">Jabatan</label><InputText id="staff-position" v-model="form.jabatan" maxlength="50" :disabled="locked" fluid /></div>
        <div class="employee-field employee-full"><label for="staff-phone">Nomor telepon</label><InputText id="staff-phone" v-model="form.nomor_hp" type="tel" maxlength="20" :disabled="locked" fluid /></div>
        <div class="employee-field employee-full"><label for="staff-address">Alamat</label><Textarea id="staff-address" v-model="form.alamat" rows="3" :disabled="locked" fluid /></div>
      </div></fieldset>
      <fieldset class="employee-form-section" :disabled="locked"><legend>Status dan masa kerja</legend><div class="employee-fields">
        <div class="employee-field"><label for="staff-start">Mulai kerja</label><DatePicker :key="locked?'locked':'editable'" input-id="staff-start" v-model="form.mulai" show-button-bar date-format="dd/mm/yy" :disabled="locked" :invalid="attempted&&invalidStart" :input-props="{'aria-invalid':attempted&&invalidStart}" @input="dateInput($event,'mulai')" @update:model-value="badStart=false" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted&&invalidStart" class="employee-field-error">Pilih tanggal mulai yang valid.</small></div>
        <div class="employee-field"><label for="staff-end">Selesai kerja</label><DatePicker :key="locked?'locked':'editable'" input-id="staff-end" v-model="form.selesai" show-button-bar date-format="dd/mm/yy" :disabled="locked" :invalid="attempted&&invalidEnd" :input-props="{'aria-invalid':attempted&&invalidEnd,'aria-describedby':'staff-end-help'}" @input="dateInput($event,'selesai')" @update:model-value="badEnd=false" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small id="staff-end-help" :class="{'employee-field-error':attempted&&invalidEnd}">{{ attempted&&invalidEnd?'Tanggal selesai harus valid dan tidak mendahului tanggal mulai.':'Kosongkan jika belum ada tanggal selesai.' }}</small></div>
        <div class="staff-active employee-full"><div><label for="staff-active">Pegawai aktif</label><p class="employee-small-note">Pegawai nonaktif tidak masuk daftar absensi baru. Riwayat yang sudah dicatat tetap tersedia.</p></div><ToggleSwitch input-id="staff-active" v-model="form.status_aktif" :disabled="locked" /></div>
      </div></fieldset>
      <div class="staff-account"><Icon name="user" /><div><strong>Akun aplikasi</strong><p>{{ row?.user ? 'Akun aplikasi sudah terhubung.' : 'Belum terhubung ke akun aplikasi.' }} Pengaitan akun dikelola oleh administrator; perubahan profil ini tidak mengubah akses akun.</p></div></div>
      <Message v-if="attempted&&invalid" severity="error" :closable="false">Periksa nama dan tanggal kerja sebelum menyimpan.</Message>
      <div v-if="error" ref="errorElement" tabindex="-1"><Message severity="error" :closable="false">{{ error }} Isian tetap ada.</Message></div>
      <Message v-if="uncertain" severity="warn" :closable="false">Hasil penyimpanan belum terkonfirmasi. Periksa daftar pegawai sebelum mencoba kembali.</Message>
    </form>
    <template #footer><Button label="Kembali" severity="secondary" :disabled="saving" @click="close" /><Button v-if="uncertain" label="Periksa daftar pegawai" @click="emit('review')" /><Button v-else :label="row?'Simpan perubahan':'Simpan pegawai'" type="submit" form="staff-profile" :loading="saving" :disabled="saving"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
