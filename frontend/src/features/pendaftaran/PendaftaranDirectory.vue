<script setup lang="ts">
import BeePaginator from '@/shared/components/BeePaginator.vue';
import { computed, ref, watch } from 'vue';
import Button from 'primevue/button';
import Tag from 'primevue/tag';
import Icon from '@/shared/components/PhosphorIcon.vue';
import type { PendaftaranSiswa } from '@/types/api';
import { dateLabel, editable, money, statusLabels, statusSeverity } from './presentation';
const props = defineProps<{
    rows: PendaftaranSiswa[];
    names: Map<number, string>;
    loading: boolean;
    error: string;
    filtered: boolean;
    readonly?: boolean;
}>();
const emit = defineEmits<{
    detail: [
        row: PendaftaranSiswa
    ];
    edit: [
        row: PendaftaranSiswa
    ];
    remove: [
        row: PendaftaranSiswa
    ];
    retry: [
    ];
    clear: [
    ];
}>();
const first = ref(0), pageRows = computed(() => props.rows.slice(first.value, first.value + 15));
watch(() => props.rows, () => {
    first.value = 0;
});
function level(row: PendaftaranSiswa) {
    return row.jenjang ? props.names.get(row.jenjang) ?? 'Nama jenjang belum dimuat' : 'Jenjang belum dipilih';
}
</script>
<template>
<div class="admission-directory" :aria-busy="loading">
  <div v-if="loading" class="admission-empty" role="status">
    <Icon name="arrows-clockwise" />
    <p>Memuat seluruh pendaftaran…</p>
  </div>
  <div v-else-if="error" class="admission-empty">
    <Icon name="warning-circle" />
    <h3>Pendaftaran belum dapat ditampilkan</h3>
    <p role="alert">{{ error }}</p><Button label="Muat ulang pendaftaran" severity="secondary"
      @click="emit('retry')" />
  </div>
  <div v-else-if="!rows.length" class="admission-empty">
    <Icon name="users" />
    <h3>{{ filtered?'Tidak ada calon yang cocok':'Belum ada calon siswa' }}</h3>
    <p>
      {{ filtered?'Sesuaikan nama, jenjang, atau status yang dicari.':'Gunakan Daftar calon baru untuk mengisi identitas dan biaya sesuai kesepakatan.' }}
    </p><Button v-if="filtered" label="Hapus filter" severity="secondary" @click="emit('clear')" />
  </div>
  <template v-else>
    <div class="admission-count" role="status">{{ first+1 }}–{{ Math.min(first+15,rows.length) }} dari
      {{ rows.length }} pendaftaran</div>
    <table class="admission-table">
      <caption>Daftar calon dan posisi biaya pendaftaran</caption>
      <thead>
        <tr>
          <th scope="col">Calon dan jenjang</th>
          <th scope="col">Status</th>
          <th scope="col" class="numeric">Total biaya</th>
          <th scope="col" class="numeric">Diterima</th>
          <th scope="col" class="numeric">Sisa</th>
          <th scope="col">Tindakan</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in pageRows" :key="row.id">
          <th scope="row">
            <strong>{{ row.nama_calon }}</strong><small>{{ level(row) }}</small><small>{{ dateLabel(row.tanggal_daftar) }}</small>
          </th>
          <td>
            <Tag :value="statusLabels[row.status]" :severity="statusSeverity[row.status]" /><small
              v-if="row.perlu_rekonsiliasi" class="admission-warning">Perlu dicocokkan</small>
          </td>
          <td class="numeric">{{ row.perlu_rekonsiliasi?'Belum diketahui':money(row.total_biaya) }}</td>
          <td class="numeric">{{ row.perlu_rekonsiliasi?'Belum diketahui':money(row.total_terbayar) }}</td>
          <td class="numeric">{{ row.perlu_rekonsiliasi?'Belum diketahui':money(row.sisa_biaya) }}</td>
          <td><div class="admission-row-actions"><Button label="Rincian" :aria-label="`Rincian ${row.nama_calon}`" severity="secondary"
              @click="emit('detail',row)"><template #icon>
                <Icon name="eye" />
              </template></Button><template v-if="!readonly&&editable(row)"><Button :aria-label="`Ubah ${row.nama_calon}`" title="Ubah calon"
              severity="secondary" text @click="emit('edit',row)"><template #icon>
                <Icon name="pencil-simple" />
              </template></Button><Button :aria-label="`Hapus ${row.nama_calon}`" title="Hapus calon" severity="danger"
              text @click="emit('remove',row)"><template #icon>
                <Icon name="trash" />
              </template></Button></template></div></td>
        </tr>
      </tbody>
    </table>
    <ul class="admission-cards">
      <li v-for="row in pageRows" :key="row.id"><strong>{{ row.nama_calon }}</strong><small>{{ level(row) }} ·
          {{ dateLabel(row.tanggal_daftar) }}</small>
        <Tag :value="statusLabels[row.status]" :severity="statusSeverity[row.status]" />
        <p v-if="row.perlu_rekonsiliasi" class="admission-warning">Perlu dicocokkan dengan bukti. Total,
          penerimaan, dan sisa belum diketahui.</p>
        <dl v-else>
          <div>
            <dt>Total biaya</dt>
            <dd>{{ money(row.total_biaya) }}</dd>
          </div>
          <div>
            <dt>Diterima</dt>
            <dd>{{ money(row.total_terbayar) }}</dd>
          </div>
          <div>
            <dt>Sisa</dt>
            <dd>{{ money(row.sisa_biaya) }}</dd>
          </div>
        </dl><div class="admission-row-actions"><Button label="Rincian" :aria-label="`Rincian ${row.nama_calon}`" severity="secondary"
          @click="emit('detail',row)"><template #icon>
            <Icon name="eye" />
          </template></Button><template v-if="!readonly&&editable(row)"><Button label="Ubah" :aria-label="`Ubah ${row.nama_calon}`"
          severity="secondary" text @click="emit('edit',row)"><template #icon>
            <Icon name="pencil-simple" />
          </template></Button><Button label="Hapus" :aria-label="`Hapus ${row.nama_calon}`" severity="danger" text
          @click="emit('remove',row)"><template #icon>
            <Icon name="trash" />
          </template></Button></template></div>
      </li>
    </ul>
    <BeePaginator v-if="rows.length>15" v-model:first="first" :rows="15" :total-records="rows.length" />
  </template>
</div>
</template>
<style scoped>
.admission-directory {
  container: admission-directory / inline-size;
  min-width: 0
}

.admission-count {
  padding: var(--bee-space-4) var(--bee-space-5);
  border-block: 1px solid var(--app-border);
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption)
}

.admission-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--bee-type-ui)
}

caption {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0)
}

th,
td {
  padding: var(--bee-space-4);
  text-align: start;
  border-bottom: 1px solid var(--app-border)
}

thead {
  background: var(--bee-color-surface-subtle);
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption)
}

th {
  font-weight: 500
}

.numeric {
  text-align: end;
  font-variant-numeric: tabular-nums
}

.admission-table strong {
  font-weight: 500;
  overflow-wrap: anywhere
}

small {
  display: block;
  font-size: var(--bee-type-caption);
  color: var(--app-text-muted);
  margin-top: var(--bee-space-1)
}

.admission-warning {
  color: var(--bee-color-warning)
}

.admission-cards {
  display: none;
  list-style: none;
  padding: 0;
  margin: 0
}

.admission-cards li {
  padding: var(--bee-space-4);
  border-bottom: 1px solid var(--app-border);
  overflow-wrap: anywhere
}

.admission-cards .p-tag {
  margin-top: var(--bee-space-3)
}

dl {
  display: grid;
  gap: var(--bee-space-3);
  margin: var(--bee-space-5) 0
}

dl>div {
  display: flex;
  justify-content: space-between;
  gap: var(--bee-space-3)
}

dt {
  color: var(--app-text-muted)
}

dd {
  margin: 0;
  font-variant-numeric: tabular-nums
}

@container admission-directory (max-width:850px) {
  .admission-table {
    display: none
  }

  .admission-cards {
    display: block
  }
}
</style>
