<script setup lang="ts">
import { computed } from "vue"

import type { AbsenPegawaiStatus, Pegawai } from "@/types/api"

export interface StaffAttendanceRow {
  pegawaiId: number
  status: AbsenPegawaiStatus
}

const props = defineProps<{
  staff: Pegawai[]
  modelValue: Record<number, StaffAttendanceRow>
  readonly?: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: Record<number, StaffAttendanceRow>]
}>()

const OPTIONS: { label: string; value: AbsenPegawaiStatus; short: string }[] = [
  { label: "Hadir", value: "hadir", short: "H" },
  { label: "Izin", value: "izin", short: "I" },
  { label: "Sakit", value: "sakit", short: "S" },
  { label: "Terlambat", value: "terlambat", short: "T" },
]

const rows = computed(() =>
  props.staff.map((p) => ({
    pegawai: p,
    entry: props.modelValue[p.id],
  })),
)

function setStatus(pegawaiId: number, status: AbsenPegawaiStatus) {
  if (props.readonly) return
  const current = props.modelValue[pegawaiId]
  if (!current) return
  emit("update:modelValue", {
    ...props.modelValue,
    [pegawaiId]: { ...current, status },
  })
}
</script>

<template>
  <div class="staff-grid">
    <div v-if="staff.length === 0" class="empty-hint">
      Belum ada pegawai aktif. Bagian Keuangan menambahkan data pegawai di menu
      <strong>Pegawai</strong> terlebih dahulu — setelah itu Admin TU bisa catat absensi
      harian di sini.
    </div>

    <article v-for="{ pegawai, entry } in rows" :key="pegawai.id" class="staff-row">
      <div class="staff-head">
        <strong class="bee-card-name">{{ pegawai.nama }}</strong>
        <span v-if="pegawai.jabatan" class="jabatan">{{ pegawai.jabatan }}</span>
      </div>
      <div class="chips">
        <button
          v-for="opt in OPTIONS"
          :key="opt.value"
          type="button"
          class="chip"
          :class="{ active: entry?.status === opt.value, readonly }"
          :disabled="readonly"
          :title="opt.label"
          @click="setStatus(pegawai.id, opt.value)"
        >
          <span class="chip-short">{{ opt.short }}</span>
          <span class="chip-text">{{ opt.label }}</span>
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.staff-grid {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.empty-hint {
  color: var(--app-text-muted);
  padding: 1rem 0;
}
.staff-row {
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 0.65rem 0.85rem;
  background: var(--app-surface);
}
.staff-head {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
}
.jabatan {
  font-size: 0.8rem;
  color: var(--app-text-muted);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: 1px solid var(--app-border);
  background: transparent;
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
}
.chip-short {
  font-weight: 700;
  min-width: 1rem;
  text-align: center;
}
.chip-text {
  font-weight: 600;
}
.chip.active {
  background: var(--bee-secondary);
  border-color: var(--bee-secondary);
  color: #fff;
}
.chip.readonly {
  cursor: default;
  opacity: 0.85;
}
</style>
