<script setup lang="ts">
import BeePaginator from '@/shared/components/BeePaginator.vue';
import { computed, ref, watch } from 'vue';
import Button from 'primevue/button';
import Icon from './PhosphorIcon.vue';
import { formatRp } from '@/core/format';
import type { KateringRekapRow } from '@/features/katering/api';
import type { JemputanRekapRow } from '@/features/jemputan/api';
const props = defineProps<{
    kind: 'katering' | 'jemputan';
    rows: KateringRekapRow[] | JemputanRekapRow[];
    loading: boolean;
    error: string;
    filtered: boolean;
}>();
const emit = defineEmits<{
    retry: [
    ];
    clearSearch: [
    ];
}>();
const first = ref(0);
const columns = computed(() => props.kind === 'katering' ? ['Senin–Kamis', 'Jumat', 'Total hari'] : ['Datang', 'Pulang']);
const rows = computed(() => props.rows.map(row => 'hariKatering' in row ? {
    id: row.siswaId, nama: row.nama, nis: row.nis, detail: row.kelompok,
    counts: [row.hariSenKam, row.hariJumat, row.hariKatering], rates: [`Senin–Kamis ${formatRp(row.tarifSenKam)}`, `Jumat ${formatRp(row.tarifJumat)}`], total: row.total,
} : {
    id: row.siswaId, nama: row.nama, nis: row.nis, detail: row.armada,
    counts: [row.jemputDatang, row.jemputPulang], rates: [`${formatRp(row.tarifPerTrip)} / perjalanan`], total: row.totalNominal,
}));
const pageRows = computed(() => rows.value.slice(first.value, first.value + 15));
const total = computed(() => rows.value.reduce((sum, row) => sum + Math.round(row.total * 100), 0) / 100);
watch(() => props.rows, () => {
    first.value = 0;
});
</script>
<template>
<div class="service-recap" :aria-busy="loading">
  <div v-if="loading" class="service-empty" role="status">
    <Icon name="arrows-clockwise" />
    <p>Memuat seluruh catatan dan tarif pada cakupan ini…</p>
  </div>
  <div v-else-if="error" class="service-empty">
    <Icon name="warning-circle" />
    <h3>Rekap belum dapat ditampilkan</h3>
    <p role="alert">{{ error }}</p><Button label="Muat ulang rekap" severity="secondary"
      @click="emit('retry')" />
  </div>
  <div v-else-if="!rows.length" class="service-empty">
    <Icon name="users" />
    <h3>{{ filtered ? 'Tidak ada siswa yang cocok' : 'Belum ada data layanan pada cakupan ini' }}</h3>
    <p>
      {{ filtered ? 'Coba nama, NIS, kelompok, atau armada lain.' : 'Periksa cakupan, pendaftaran layanan, dan catatan absensi siswa.' }}
    </p><Button v-if="filtered" label="Hapus pencarian" severity="secondary" @click="emit('clearSearch')" />
  </div>
  <template v-else>
    <div class="service-result-count" role="status">{{ first + 1 }}–{{ Math.min(first + 15, rows.length) }}
      dari {{ rows.length }} siswa</div>
    <table class="service-recap-table">
      <caption class="service-caption">Rekap {{ kind }}. Angka layanan dihitung dari catatan absensi, nominal
        dalam rupiah.</caption>
      <thead>
        <tr>
          <th scope="col">Siswa dan {{ kind === 'katering' ? 'kelompok' : 'armada' }}</th>
          <th v-for="column in columns" :key="column" scope="col" class="numeric">{{ column }}</th>
          <th scope="col">Tarif {{ kind === 'katering' ? 'per hari' : 'per perjalanan' }}</th>
          <th scope="col" class="numeric">Jumlah</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in pageRows" :key="row.id">
          <th scope="row"><strong>{{ row.nama }}</strong><small>{{ row.nis || 'NIS belum diisi' }} ·
              {{ row.detail }}</small></th>
          <td v-for="(count, index) in row.counts" :key="index" class="numeric">{{ count }}</td>
          <td><small v-for="rate in row.rates" :key="rate">{{ rate }}</small></td>
          <td class="numeric service-money">{{ formatRp(row.total) }}</td>
        </tr>
      </tbody>
    </table>
    <ul class="service-recap-cards">
      <li v-for="row in pageRows" :key="row.id">
        <strong>{{ row.nama }}</strong><small>{{ row.nis || 'NIS belum diisi' }} · {{ row.detail }}</small>
        <dl>
          <div v-for="(count,index) in row.counts" :key="index">
            <dt>{{ columns[index] }}</dt>
            <dd>{{ count }} {{ kind === 'katering' ? 'hari' : 'perjalanan' }}</dd>
          </div>
        </dl>
        <p><small v-for="rate in row.rates" :key="rate">{{ rate }}</small></p>
        <div class="service-card-total"><span>Jumlah</span><strong>{{ formatRp(row.total) }}</strong></div>
      </li>
    </ul>
    <BeePaginator v-if="rows.length > 15" v-model:first="first" :rows="15" :total-records="rows.length" />
    <div class="service-total"><span>Total {{ filtered ? 'hasil pencarian' : 'rekap' }} · {{ rows.length }}
        siswa</span><strong>{{ formatRp(total) }}</strong></div>
  </template>
</div>
</template>
<style scoped>
.service-recap {
  container: service-recap / inline-size;
  min-width: 0
}

.service-recap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--bee-type-ui)
}

th,
td {
  padding: var(--bee-space-4) var(--bee-space-5);
  border-bottom: 1px solid var(--app-border);
  text-align: start;
  vertical-align: middle
}

thead th {
  background: var(--bee-color-surface-subtle);
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption);
  font-weight: 500
}

tbody th {
  font-weight: 400;
  min-width: 160px
}

.numeric {
  text-align: end;
  font-variant-numeric: tabular-nums
}

.service-money {
  white-space: nowrap;
  font-weight: 500
}

strong {
  font-weight: 500
}

small {
  display: block;
  font-size: var(--bee-type-caption);
  color: var(--app-text-muted);
  margin-top: var(--bee-space-1);
  overflow-wrap: anywhere
}

.service-recap-cards {
  display: none;
  list-style: none;
  margin: 0;
  padding: 0
}

.service-recap-cards li {
  padding: var(--bee-space-4);
  border-bottom: 1px solid var(--app-border)
}

dl {
  display: grid;
  gap: var(--bee-space-3);
  margin: var(--bee-space-5) 0
}

dl>div,
.service-card-total {
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

.service-card-total {
  border-top: 1px solid var(--app-border);
  padding-top: var(--bee-space-3)
}

@container service-recap (max-width:800px) {
  .service-recap-table {
    display: none
  }

  .service-recap-cards {
    display: block
  }
}
</style>
