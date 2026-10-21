<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import Button from 'primevue/button';
import Message from 'primevue/message';
import Select from 'primevue/select';
import ToggleSwitch from 'primevue/toggleswitch';
import { friendlyError } from '@/core/errors';
import { siswaApi } from '@/features/siswa/api';
import PageLayout from '@/shared/components/PageLayout.vue';
import SearchField from '@/shared/components/SearchField.vue';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { useTableSearch } from '@/shared/composables/useTableSearch';
import { currentTahunPelajaran, defaultMonthForTa, listTahunPelajaran } from '@/shared/utils/tahunPelajaran';
import { useAuthStore } from '@/stores/auth';
import type { KehadiranSiswa, Kelompok, Siswa } from '@/types/api';
import { buildRekapRows, countDistinctDays, downloadCsv, kelompokApi, kehadiranApi, monthDateRange, rekapAsOfDate, rekapToCsv } from './api';
import RekapDirectory from './RekapDirectory.vue';
import { attendanceDays } from './presentation';
interface Scope {
    ta: string;
    tahun: number;
    bulan: number;
    kelompok: number | null;
    groupLabel: string;
    asOfDate?: string;
}
interface Snapshot {
    scope: Scope;
    students: Pick<Siswa, 'id' | 'nama' | 'nis' | 'kelompok'>[];
    records: KehadiranSiswa[];
}
const auth = useAuthStore(), canFill = computed(() => auth.hasRole(['Administration']));
const taList = listTahunPelajaran(), activeTa = currentTahunPelajaran(), initialMonth = defaultMonthForTa(activeTa);
const ta = ref(activeTa.kode), period = ref(`${initialMonth.tahun}-${String(initialMonth.bulan).padStart(2, '0')}`), group = ref<number | null>(null);
const taOptions = taList.map(item => ({ label: item.isActive ? `${item.kode} (aktif)` : item.kode, value: item.kode }));
const selectedTa = computed(() => taList.find(item => item.kode === ta.value) ?? activeTa);
function monthLabel(tahun: number, bulan: number) { return new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric' }).format(new Date(tahun, bulan - 1, 1)); }
const periods = computed(() => Array.from({ length: 12 }, (_, index) => { const month = (index + 6) % 12 + 1, year = index < 6 ? selectedTa.value.startYear : selectedTa.value.endYear; return { label: monthLabel(year, month), value: `${year}-${String(month).padStart(2, '0')}` }; }));
const options = ref<Kelompok[]>([]), optionsLoading = ref(false), optionsError = ref('');
const scope = ref<Scope>({ ta: activeTa.kode, tahun: initialMonth.tahun, bulan: initialMonth.bulan, kelompok: null, groupLabel: 'Semua kelompok', asOfDate: rekapAsOfDate(initialMonth.bulan, initialMonth.tahun) });
const snapshot = ref<Snapshot | null>(null), loading = ref(false), error = ref(''), formError = ref('');
const onlyWithData = ref(true);
let sequence = 0;
const groupOptions = computed(() => options.value.map(item => ({ label: item.nama, value: item.id })));
const names = computed(() => {
    const result = new Map(options.value.map(item => [item.id, item.nama]));
    for (const student of snapshot.value?.students ?? []) {
        if (student.kelompok && !result.has(student.kelompok))
            result.set(student.kelompok, 'Nama kelompok belum dimuat');
    }
    return result;
});
// shortcut: archives use current profiles/groups; use historical snapshots when the API provides them.
const allRows = computed(() => snapshot.value ? buildRekapRows(snapshot.value.students, names.value, snapshot.value.records, { asOfDate: snapshot.value.scope.asOfDate }) : []);
const { query, filtered: searched } = useTableSearch(allRows, row => [row.nama, row.nis, row.kelompok]);
const rows = computed(() => searched.value.filter(row => !onlyWithData.value || attendanceDays(row) + row.katering + row.jemput_datang + row.jemput_pulang > 0));
const representedIds = computed(() => new Set(rows.value.map(row => row.siswaId)));
const days = computed(() => snapshot.value ? countDistinctDays(snapshot.value.records.filter(record => representedIds.value.has(record.siswa)), snapshot.value.scope.asOfDate) : 0);
const applied = computed(() => snapshot.value?.scope ?? scope.value);
const dirty = computed(() => ta.value !== scope.value.ta || period.value !== `${scope.value.tahun}-${String(scope.value.bulan).padStart(2, '0')}` || group.value !== scope.value.kelompok);
const ready = computed(() => !!snapshot.value && !loading.value && !error.value);
function message(e: unknown, fallback: string) { const result = friendlyError(e, fallback); return [result.summary, result.detail].filter(Boolean).join('. '); }
function changeTa(value: string) { const target = taList.find(item => item.kode === value); if (!target)
    return; ta.value = value; const date = defaultMonthForTa(target); period.value = `${date.tahun}-${String(date.bulan).padStart(2, '0')}`; }
async function loadOptions() { optionsLoading.value = true; optionsError.value = ''; try {
    options.value = await kelompokApi.listAll();
}
catch (e) {
    optionsError.value = message(e, 'Nama kelompok belum berhasil dimuat');
}
finally {
    optionsLoading.value = false;
} }
async function load() {
    const request = ++sequence, current = { ...scope.value, asOfDate: rekapAsOfDate(scope.value.bulan, scope.value.tahun) };
    loading.value = true;
    error.value = '';
    snapshot.value = null;
    scope.value = current;
    try {
        const range = monthDateRange(current.bulan, current.tahun);
        const [students, records] = await Promise.all([siswaApi.listAll({ status: 'aktif', ...(current.kelompok ? { kelompok: current.kelompok } : {}) }), kehadiranApi.listAll({ ...range, ...(current.asOfDate ? { tanggal__lte: current.asOfDate } : {}), ...(current.kelompok ? { kelompok: current.kelompok } : {}) })]);
        if (request === sequence)
            snapshot.value = { scope: current, students, records };
    }
    catch (e) {
        if (request === sequence)
            error.value = message(e, 'Rekap absensi belum berhasil dimuat');
    }
    finally {
        if (request === sequence)
            loading.value = false;
    }
}
function apply() {
    if (loading.value)
        return;
    if (!periods.value.some(item => item.value === period.value)) {
        formError.value = 'Pilih bulan yang sesuai tahun pelajaran.';
        return;
    }
    const [tahun, bulan] = period.value.split('-').map(Number);
    formError.value = '';
    scope.value = { ta: ta.value, tahun: tahun!, bulan: bulan!, kelompok: group.value, groupLabel: group.value ? options.value.find(item => item.id === group.value)?.nama ?? 'Nama kelompok belum dimuat' : 'Semua kelompok' };
    void load();
}
function exportCsv() { if (!ready.value || !rows.value.length || !snapshot.value)
    return; const current = snapshot.value.scope; downloadCsv(`rekap-absensi-${current.tahun}-${String(current.bulan).padStart(2, '0')}.csv`, rekapToCsv(rows.value)); }
onMounted(() => { void loadOptions(); void load(); });
onBeforeUnmount(() => { sequence += 1; });
</script>
<template>
<PageLayout class="recap-page" title="Rekap absensi siswa"
  subtitle="Baca jumlah hari kehadiran, katering, dan jemputan pada bulan yang diterapkan." :surface="false">
  <template #actions>
    <RouterLink v-if="canFill" class="attendance-nav-link" to="/absensi-siswa">
      <Icon name="calendar-plus" />Isi absensi
    </RouterLink><Button label="Muat ulang rekap" severity="secondary" :disabled="loading"
      @click="load"><template #icon>
        <Icon name="arrows-clockwise" />
      </template></Button><Button label="Unduh CSV" severity="secondary" :disabled="!ready||!rows.length"
      @click="exportCsv"><template #icon>
        <Icon name="download" />
      </template></Button>
  </template>
  <section class="attendance-panel">
    <header class="attendance-panel-heading">
      <h2>Pilih cakupan rekap</h2>
      <p>Tahun pelajaran mengikuti Juli–Juni. Bulan yang tersedia sudah sesuai tahun pelajaran.</p>
    </header>
    <form class="attendance-controls" @submit.prevent="apply">
      <div class="attendance-field"><label for="recap-ta">Tahun pelajaran</label><Select input-id="recap-ta"
          :model-value="ta" :options="taOptions" option-label="label" option-value="value"
          @update:model-value="changeTa"><template #dropdownicon>
            <Icon name="caret-down" />
          </template></Select></div>
      <div class="attendance-field"><label for="recap-period">Bulan rekap</label><Select
          input-id="recap-period" v-model="period" :options="periods" option-label="label"
          option-value="value"><template #dropdownicon>
            <Icon name="caret-down" />
          </template></Select></div>
      <div class="attendance-field"><label for="recap-group">Kelompok</label><Select input-id="recap-group"
          v-model="group" :options="groupOptions" option-label="label" option-value="value"
          placeholder="Semua kelompok" show-clear :loading="optionsLoading"><template #dropdownicon>
            <Icon name="caret-down" />
          </template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div><Button label="Terapkan" type="submit" :loading="loading"><template #icon>
          <Icon name="funnel" />
        </template><template #loadingicon>
          <Icon name="arrows-clockwise" class="bee-spin" />
        </template></Button>
    </form>
    <p v-if="dirty" class="attendance-small-note" role="status">Pilihan belum diterapkan. Ringkasan dan CSV
      tetap mengikuti bulan serta kelompok pada hasil.</p>
    <p v-if="formError" class="attendance-small-note attendance-field-error" role="alert">{{ formError }}</p>
    <div v-if="optionsError" class="attendance-notice">
      <Message severity="warn" :closable="false">{{ optionsError }} Catatan tetap ditampilkan; nama kelompok
        dapat dimuat ulang.</Message><Button label="Muat ulang kelompok" severity="secondary"
        :loading="optionsLoading" @click="loadOptions" />
    </div>
  </section>
  <section class="attendance-panel">
    <header class="attendance-panel-heading">
      <div class="attendance-recap-title">
        <div>
          <h2>{{ monthLabel(applied.tahun,applied.bulan) }}</h2>
          <p>TA {{ applied.ta }} · {{ applied.groupLabel }}</p>
        </div><span v-if="ready" class="attendance-recap-total">{{ rows.length }} siswa · {{ days }} hari
          tercatat</span>
      </div>
      <p v-if="!canFill" class="attendance-readonly">
        <Icon name="lock" />Baca saja. Hubungi Admin TU untuk koreksi absensi.
      </p>
      <p class="attendance-recap-explanation">Angka menyatakan jumlah hari, bukan persentase.
        {{ applied.asOfDate?`Bulan ini dihitung sampai ${applied.asOfDate.split('-').reverse().join('/')}.`:'' }}
        Belum ada catatan tidak dianggap tidak hadir.</p>
    </header>
    <div class="recap-display-controls">
      <div class="attendance-field"><label for="recap-search">Cari siswa pada rekap</label>
        <SearchField input-id="recap-search" v-model="query" placeholder="Nama, NIS, atau kelompok"
          hint="Mencari pada seluruh siswa yang sudah dimuat untuk cakupan rekap ini." />
      </div><label class="recap-data-toggle">
        <ToggleSwitch v-model="onlyWithData" input-id="recap-only-data" /><span>Hanya siswa dengan
          catatan</span>
      </label>
    </div>
    <RekapDirectory :rows="rows" :loading="loading" :error="error" :filtered="!!query.trim()||onlyWithData"
      @retry="load" @show-all="query='';onlyWithData=false" />
    <p class="attendance-small-note">Rekap memakai siswa aktif dan kelompok pada profil saat ini, termasuk
      saat membuka arsip. CSV mencakup seluruh hasil pencarian/tampilan, bukan hanya halaman tabel yang
      terbuka.</p>
  </section>
</PageLayout>
</template>
<style src="./attendance.css"></style>
