<script setup lang="ts">
import { computed } from "vue"

import type { KehadiranStatus, Siswa } from "@/types/api"

export interface AttendanceRow {
  siswaId: number
  existingId?: number
  status: KehadiranStatus
  ikut_katering: boolean
  jemput_datang: boolean
  jemput_pulang: boolean
}

const props = defineProps<{
  students: Siswa[]
  modelValue: Record<number, AttendanceRow>
  readonly?: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: Record<number, AttendanceRow>]
  delete: [siswaId: number]
}>()

const STATUS_OPTS: { label: string; value: KehadiranStatus; short: string }[] = [
  { label: "Hadir", value: "hadir", short: "H" },
  { label: "Izin", value: "izin", short: "I" },
  { label: "Sakit", value: "sakit", short: "S" },
  { label: "Tidak Hadir", value: "tidak_hadir", short: "TH" },
]

const rows = computed(() =>
  props.students.map((s) => ({
    siswa: s,
    entry: props.modelValue[s.id],
  })),
)

function patch(siswaId: number, patch: Partial<AttendanceRow>) {
  if (props.readonly) return
  const current = props.modelValue[siswaId]
  if (!current) return
  const next = { ...current, ...patch }
  if (patch.status && patch.status !== "hadir") {
    next.ikut_katering = false
    next.jemput_datang = false
    next.jemput_pulang = false
  }
  emit("update:modelValue", { ...props.modelValue, [siswaId]: next })
}

function toggleFlag(
  siswaId: number,
  key: "ikut_katering" | "jemput_datang" | "jemput_pulang",
) {
  if (props.readonly) return
  const current = props.modelValue[siswaId]
  if (!current || current.status !== "hadir") return
  patch(siswaId, { [key]: !current[key] })
}
</script>

<template>
  <div class="attendance-grid">
    <div v-if="students.length === 0" class="empty-hint">
      Tidak ada siswa aktif di kelompok ini.
    </div>

    <article
      v-for="{ siswa, entry } in rows"
      :key="siswa.id"
      class="student-row"
    >
      <div class="student-head">
        <div class="student-head__titles">
          <strong class="bee-card-name">{{ siswa.nama }}</strong>
          <span v-if="siswa.nis" class="nis">{{ siswa.nis }}</span>
        </div>
        <button
          v-if="!readonly && entry?.existingId"
          type="button"
          class="clear-btn"
          title="Hapus absensi hari ini untuk siswa ini"
          @click="emit('delete', siswa.id)"
        >
          Hapus
        </button>
      </div>

      <div class="option-block">
        <span class="bee-field-label">Kehadiran</span>
        <div class="chip-group">
          <button
            v-for="opt in STATUS_OPTS"
            :key="opt.value"
            type="button"
            class="chip"
            :class="{ active: entry?.status === opt.value, readonly }"
            :disabled="readonly"
            :title="opt.label"
            @click="patch(siswa.id, { status: opt.value })"
          >
            <span class="chip-short">{{ opt.short }}</span>
            <span class="chip-text">{{ opt.label }}</span>
          </button>
        </div>
      </div>

      <template v-if="entry?.status === 'hadir'">
        <div class="option-block">
          <span class="bee-field-label">Katering</span>
          <div class="chip-group">
            <button
              type="button"
              class="chip toggle"
              :class="{ active: !entry.ikut_katering, readonly }"
              :disabled="readonly"
              @click="entry.ikut_katering && toggleFlag(siswa.id, 'ikut_katering')"
            >
              Tidak ikut
            </button>
            <button
              type="button"
              class="chip toggle"
              :class="{ active: entry.ikut_katering, readonly }"
              :disabled="readonly"
              @click="!entry.ikut_katering && toggleFlag(siswa.id, 'ikut_katering')"
            >
              Ikut katering
            </button>
          </div>
        </div>

        <div class="option-block jemput-block">
          <span class="bee-field-label">Jemputan antar-jemput</span>
          <div class="jemput-grid">
            <div class="jemput-item">
              <span class="jemput-sublabel">Datang (pagi)</span>
              <div class="chip-group">
                <button
                  type="button"
                  class="chip toggle sm"
                  :class="{ active: !entry.jemput_datang, readonly }"
                  :disabled="readonly"
                  @click="entry.jemput_datang && toggleFlag(siswa.id, 'jemput_datang')"
                >
                  Tidak
                </button>
                <button
                  type="button"
                  class="chip toggle sm"
                  :class="{ active: entry.jemput_datang, readonly }"
                  :disabled="readonly"
                  @click="!entry.jemput_datang && toggleFlag(siswa.id, 'jemput_datang')"
                >
                  Ya, dijemput
                </button>
              </div>
            </div>
            <div class="jemput-item">
              <span class="jemput-sublabel">Pulang (sore)</span>
              <div class="chip-group">
                <button
                  type="button"
                  class="chip toggle sm"
                  :class="{ active: !entry.jemput_pulang, readonly }"
                  :disabled="readonly"
                  @click="entry.jemput_pulang && toggleFlag(siswa.id, 'jemput_pulang')"
                >
                  Tidak
                </button>
                <button
                  type="button"
                  class="chip toggle sm"
                  :class="{ active: entry.jemput_pulang, readonly }"
                  :disabled="readonly"
                  @click="!entry.jemput_pulang && toggleFlag(siswa.id, 'jemput_pulang')"
                >
                  Ya, dijemput
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </article>
  </div>
</template>

<style scoped>
.attendance-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.empty-hint {
  color: var(--app-text-muted);
  padding: 1.5rem;
  text-align: center;
}
.student-row {
  border: 1px solid var(--app-border);
  border-radius: var(--bee-radius-md, 12px);
  padding: 0.85rem 1rem;
  background: var(--app-surface);
}
.student-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.student-head__titles {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
}
.clear-btn {
  border: none;
  background: transparent;
  color: var(--p-red-500, #ef4444);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  padding: 0.2rem 0.4rem;
}
.clear-btn:hover {
  text-decoration: underline;
}
.nis {
  color: var(--app-text-muted);
  font-size: 0.85rem;
}
.option-block {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.65rem;
  margin-top: 0.65rem;
  border-top: 1px dashed var(--app-border);
}
.option-block:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}
.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: 1px solid var(--app-border);
  background: var(--app-bg);
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.chip-short {
  font-weight: 700;
  min-width: 1.25rem;
  text-align: center;
}
.chip-text {
  font-weight: 600;
}
.chip:hover:not(:disabled) {
  border-color: var(--bee-navy);
}
.chip.active {
  background: var(--bee-navy);
  border-color: var(--bee-navy);
  color: #fff;
}
.chip.toggle.active {
  background: var(--bee-green, #2e9e5b);
  border-color: var(--bee-green, #2e9e5b);
  color: #fff;
}
.chip.sm {
  font-size: 0.78rem;
  padding: 0.25rem 0.6rem;
}
.chip.readonly,
.chip:disabled {
  cursor: default;
  opacity: 0.85;
}
.jemput-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: 0.65rem;
}
.jemput-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.55rem 0.65rem;
  background: var(--app-bg);
  border-radius: var(--bee-radius-sm, 8px);
  border: 1px solid var(--app-border);
}
.jemput-sublabel {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--app-text-muted);
}
</style>
