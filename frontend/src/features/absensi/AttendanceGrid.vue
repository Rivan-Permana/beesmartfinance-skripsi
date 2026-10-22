<script setup lang="ts">
import { computed } from 'vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import Icon from '@/shared/components/PhosphorIcon.vue';
import type { Siswa } from '@/types/api';
import { attendanceChanged, attendanceStatuses, invalidServices, serviceFlags, type AttendanceRow } from './presentation';
export type { AttendanceRow } from './presentation';
const props = defineProps<{
    students: Siswa[];
    modelValue: Record<number, AttendanceRow>;
    baseline?: Record<number, AttendanceRow>;
    readonly?: boolean;
    failedIds?: number[];
}>();
const emit = defineEmits<{
    'update:modelValue': [
        value: Record<number, AttendanceRow>
    ];
    delete: [
        siswaId: number
    ];
}>();
const rows = computed(() => props.students.map(siswa => ({ siswa, entry: props.modelValue[siswa.id] })));
function patch(siswaId: number, change: Partial<AttendanceRow>) {
    if (props.readonly)
        return;
    const current = props.modelValue[siswaId];
    if (!current)
        return;
    const next = { ...current, ...change };
    if (next.status !== 'hadir') {
        next.ikut_katering = false;
        next.jemput_datang = false;
        next.jemput_pulang = false;
    }
    emit('update:modelValue', { ...props.modelValue, [siswaId]: next });
}
function state(row: AttendanceRow) {
    if (props.failedIds?.includes(row.siswaId))
        return { label: 'Periksa kembali', severity: 'warn' };
    if (invalidServices(row))
        return { label: 'Periksa layanan', severity: 'warn' };
    if (!row.existingId)
        return { label: 'Belum disimpan', severity: 'secondary' };
    if (props.baseline && attendanceChanged(row, props.baseline[row.siswaId]))
        return { label: 'Belum disimpan', severity: 'warn' };
    return { label: 'Tersimpan', severity: 'success' };
}
</script>
<template>
<div class="attendance-grid">
  <p v-if="!students.length" class="attendance-no-students">Tidak ada siswa aktif pada kelompok ini.</p>
  <article v-for="{siswa,entry} in rows" :key="siswa.id" class="attendance-student"
    :aria-label="`Absensi ${siswa.nama}`">
    <template v-if="entry">
      <div class="attendance-person">
        <strong>{{ siswa.nama }}</strong><small>{{ siswa.nis||'NIS belum diisi' }}</small>
        <Tag :value="state(entry).label" :severity="state(entry).severity" />
      </div>
      <div class="attendance-choices"><span class="attendance-section-label">Kehadiran</span>
        <div class="attendance-status-buttons" role="group" :aria-label="`Kehadiran ${siswa.nama}`"><button
            v-for="status in attendanceStatuses" :key="status.value" type="button"
            :aria-label="`${status.label} untuk ${siswa.nama}`" :aria-pressed="entry.status===status.value"
            :disabled="readonly" @click="patch(siswa.id,{status:status.value})">
            <Icon name="check" :style="{visibility:entry.status===status.value?'visible':'hidden'}" />
            {{ status.label }}
          </button></div>
      </div>
      <div class="attendance-services"><span class="attendance-section-label">Layanan hari ini</span>
        <div class="attendance-service-fields"><label v-for="flag in serviceFlags" :key="flag.key"
            :class="{'attendance-service-disabled':entry.status!=='hadir'}"><input type="checkbox"
              :checked="entry.status==='hadir'&&entry[flag.key]" :disabled="readonly||entry.status!=='hadir'"
              :aria-label="`${flag.label} untuk ${siswa.nama}`"
              @change="patch(siswa.id,{[flag.key]:($event.target as HTMLInputElement).checked})"><span>{{ flag.label }}</span></label>
        </div><small v-if="entry.status!=='hadir'">Katering dan jemputan dinonaktifkan saat tidak
          hadir.</small>
      </div>
      <Button v-if="entry.existingId" class="attendance-delete" severity="danger" text :disabled="readonly"
        :aria-label="`Hapus absensi ${siswa.nama}`" @click="emit('delete',siswa.id)"><template #icon>
          <Icon name="trash" />
        </template></Button>
    </template>
  </article>
</div>
</template>
<style scoped>
.attendance-grid {
  container: attendance-grid / inline-size;
  min-width: 0
}

.attendance-student {
  display: grid;
  grid-template-columns: minmax(140px, 0.8fr) minmax(300px, 1.6fr) minmax(300px, 1.6fr) 44px;
  gap: var(--bee-space-5);
  padding: var(--bee-space-5);
  border-top: 1px solid var(--app-border);
  align-items: start
}

.attendance-person {
  display: grid;
  justify-items: start;
  gap: var(--bee-space-2);
  min-width: 0
}

.attendance-person strong {
  font-weight: 500;
  overflow-wrap: anywhere
}

.attendance-person small {
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption)
}

.attendance-person .p-tag {
  font-size: 12px
}

.attendance-section-label {
  display: block;
  font-size: var(--bee-type-caption);
  color: var(--app-text-muted);
  margin-bottom: var(--bee-space-2)
}

.attendance-status-buttons {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--bee-space-2)
}

.attendance-status-buttons button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--bee-space-1);
  min-height: 44px;
  border: 1px solid var(--bee-color-control-border);
  border-radius: var(--bee-radius-control);
  background: var(--app-surface);
  color: var(--app-text);
  font: inherit;
  font-size: var(--bee-type-ui);
  padding: var(--bee-space-2);
  cursor: pointer
}

.attendance-status-buttons button[aria-pressed=true] {
  background: var(--bee-color-brand-tint);
  color: var(--bee-color-brand);
  border-color: var(--bee-color-brand);
  font-weight: 500
}

.attendance-status-buttons button:disabled {
  cursor: default
}

.attendance-status-buttons .bee-icon {
  width: 16px;
  height: 16px
}

/* Unchecked options reserve no icon space so labels fit on one line. */
.attendance-status-buttons button[aria-pressed=false] .bee-icon {
  display: none
}

.attendance-service-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 0 var(--bee-space-4)
}

.attendance-service-fields label {
  display: flex;
  align-items: center;
  gap: var(--bee-space-2);
  min-height: 44px;
  cursor: pointer;
  font-size: var(--bee-type-ui)
}

.attendance-service-fields input {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: var(--bee-color-brand);
  flex-shrink: 0
}

.attendance-service-disabled {
  color: var(--app-text-muted);
  cursor: default !important
}

.attendance-services>small {
  display: block;
  font-size: var(--bee-type-caption);
  color: var(--app-text-muted);
  margin-top: var(--bee-space-2)
}

.attendance-delete {
  min-height: 44px;
  min-width: 44px
}

.attendance-no-students {
  padding: var(--bee-space-5);
  text-align: center;
  color: var(--app-text-muted)
}

@container attendance-grid (max-width:850px) {
  .attendance-student {
    grid-template-columns: minmax(0, 1fr) 44px;
    gap: var(--bee-space-4);
    padding: var(--bee-space-4)
  }

  .attendance-person {
    grid-column: 1;
    grid-row: 1;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--bee-space-1) var(--bee-space-2)
  }

  .attendance-person strong {
    flex-basis: 100%
  }

  /* Each control already carries the student name in its accessible label. */
  .attendance-section-label {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap
  }

  .attendance-delete {
    grid-column: 2;
    grid-row: 1
  }

  .attendance-choices,
  .attendance-services {
    grid-column: 1/-1
  }

  .attendance-service-fields {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--bee-space-3)
  }
}

@container attendance-grid (max-width:480px) {
  .attendance-student {
    gap: var(--bee-space-3)
  }

  .attendance-service-fields {
    gap: var(--bee-space-2)
  }

  .attendance-service-fields label {
    line-height: 1.2
  }

  /* Pressed state stays visible through fill, border and weight. */
  .attendance-status-buttons button {
    padding-inline: var(--bee-space-1);
    line-height: 1.2;
    text-align: center
  }

  .attendance-status-buttons .bee-icon {
    display: none
  }
}
</style>
