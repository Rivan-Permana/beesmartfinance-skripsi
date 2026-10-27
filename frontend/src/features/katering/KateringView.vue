<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { onBeforeRouteLeave, RouterLink } from 'vue-router';
import Button from 'primevue/button';
import Select from 'primevue/select';
import InputNumber from 'primevue/inputnumber';
import Message from 'primevue/message';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import PageLayout from '@/shared/components/PageLayout.vue';
import SearchField from '@/shared/components/SearchField.vue';
import PeriodPicker from '@/shared/components/PeriodPicker.vue';
import Icon from '@/shared/components/PhosphorIcon.vue';
import ServiceRecap from '@/shared/components/ServiceRecap.vue';
import { useTableSearch } from '@/shared/composables/useTableSearch';
import { friendlyError, notifySuccess } from '@/core/errors';
import { formatRp } from '@/core/format';
import { siswaApi } from '@/features/siswa/api';
import { downloadCsv, jenjangApi, kelompokApi, kehadiranApi, monthDateRange } from '@/features/absensi/api';
import type { Jenjang, Kelompok } from '@/types/api';
import { buildKateringRekapFromRecords, kateringRekapToCsv, tarifKateringApi, type KateringRekapRow } from './api';
import { legacyExportApi } from './legacyExport';
import MenuBulanan from './MenuBulanan.vue';
import '@/shared/components/school-services.css';
interface Scope {
    bulan: number;
    tahun: number;
    jenjang: number | null;
    kelompok: number | null;
    label: string;
}
const toast = useToast(), confirm = useConfirm(), tab = ref('rekap'), menuBusy = ref(false);
const bulan = ref(new Date().getMonth() + 1), tahun = ref(new Date().getFullYear()), level = ref<number | null>(null), group = ref<number | null>(null);
const levels = ref<Jenjang[]>([]), groups = ref<Kelompok[]>([]);
const scope = ref<Scope>({ bulan: bulan.value, tahun: tahun.value, jenjang: null, kelompok: null, label: 'Semua jenjang dan kelompok' });
const rows = ref<KateringRekapRow[]>([]), loading = ref(false), error = ref(''), rateError = ref(''), exportError = ref(''), saving = ref(false), exporting = ref(false), loaded = ref(false);
const rate = ref<number | null>(null), friday = ref<number | null>(null), savedRate = ref<number | null>(null), savedFriday = ref<number | null>(null), isDefault = ref(false);
let sequence = 0;
const groupOptions = computed(() => groups.value.filter(row => !level.value || row.jenjang === level.value));
watch(level, () => {
    if (group.value && !groupOptions.value.some(row => row.id === group.value))
        group.value = null;
});
const dirty = computed(() => bulan.value !== scope.value.bulan || tahun.value !== scope.value.tahun || level.value !== scope.value.jenjang || group.value !== scope.value.kelompok);
const rateDirty = computed(() => loaded.value && (rate.value !== savedRate.value || friday.value !== savedFriday.value));
const periodLabel = computed(() => new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric' }).format(new Date(scope.value.tahun, scope.value.bulan - 1, 1)));
const { query, filtered } = useTableSearch(rows, row => [row.nis, row.nama, row.kelompok]);
function message(e: unknown, fallback: string) {
    const value = friendlyError(e, fallback);
    return [value.summary, value.detail].filter(Boolean).join('. ');
}
async function load() {
    const request = ++sequence, current = { ...scope.value };
    loading.value = true;
    loaded.value = false;
    error.value = '';
    rows.value = [];
    rate.value = null;
    friday.value = null;
    try {
        const [students, records, allGroups, allLevels, tariff] = await Promise.all([siswaApi.listAll({ status: 'aktif', ...(current.kelompok ? { kelompok: current.kelompok } : {}) }), kehadiranApi.listAll({ ...monthDateRange(current.bulan, current.tahun), ...(current.kelompok ? { kelompok: current.kelompok } : {}) }), kelompokApi.listAll(), jenjangApi.listAll(), tarifKateringApi.get(current.bulan, current.tahun)]);
        if (request !== sequence)
            return;
        const regular = Number(tariff.tarif_harian), special = Number(tariff.tarif_jumat);
        if (!Number.isFinite(regular) || regular < 0 || !Number.isFinite(special) || special < 0)
            throw new Error('Tarif pada periode ini tidak valid. Periksa data tarif sebelum membaca nominal rekap.');
        levels.value = allLevels;
        groups.value = allGroups;
        const names = new Map(allGroups.map(row => [row.id, row.nama])), allowed = new Set(allGroups.filter(row => !current.jenjang || row.jenjang === current.jenjang).map(row => row.id));
        const roster = students.filter(row => !current.jenjang || !!row.kelompok && allowed.has(row.kelompok)).map(row => ({ id: row.id, nis: row.nis, nama: row.nama, kelompok: row.kelompok ? names.get(row.kelompok) ?? 'Nama kelompok belum dimuat' : 'Belum ada kelompok' }));
        rows.value = buildKateringRekapFromRecords(roster, records, regular, special);
        rate.value = savedRate.value = regular;
        friday.value = savedFriday.value = special;
        isDefault.value = tariff.is_default;
        loaded.value = true;
        rateError.value = '';
    }
    catch (e) {
        if (request === sequence)
            error.value = message(e, 'Rekap katering belum berhasil dimuat');
    }
    finally {
        if (request === sequence)
            loading.value = false;
    }
}
function discard() {
    return new Promise<boolean>(resolve => confirm.require({ header: 'Tarif belum disimpan', message: 'Perubahan tarif akan dibuang. Lanjutkan memuat rekap?', acceptLabel: 'Lanjutkan', rejectLabel: 'Tetap di sini', accept: () => resolve(true), reject: () => resolve(false), onHide: () => resolve(false) }));
}
async function apply(refresh = false) {
    if (loading.value || saving.value || exporting.value)
        return;
    if (rateDirty.value && !await discard())
        return;
    if (!refresh)
        scope.value = { bulan: bulan.value, tahun: tahun.value, jenjang: level.value, kelompok: group.value, label: group.value ? groups.value.find(row => row.id === group.value)?.nama ?? 'Kelompok pilihan' : level.value ? levels.value.find(row => row.id === level.value)?.nama ?? 'Jenjang pilihan' : 'Semua jenjang dan kelompok' };
    await load();
}
async function saveRate() {
    if (saving.value || !loaded.value)
        return;
    if (rate.value == null || friday.value == null || ![rate.value, friday.value].every(value => Number.isFinite(value) && value >= 0)) {
        rateError.value = 'Isi kedua tarif dengan angka nol atau lebih.';
        return;
    }
    saving.value = true;
    rateError.value = '';
    try {
        await tarifKateringApi.set({ periode_bulan: scope.value.bulan, periode_tahun: scope.value.tahun, tarif_harian: rate.value, tarif_jumat: friday.value });
        notifySuccess(toast, 'Tarif katering tersimpan', { detail: periodLabel.value });
        await load();
    }
    catch (e) {
        rateError.value = message(e, 'Tarif belum berhasil disimpan') + '. Input tetap ada. Rekap masih memakai tarif terakhir yang berhasil dimuat.';
    }
    finally {
        saving.value = false;
    }
}
function csv() {
    if (!loaded.value || loading.value || saving.value || !filtered.value.length)
        return;
    downloadCsv(`rekap-katering-${scope.value.tahun}-${String(scope.value.bulan).padStart(2, '0')}.csv`, kateringRekapToCsv(filtered.value));
}
async function legacy() {
    if (!loaded.value || exporting.value || saving.value)
        return;
    exporting.value = true;
    exportError.value = '';
    try {
        await legacyExportApi.katering(scope.value.bulan, scope.value.tahun, `laporan-katering-legacy-${scope.value.tahun}-${String(scope.value.bulan).padStart(2, '0')}.csv`);
    }
    catch (e) {
        exportError.value = message(e, 'CSV format lama belum berhasil diunduh');
    }
    finally {
        exporting.value = false;
    }
}
function beforeUnload(event: BeforeUnloadEvent) {
    if (saving.value || menuBusy.value || rateDirty.value) {
        event.preventDefault();
        event.returnValue = '';
    }
}
onMounted(() => {
    void load();
    window.addEventListener('beforeunload', beforeUnload);
});
onBeforeRouteLeave(async () => !saving.value && !menuBusy.value && (!rateDirty.value || await discard()));
onBeforeUnmount(() => {
    sequence++;
    window.removeEventListener('beforeunload', beforeUnload);
});
</script>
<template>
<PageLayout class="school-service-page" title="Katering"
  subtitle="Periksa penggunaan, atur tarif bulanan, dan siapkan menu bulanan." :surface="false"><template
    #actions>
    <RouterLink class="service-link" to="/absensi-siswa">
      <Icon name="calendar-blank" />Buka absensi
    </RouterLink>
  </template>
  <nav class="service-nav" aria-label="Bagian katering"><button type="button" :aria-pressed="tab==='rekap'"
      :disabled="menuBusy" @click="tab='rekap'">Rekap katering</button><button type="button"
      :aria-pressed="tab==='menu'" :disabled="saving" @click="tab='menu'">Menu bulanan</button></nav>
  <div v-if="tab==='rekap'" class="bee-subpage">
    <section class="service-panel">
      <header class="service-heading">
        <h2>Pilih cakupan rekap</h2>
        <p>Rekap memakai siswa aktif dan seluruh tanggal pada bulan yang diterapkan.</p>
      </header>
      <form class="service-controls" @submit.prevent="apply()">
        <div class="service-field"><label>Periode rekap</label>
          <PeriodPicker v-model:bulan="bulan" v-model:tahun="tahun" />
        </div>
        <div class="service-field"><label for="catering-level">Jenjang</label><Select :key="(loading||saving) ? 'locked' : 'editable'"
            input-id="catering-level" v-model="level" :options="levels" option-label="nama" option-value="id"
            placeholder="Semua jenjang" show-clear :disabled="loading||saving"><template #dropdownicon>
              <Icon name="caret-down" />
            </template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
        <div class="service-field"><label for="catering-group">Kelompok</label><Select :key="(loading||saving) ? 'locked' : 'editable'"
            input-id="catering-group" v-model="group" :options="groupOptions" option-label="nama"
            option-value="id" placeholder="Semua kelompok" show-clear :disabled="loading||saving"><template
              #dropdownicon>
              <Icon name="caret-down" />
            </template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div><Button label="Terapkan" type="submit"
          :disabled="loading||saving||exporting"><template #icon>
            <Icon name="funnel" />
          </template></Button>
      </form>
      <p v-if="dirty" class="service-note" role="status">Pilihan belum diterapkan. Tarif, hasil dan CSV tetap
        mengikuti cakupan yang tertulis pada hasil.</p>
    </section>
    <details v-if="loaded" class="service-panel catering-tariff">
      <summary><span><strong>Tarif {{ periodLabel }}</strong><small>Senin–Kamis {{ formatRp(savedRate) }} /
            hari · Jumat {{ formatRp(savedFriday) }} / hari</small></span><span
          class="tariff-disclosure-label">Atur tarif
          <Icon name="caret-down" />
        </span></summary>
      <header class="service-heading">
        <h2>Atur tarif {{ periodLabel }}</h2>
        <p>
          {{ isDefault?'Tarif bawaan digunakan karena periode ini belum memiliki tarif tersimpan.':'Tarif tersimpan untuk periode ini.' }}
          Perubahan angka baru berlaku pada rekap setelah berhasil disimpan.</p>
      </header>
      <form class="service-controls" @submit.prevent="saveRate">
        <div class="service-field"><label for="catering-rate">Senin–Kamis / hari</label>
          <InputNumber input-id="catering-rate" v-model="rate" locale="id-ID" :min="0"
            :max-fraction-digits="2" :disabled="saving" :invalid="!!rateError"
            :input-props="{'aria-describedby':rateError?'catering-rate-error':undefined}" fluid />
        </div>
        <div class="service-field"><label for="catering-friday">Jumat / hari</label>
          <InputNumber input-id="catering-friday" v-model="friday" locale="id-ID" :min="0"
            :max-fraction-digits="2" :disabled="saving" :invalid="!!rateError"
            :input-props="{'aria-describedby':rateError?'catering-rate-error':undefined}" fluid />
        </div><Button label="Simpan tarif" type="submit" :loading="saving"
          :disabled="saving||!rateDirty"><template #icon>
            <Icon name="floppy-disk" />
          </template></Button>
      </form>
      <div v-if="rateError" id="catering-rate-error" class="service-notice">
        <Message severity="error" :closable="false">{{ rateError }}</Message>
      </div>
      <p v-if="rateDirty" class="service-note" role="status">Tarif belum disimpan. Nominal pada hasil dan CSV
        belum berubah.</p>
    </details>
    <section class="service-panel">
      <header class="service-heading">
        <h2>{{ periodLabel }}</h2>
        <p>{{ scope.label }}. Hari Senin–Kamis × tarif harian, ditambah hari Jumat × tarif Jumat. Sabtu/Minggu
          tidak dihitung.</p>
      </header>
      <div class="service-toolbar">
        <div class="service-field"><label for="catering-search">Cari siswa pada rekap</label>
          <SearchField input-id="catering-search" v-model="query" placeholder="Nama, NIS, atau kelompok"
            hint="Mencari pada seluruh hasil yang dimuat, termasuk halaman lain." />
        </div>
        <div class="menu-day-actions"><Button label="Muat ulang rekap" severity="secondary"
            :disabled="loading||saving||exporting" @click="apply(true)"><template #icon>
              <Icon name="arrows-clockwise" />
            </template></Button><Button label="Unduh CSV" severity="secondary"
            :disabled="!loaded||saving||!filtered.length" @click="csv"><template #icon>
              <Icon name="download" />
            </template></Button><Button label="CSV format lama" severity="secondary" text
            :disabled="!loaded||saving||exporting" :loading="exporting" @click="legacy" /></div>
      </div>
      <div v-if="exportError" class="service-notice">
        <Message severity="error" :closable="false">{{ exportError }}</Message>
      </div>
      <ServiceRecap kind="katering" :rows="filtered" :loading="loading" :error="error"
        :filtered="!!query.trim()" @retry="apply(true)" @clear-search="query=''" />
      <p class="service-note service-recap-note">Hari layanan berasal dari penanda ikut katering pada absensi.
        Rekap merupakan perhitungan, bukan bukti tagihan sudah dibuat atau dibayar. CSV mengikuti pencarian;
        CSV format lama memakai cakupan endpoint bulanan TK A/TK B dan mengabaikan filter serta pencarian
        layar.</p>
    </section>
  </div>
  <div v-else class="bee-subpage"><MenuBulanan @busy="menuBusy=$event" /></div>
</PageLayout>
</template>
<style scoped>
.catering-tariff summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--bee-space-3);
  padding: var(--bee-space-4) var(--bee-space-5);
  min-height: 64px;
  cursor: pointer;
  list-style: none
}

.catering-tariff summary::-webkit-details-marker {
  display: none
}

.catering-tariff summary strong {
  font-weight: 500;
  font-size: var(--bee-type-ui)
}

.catering-tariff summary small {
  display: block;
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption);
  margin-top: var(--bee-space-1)
}

.tariff-disclosure-label {
  display: flex;
  gap: var(--bee-space-2);
  align-items: center;
  font-size: var(--bee-type-ui);
  color: var(--bee-color-brand)
}

.catering-tariff[open] summary {
  border-bottom: 1px solid var(--app-border)
}

.catering-tariff[open] summary .bee-icon {
  transform: rotate(180deg)
}

.menu-day-actions {
  display: flex;
  align-items: center;
  gap: var(--bee-space-2);
  flex-wrap: wrap
}

.service-recap-note {
  padding-top: var(--bee-space-4)
}
</style>
