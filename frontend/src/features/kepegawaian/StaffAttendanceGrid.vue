<script setup lang="ts">
import type { Pegawai } from '@/types/api'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { setStaffStatus, staffChanged, staffNeedsSave, staffStatus, staffStatuses, type StaffAttendanceRow, type StaffStatus } from './staff'
const props = defineProps<{ staff: Pegawai[]; modelValue: Record<number, StaffAttendanceRow>; baseline: Record<number, StaffAttendanceRow>; readonly?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<number, StaffAttendanceRow>] }>()
function choose(id: number, value: StaffStatus) {
  const row = props.modelValue[id]
  if (props.readonly || !row) return
  emit('update:modelValue',{ ...props.modelValue, [id]: setStaffStatus(row,value) })
}
function changed(id: number) { return staffChanged(props.modelValue[id]!,props.baseline[id]!) && staffNeedsSave(props.modelValue[id]!,props.baseline[id]!) }
</script>
<template>
  <div class="staff-attendance-grid">
    <article v-for="person in staff" :key="person.id" class="staff-attendance-row">
      <div class="staff-attendance-person"><strong :id="`staff-attendance-${person.id}`">{{ person.nama }}</strong><small>{{ person.jabatan || 'Jabatan belum dicatat' }}{{ !person.status_aktif?' · Nonaktif':'' }}</small><span :class="{'staff-changed':changed(person.id)}"><Icon :name="changed(person.id)?'pencil-simple':baseline[person.id]?.stored||staffStatus(modelValue[person.id]!)==='none'?'check':'clock'" />{{ changed(person.id)?'Diubah, belum disimpan':baseline[person.id]?.stored?'Catatan tersimpan':staffStatus(modelValue[person.id]!)==='none'?'Tanpa catatan':'Pilihan awal, belum disimpan' }}</span></div>
      <div class="staff-attendance-options" role="group" :aria-labelledby="`staff-attendance-${person.id}`"><button v-for="option in staffStatuses" :key="option.value" type="button" :disabled="readonly" :aria-pressed="staffStatus(modelValue[person.id]!)===option.value" @click="choose(person.id,option.value)">{{ option.label }}</button></div>
      <p v-if="staffStatus(modelValue[person.id]!)==='mixed'" class="staff-mixed">Catatan lama: {{ modelValue[person.id]!.hadir }} hadir, {{ modelValue[person.id]!.izin }} izin, {{ modelValue[person.id]!.sakit }} sakit, {{ modelValue[person.id]!.terlambat }} terlambat. Memilih status baru akan mengganti nilai ini.</p>
    </article>
  </div>
</template>
