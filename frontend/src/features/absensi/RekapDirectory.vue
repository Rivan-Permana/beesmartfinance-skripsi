<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Button from 'primevue/button';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Paginator from 'primevue/paginator';
import Icon from '@/shared/components/PhosphorIcon.vue';
import type { RekapAbsensiRow } from './api';
import { attendanceDays } from './presentation';
const props = defineProps<{
    rows: RekapAbsensiRow[];
    loading?: boolean;
    error?: string;
    filtered?: boolean;
}>();
const emit = defineEmits<{
    retry: [
    ];
    showAll: [
    ];
}>();
const first = ref(0);
const pageRows = computed(() => props.rows.slice(first.value, first.value + 20));
const statuses = [{ key: 'hadir', label: 'Hadir' }, { key: 'izin', label: 'Izin' }, { key: 'sakit', label: 'Sakit' }, { key: 'tidak_hadir', label: 'Tidak hadir' }] as const;
const services = [{ key: 'katering', label: 'Katering' }, { key: 'jemput_datang', label: 'Jemput datang' }, { key: 'jemput_pulang', label: 'Jemput pulang' }] as const;
watch(() => props.rows, () => { first.value = 0; });
</script>
<template>
<div class="recap-directory" :aria-busy="loading">
  <div class="recap-count" role="status">
    {{ loading?'Memuat rekap…':error?'Rekap belum dapat ditampilkan':rows.length?`${first+1}–${Math.min(first+20,rows.length)} dari ${rows.length} siswa`:'0 siswa pada tampilan ini' }}
  </div>
  <div v-if="loading" class="attendance-empty">
    <Icon name="arrows-clockwise" />
    <p>Menyiapkan seluruh catatan pada bulan yang diterapkan.</p>
  </div>
  <div v-else-if="error" class="attendance-empty">
    <Icon name="warning-circle" />
    <h3>Rekap belum berhasil dimuat</h3>
    <p role="alert">{{ error }}</p><Button label="Muat ulang rekap" severity="secondary"
      @click="emit('retry')" />
  </div>
  <div v-else-if="!rows.length" class="attendance-empty">
    <Icon name="users" />
    <h3>{{ filtered?'Belum ada siswa yang cocok':'Belum ada siswa aktif pada kelompok ini' }}</h3>
    <p>
      {{ filtered?'Sesuaikan pencarian atau tampilkan siswa yang belum mempunyai catatan absensi.':'Periksa kelompok dan status siswa yang dipilih.' }}
    </p><Button v-if="filtered" label="Tampilkan semua siswa" severity="secondary" @click="emit('showAll')" />
  </div>
  <template v-else>
    <DataTable class="recap-desktop" :value="pageRows" data-key="siswaId" table-style="min-width:760px">
      <Column header="Siswa dan kelompok"><template #body="{data}"><strong
            class="recap-name">{{ data.nama }}</strong><small
            class="recap-secondary">{{ data.nis||'NIS belum diisi' }} · {{ data.kelompok }}</small><small
            v-if="!attendanceDays(data)" class="recap-secondary">Belum ada catatan</small></template></Column>
      <Column v-for="field in [...statuses,...services]" :key="field.key" :header="field.label"
        header-class="recap-numeric" body-class="recap-numeric"><template #body="{data}"><span
            :class="{'recap-zero':data[field.key]===0}">{{ data[field.key] }}</span></template></Column>
    </DataTable>
    <ul class="recap-mobile">
      <li v-for="row in pageRows" :key="row.siswaId"><strong class="recap-name">{{ row.nama }}</strong><small
          class="recap-secondary">{{ row.nis||'NIS belum diisi' }} · {{ row.kelompok }}</small>
        <p v-if="!attendanceDays(row)" class="recap-secondary">Belum ada catatan; bukan berarti tidak hadir.
        </p>
        <dl class="recap-status-grid">
          <div v-for="field in statuses" :key="field.key">
            <dt>{{ field.label }}</dt>
            <dd>{{ row[field.key] }} <span>hari</span></dd>
          </div>
        </dl>
        <dl class="recap-service-list">
          <div v-for="field in services" :key="field.key">
            <dt>{{ field.label }}</dt>
            <dd>{{ row[field.key] }} hari</dd>
          </div>
        </dl>
      </li>
    </ul>
    <Paginator v-if="rows.length>20" v-model:first="first" :rows="20" :total-records="rows.length"
      :page-link-size="3" template="PrevPageLink PageLinks NextPageLink"><template #prevpagelinkicon>
        <Icon name="caret-left" />
      </template><template #nextpagelinkicon>
        <Icon name="caret-right" />
      </template></Paginator>
  </template>
</div>
</template>
<style scoped>
.recap-directory {
  container: recap-directory / inline-size;
  min-width: 0
}

.recap-count {
  padding: var(--bee-space-4) var(--bee-space-5);
  border-block: 1px solid var(--app-border);
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption)
}

.recap-name {
  font-weight: 500;
  overflow-wrap: anywhere
}

.recap-secondary {
  display: block;
  font-size: var(--bee-type-caption);
  color: var(--app-text-muted);
  margin-top: var(--bee-space-1);
  overflow-wrap: anywhere
}

.recap-directory :deep(.recap-numeric) {
  text-align: end;
  font-variant-numeric: tabular-nums
}

.recap-directory :deep(th.recap-numeric .p-datatable-column-header-content) {
  justify-content: flex-end
}

.recap-directory :deep(.p-datatable-tbody>tr>td) {
  height: var(--bee-size-row-multiline);
  padding-block: var(--bee-space-3)
}

.recap-zero {
  color: var(--app-text-muted)
}

.recap-mobile {
  display: none
}

@container recap-directory (max-width:800px) {
  .recap-desktop {
    display: none
  }

  .recap-mobile {
    display: block;
    list-style: none;
    margin: 0;
    padding: 0
  }

  .recap-mobile li {
    padding: var(--bee-space-4);
    border-bottom: 1px solid var(--app-border)
  }

  .recap-status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--bee-space-4);
    margin: var(--bee-space-5) 0
  }

  .recap-status-grid dt,
  .recap-service-list dt {
    font-size: var(--bee-type-caption);
    color: var(--app-text-muted)
  }

  .recap-status-grid dd {
    margin: var(--bee-space-1) 0 0;
    font-weight: 500;
    font-variant-numeric: tabular-nums
  }

  .recap-status-grid dd span {
    font-weight: 400;
    font-size: var(--bee-type-caption);
    color: var(--app-text-muted)
  }

  .recap-service-list {
    display: grid;
    gap: var(--bee-space-2);
    margin: 0
  }

  .recap-service-list>div {
    display: flex;
    justify-content: space-between;
    gap: var(--bee-space-3)
  }

  .recap-service-list dd {
    margin: 0;
    font-size: var(--bee-type-caption);
    font-variant-numeric: tabular-nums
  }

  .recap-count {
    padding-inline: var(--bee-space-4)
  }
}
</style>
