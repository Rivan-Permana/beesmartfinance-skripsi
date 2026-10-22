<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, RouterLink } from 'vue-router';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputNumber from 'primevue/inputnumber';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Select from 'primevue/select';
import Paginator from 'primevue/paginator';
import Message from 'primevue/message';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import { friendlyError, notifySuccess } from '@/core/errors';
import { formatRp } from '@/core/format';
import { JEMPUTAN_TARIF_MINIMAL } from '@/core/config';
import { siswaApi } from '@/features/siswa/api';
import { downloadCsv, kehadiranApi, monthDateRange } from '@/features/absensi/api';
import { legacyExportApi } from '@/features/katering/legacyExport';
import PageLayout from '@/shared/components/PageLayout.vue';
import SearchField from '@/shared/components/SearchField.vue';
import PeriodPicker from '@/shared/components/PeriodPicker.vue';
import ServiceRecap from '@/shared/components/ServiceRecap.vue';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { useTableSearch } from '@/shared/composables/useTableSearch';
import { armadaApi, pendaftaranJemputanApi, buildJemputanRekap, jemputanRekapToCsv, type JemputanRekapRow } from './api';
import type { ArmadaJemputan, PendaftaranJemputan, Siswa } from '@/types/api';
import '@/shared/components/school-services.css';
const toast = useToast(), confirm = useConfirm(), tab = ref('armada');
const fleets = ref<ArmadaJemputan[]>([]), registrations = ref<PendaftaranJemputan[]>([]), students = ref<Siswa[]>([]);
const loading = ref(false), error = ref(''), actionError = ref(''), saving = ref(false), visible = ref(false), editing = ref<number | null>(null), formError = ref(''), attempted = ref(false), uncertain = ref(false);
const formKind = ref<'armada' | 'pendaftaran'>('armada');
const fleetForm = reactive({ nama_supir: '', jenis_mobil: '', kapasitas: 7 as number | null, keterangan: '' });
const registrationForm = reactive({ siswa: null as number | null, armada: null as number | null, harga: JEMPUTAN_TARIF_MINIMAL as number | null });
const bulan = ref(new Date().getMonth() + 1), tahun = ref(new Date().getFullYear()), scope = ref({ bulan: bulan.value, tahun: tahun.value });
const recapRows = ref<JemputanRekapRow[]>([]), recapLoading = ref(false), recapError = ref(''), recapReady = ref(false), exporting = ref(false), exportError = ref('');
let masterSequence = 0, recapSequence = 0;
const studentMap = computed(() => new Map(students.value.map(row => [row.id, row])));
const fleetMap = computed(() => new Map(fleets.value.map(row => [row.id, `${row.nama_supir}${row.jenis_mobil ? ` (${row.jenis_mobil})` : ''}`])));
const studentOptions = computed(() => students.value.filter(row => row.status === 'aktif' || row.id === registrationForm.siswa).map(row => ({ id: row.id, label: `${row.nama} · ${row.nis || 'NIS belum diisi'}` })));
const fleetOptions = computed(() => fleets.value.map(row => ({ id: row.id, label: fleetMap.value.get(row.id) })));
const { query: fleetQuery, filtered: filteredFleets } = useTableSearch(fleets, row => [row.nama_supir, row.jenis_mobil, row.keterangan]);
const registrationDisplay = computed(() => registrations.value.map(row => ({ ...row, nama: studentMap.value.get(row.siswa)?.nama ?? `Siswa #${row.siswa}`, nis: studentMap.value.get(row.siswa)?.nis, alamat: studentMap.value.get(row.siswa)?.alamat || 'Alamat belum diisi', armadaLabel: row.armada ? fleetMap.value.get(row.armada) ?? 'Nama armada belum dimuat' : 'Belum ditentukan' })));
const { query: registrationQuery, filtered: filteredRegistrations } = useTableSearch(registrationDisplay, row => [row.nama, row.nis, row.armadaLabel]);
const first = ref(0), directoryRows = computed(() => tab.value === 'armada' ? filteredFleets.value : filteredRegistrations.value);
const fleetPage = computed(() => filteredFleets.value.slice(first.value, first.value + 10)), registrationPage = computed(() => filteredRegistrations.value.slice(first.value, first.value + 10));
watch([fleetQuery, registrationQuery, tab], () => {
    first.value = 0;
});
const { query: recapQuery, filtered: filteredRecap } = useTableSearch(recapRows, row => [row.nis, row.nama, row.armada]);
const periodLabel = computed(() => new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric' }).format(new Date(scope.value.tahun, scope.value.bulan - 1, 1)));
const dirty = computed(() => bulan.value !== scope.value.bulan || tahun.value !== scope.value.tahun);
function message(e: unknown, fallback: string) {
    const result = friendlyError(e, fallback);
    return [result.summary, result.detail].filter(Boolean).join('. ');
}
async function loadDirectory() {
    const request = ++masterSequence, kind = tab.value;
    loading.value = true;
    error.value = '';
    first.value = 0;
    if (kind === 'armada')
        fleets.value = [];
    else
        registrations.value = [];
    try {
        const [armada, pend, siswa] = await Promise.all([armadaApi.listAll(), kind === 'pendaftaran' ? pendaftaranJemputanApi.listAll() : Promise.resolve(null), kind === 'pendaftaran' ? siswaApi.listAll() : Promise.resolve(null)]);
        if (request !== masterSequence)
            return;
        fleets.value = armada;
        if (pend)
            registrations.value = pend;
        if (siswa)
            students.value = siswa;
    }
    catch (e) {
        if (request === masterSequence)
            error.value = message(e, 'Daftar jemputan belum berhasil dimuat');
    }
    finally {
        if (request === masterSequence)
            loading.value = false;
    }
}
async function loadRecap() {
    const request = ++recapSequence, current = { ...scope.value };
    recapLoading.value = true;
    recapReady.value = false;
    recapError.value = '';
    recapRows.value = [];
    try {
        const [pend, siswa, records, armada] = await Promise.all([pendaftaranJemputanApi.listAll(), siswaApi.listAll({ status: 'aktif' }), kehadiranApi.listAll(monthDateRange(current.bulan, current.tahun)), armadaApi.listAll()]);
        if (request !== recapSequence)
            return;
        if (pend.some(row => row.harga == null || !Number.isFinite(Number(row.harga)) || Number(row.harga) < 0))
            throw new Error('Ada tarif pendaftaran tidak valid. Periksa tarif sebelum membaca nominal rekap.');
        const counts = new Map<number, {
            datang: number;
            pulang: number;
        }>();
        for (const record of records) {
            const value = counts.get(record.siswa) ?? { datang: 0, pulang: 0 };
            if (record.jemput_datang)
                value.datang++;
            if (record.jemput_pulang)
                value.pulang++;
            counts.set(record.siswa, value);
        }
        // shortcut: archives use current registrations/profiles; use historical snapshots when the API provides them.
        recapRows.value = buildJemputanRekap(pend, new Map(siswa.map(row => [row.id, { nis: row.nis, nama: row.nama, alamat: row.alamat }])), new Map(armada.map(row => [row.id, `${row.nama_supir}${row.jenis_mobil ? ` (${row.jenis_mobil})` : ''}`])), counts);
        recapReady.value = true;
    }
    catch (e) {
        if (request === recapSequence)
            recapError.value = message(e, 'Rekap jemputan belum berhasil dimuat');
    }
    finally {
        if (request === recapSequence)
            recapLoading.value = false;
    }
}
function apply() {
    if (recapLoading.value || exporting.value)
        return;
    scope.value = { bulan: bulan.value, tahun: tahun.value };
    void loadRecap();
}
function openFleet(row?: ArmadaJemputan) {
    formKind.value = 'armada';
    editing.value = row?.id ?? null;
    Object.assign(fleetForm, { nama_supir: row?.nama_supir ?? '', jenis_mobil: row?.jenis_mobil ?? '', kapasitas: row?.kapasitas ?? 7, keterangan: row?.keterangan ?? '' });
    openForm();
}
function openRegistration(row?: PendaftaranJemputan) {
    formKind.value = 'pendaftaran';
    editing.value = row?.id ?? null;
    Object.assign(registrationForm, { siswa: row?.siswa ?? null, armada: row?.armada ?? null, harga: row ? Number(row.harga) : JEMPUTAN_TARIF_MINIMAL });
    openForm();
}
function openForm() {
    if (saving.value)
        return;
    attempted.value = false;
    formError.value = '';
    uncertain.value = false;
    visible.value = true;
}
const invalidFleet = computed(() => !fleetForm.nama_supir.trim() || fleetForm.nama_supir.length > 100 || fleetForm.jenis_mobil.length > 50 || fleetForm.keterangan.length > 255 || fleetForm.kapasitas == null || !Number.isInteger(fleetForm.kapasitas) || fleetForm.kapasitas < 0);
const invalidRegistration = computed(() => !registrationForm.siswa || !studentMap.value.has(registrationForm.siswa) || registrationForm.harga == null || !Number.isFinite(registrationForm.harga) || registrationForm.harga < 0 || !!registrationForm.armada && !fleetMap.value.has(registrationForm.armada));
async function save() {
    if (saving.value)
        return;
    attempted.value = true;
    formError.value = '';
    if (formKind.value === 'armada' ? invalidFleet.value : invalidRegistration.value) {
        formError.value = 'Periksa isian wajib, panjang teks, dan angka nol atau lebih sebelum menyimpan.';
        return;
    }
    if (uncertain.value && !editing.value) {
        formError.value = 'Hasil penambahan sebelumnya belum pasti. Tutup form, muat ulang daftar, dan periksa data sebelum menambahkan kembali.';
        return;
    }
    saving.value = true;
    try {
        if (formKind.value === 'armada') {
            const payload = { nama_supir: fleetForm.nama_supir.trim(), jenis_mobil: fleetForm.jenis_mobil, kapasitas: fleetForm.kapasitas!, keterangan: fleetForm.keterangan };
            if (editing.value)
                await armadaApi.update(editing.value, payload);
            else
                await armadaApi.create(payload);
        }
        else {
            const payload = { siswa: registrationForm.siswa!, armada: registrationForm.armada, harga: registrationForm.harga!.toFixed(2) };
            if (editing.value)
                await pendaftaranJemputanApi.update(editing.value, payload);
            else
                await pendaftaranJemputanApi.create(payload);
        }
        notifySuccess(toast, formKind.value === 'armada' ? 'Armada tersimpan' : 'Pendaftaran jemputan tersimpan');
        visible.value = false;
        await loadDirectory();
    }
    catch (e) {
        const status = (e as {
            response?: {
                status?: number;
            };
        })?.response?.status;
        // shortcut: create endpoints have no request ID; require a list check after an ambiguous outcome.
        uncertain.value = !status || status >= 500;
        formError.value = message(e, 'Data belum berhasil disimpan') + '. Input tetap ada.' + (uncertain.value && !editing.value ? ' Periksa daftar sebelum menambahkan kembali.' : '');
    }
    finally {
        saving.value = false;
    }
}
function removeFleet(row: ArmadaJemputan) {
    remove('armada', row.id, row.nama_supir);
}
function removeRegistration(row: PendaftaranJemputan) {
    remove('pendaftaran', row.id, studentMap.value.get(row.siswa)?.nama ?? `Siswa #${row.siswa}`);
}
function remove(kind: 'armada' | 'pendaftaran', id: number, label: string) {
    confirm.require({ header: kind === 'armada' ? 'Hapus armada?' : 'Hapus pendaftaran jemputan?', message: kind === 'armada' ? `Armada ${label} akan dihapus. Pendaftaran siswa terkait kehilangan penetapan armada, tetapi tetap ada.` : `Pendaftaran jemputan ${label} akan dihapus. Catatan absensi siswa tetap ada.`, acceptLabel: 'Hapus', rejectLabel: 'Kembali', acceptProps: { severity: 'danger' }, accept: async () => {
            if (saving.value)
                return;
            saving.value = true;
            actionError.value = '';
            try {
                if (kind === 'armada')
                    await armadaApi.remove(id);
                else
                    await pendaftaranJemputanApi.remove(id);
                notifySuccess(toast, 'Data dihapus');
                await loadDirectory();
            }
            catch (e) {
                actionError.value = message(e, 'Data belum berhasil dihapus') + '. Muat ulang daftar untuk memeriksa hasil.';
            }
            finally {
                saving.value = false;
            }
        } });
}
function csv() {
    if (!recapReady.value || !filteredRecap.value.length)
        return;
    downloadCsv(`rekap-jemputan-${scope.value.tahun}-${String(scope.value.bulan).padStart(2, '0')}.csv`, jemputanRekapToCsv(filteredRecap.value));
}
async function legacy() {
    if (!recapReady.value || exporting.value)
        return;
    exporting.value = true;
    exportError.value = '';
    try {
        await legacyExportApi.jemput(scope.value.bulan, scope.value.tahun, `laporan-jemput-legacy-${scope.value.tahun}-${String(scope.value.bulan).padStart(2, '0')}.csv`);
    }
    catch (e) {
        exportError.value = message(e, 'CSV format lama belum berhasil diunduh');
    }
    finally {
        exporting.value = false;
    }
}
watch(tab, () => {
    actionError.value = '';
    if (tab.value === 'rekap')
        void loadRecap();
    else
        void loadDirectory();
});
function beforeUnload(event: BeforeUnloadEvent) {
    if (saving.value) {
        event.preventDefault();
        event.returnValue = '';
    }
}
onMounted(() => {
    void loadDirectory();
    window.addEventListener('beforeunload', beforeUnload);
});
onBeforeRouteLeave(() => !saving.value);
onBeforeUnmount(() => {
    masterSequence++;
    recapSequence++;
    window.removeEventListener('beforeunload', beforeUnload);
});
</script>
<template>
<PageLayout class="school-service-page" title="Jemputan"
  subtitle="Kelola kendaraan dan peserta, lalu periksa perjalanan yang tercatat." :surface="false"><template
    #actions>
    <RouterLink class="service-link" to="/absensi-siswa">
      <Icon name="calendar-blank" />Buka absensi
    </RouterLink>
  </template>
  <nav class="service-nav" aria-label="Bagian jemputan"><button
      v-for="item in [{id:'armada',label:'Armada'},{id:'pendaftaran',label:'Pendaftaran siswa'},{id:'rekap',label:'Rekap jemputan'}]"
      :key="item.id" type="button" :aria-pressed="tab===item.id" :disabled="saving"
      @click="tab=item.id">{{ item.label }}</button></nav>
  <section v-if="tab!=='rekap'" :key="tab" class="service-panel bee-subpage">
    <header class="service-heading">
      <h2>{{ tab==='armada'?'Armada jemputan':'Pendaftaran siswa' }}</h2>
      <p>
        {{ tab==='armada'?'Identitas pengemudi, kendaraan, kapasitas, dan keterangan rute.':'Tarif berlaku per perjalanan datang atau pulang. Penanda perjalanan diisi melalui absensi.' }}
      </p>
    </header>
    <div class="service-toolbar">
      <div class="service-field"><label
          :for="tab==='armada'?'fleet-search':'registration-search'">{{ tab==='armada'?'Cari armada':'Cari peserta jemputan' }}</label>
        <SearchField v-if="tab==='armada'" input-id="fleet-search" v-model="fleetQuery"
          placeholder="Pengemudi, mobil, atau rute" hint="Mencari pada seluruh armada yang dimuat." />
        <SearchField v-else input-id="registration-search" v-model="registrationQuery"
          placeholder="Nama, NIS, atau armada" hint="Mencari pada seluruh pendaftaran yang dimuat." />
      </div>
      <div class="service-buttons"><Button label="Muat ulang daftar" severity="secondary"
          :disabled="loading||saving" @click="loadDirectory"><template #icon>
            <Icon name="arrows-clockwise" />
          </template></Button><Button :label="tab==='armada'?'Tambah armada':'Daftarkan siswa'"
          :disabled="loading||saving||!!error"
          @click="tab==='armada'?openFleet():openRegistration()"><template #icon>
            <Icon name="plus" />
          </template></Button></div>
    </div>
    <div v-if="actionError" class="service-notice">
      <Message severity="error" :closable="false">{{ actionError }}</Message>
    </div>
    <div v-if="loading" class="service-empty" role="status">
      <Icon name="arrows-clockwise" />
      <p>Memuat seluruh {{ tab==='armada'?'armada':'pendaftaran dan pilihan siswa' }}…</p>
    </div>
    <div v-else-if="error" class="service-empty">
      <Icon name="warning-circle" />
      <h3>Daftar belum dapat ditampilkan</h3>
      <p role="alert">{{ error }}</p><Button label="Coba muat daftar" severity="secondary"
        @click="loadDirectory" />
    </div>
    <div v-else-if="!directoryRows.length" class="service-empty">
      <Icon name="van" />
      <h3>
        {{ (tab==='armada'?fleetQuery:registrationQuery).trim()?'Tidak ada hasil yang cocok':tab==='armada'?'Belum ada armada':'Belum ada peserta jemputan' }}
      </h3>
      <p>Sesuaikan pencarian atau gunakan tombol {{ tab==='armada'?'Tambah armada':'Daftarkan siswa' }} untuk
        mengisi daftar.</p>
    </div>
    <template v-else>
      <div class="service-result-count" role="status">
        {{ first+1 }}–{{ Math.min(first+10,directoryRows.length) }} dari {{ directoryRows.length }}
        {{ tab==='armada'?'armada':'pendaftaran' }}</div>
      <template v-if="tab==='armada'">
        <table class="service-master-table">
          <caption class="service-caption">Daftar armada jemputan</caption>
          <thead>
            <tr>
              <th scope="col">Pengemudi dan kendaraan</th>
              <th scope="col">Kapasitas</th>
              <th scope="col">Keterangan / rute</th>
              <th scope="col">Tindakan</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in fleetPage" :key="row.id">
              <th scope="row">
                {{ row.nama_supir }}<small>{{ row.jenis_mobil||'Jenis mobil belum diisi' }}</small></th>
              <td>{{ row.kapasitas }} penumpang</td>
              <td>{{ row.keterangan||'Belum diisi' }}</td>
              <td class="service-master-actions"><Button :aria-label="`Ubah armada ${row.nama_supir}`"
                  severity="secondary" text :disabled="saving" @click="openFleet(row)"><template #icon>
                    <Icon name="pencil-simple" />
                  </template></Button><Button :aria-label="`Hapus armada ${row.nama_supir}`" severity="danger"
                  text :disabled="saving" @click="removeFleet(row)"><template #icon>
                    <Icon name="trash" />
                  </template></Button></td>
            </tr>
          </tbody>
        </table>
        <ul class="service-master-cards">
          <li v-for="row in fleetPage" :key="row.id">
            <strong>{{ row.nama_supir }}</strong><small>{{ row.jenis_mobil||'Jenis mobil belum diisi' }}</small>
            <p>Kapasitas {{ row.kapasitas }} penumpang</p>
            <p>{{ row.keterangan||'Keterangan / rute belum diisi' }}</p>
            <div class="service-buttons"><Button label="Ubah armada" severity="secondary" :disabled="saving"
                @click="openFleet(row)" /><Button :aria-label="`Hapus armada ${row.nama_supir}`"
                severity="danger" text :disabled="saving" @click="removeFleet(row)"><template #icon>
                  <Icon name="trash" />
                </template></Button></div>
          </li>
        </ul>
      </template>
      <template v-else>
        <table class="service-master-table">
          <caption class="service-caption">Daftar peserta jemputan</caption>
          <thead>
            <tr>
              <th scope="col">Siswa dan armada</th>
              <th scope="col">Alamat penjemputan</th>
              <th scope="col" class="service-master-number">Tarif / perjalanan</th>
              <th scope="col">Tindakan</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in registrationPage" :key="row.id">
              <th scope="row">{{ row.nama }}<small>{{ row.nis||'NIS belum diisi' }} ·
                  {{ row.armadaLabel }}</small></th>
              <td>{{ row.alamat }}</td>
              <td class="service-money service-master-number">{{ formatRp(row.harga) }}</td>
              <td class="service-master-actions"><Button :aria-label="`Ubah pendaftaran ${row.nama}`"
                  severity="secondary" text :disabled="saving" @click="openRegistration(row)"><template #icon>
                    <Icon name="pencil-simple" />
                  </template></Button><Button :aria-label="`Hapus pendaftaran ${row.nama}`" severity="danger"
                  text :disabled="saving" @click="removeRegistration(row)"><template #icon>
                    <Icon name="trash" />
                  </template></Button></td>
            </tr>
          </tbody>
        </table>
        <ul class="service-master-cards">
          <li v-for="row in registrationPage" :key="row.id">
            <strong>{{ row.nama }}</strong><small>{{ row.nis||'NIS belum diisi' }} ·
              {{ row.armadaLabel }}</small>
            <p>{{ row.alamat }}</p>
            <p class="service-money">{{ formatRp(row.harga) }} / perjalanan</p>
            <div class="service-buttons"><Button label="Ubah pendaftaran" severity="secondary"
                :disabled="saving" @click="openRegistration(row)" /><Button
                :aria-label="`Hapus pendaftaran ${row.nama}`" severity="danger" text :disabled="saving"
                @click="removeRegistration(row)"><template #icon>
                  <Icon name="trash" />
                </template></Button></div>
          </li>
        </ul>
      </template>
      <Paginator v-if="directoryRows.length>10" v-model:first="first" :rows="10"
        :total-records="directoryRows.length" :page-link-size="3"
        template="PrevPageLink PageLinks NextPageLink"><template #prevpagelinkicon>
          <Icon name="caret-left" />
        </template><template #nextpagelinkicon>
          <Icon name="caret-right" />
        </template></Paginator>
    </template>
  </section>
  <div v-else class="bee-subpage">
    <section class="service-panel">
      <header class="service-heading">
        <h2>Pilih cakupan rekap</h2>
        <p>Jumlah perjalanan datang dan pulang berasal dari catatan absensi pada seluruh tanggal bulan
          tersebut.</p>
      </header>
      <form class="service-controls" @submit.prevent="apply">
        <div class="service-field"><label>Periode rekap</label>
          <PeriodPicker v-model:bulan="bulan" v-model:tahun="tahun" />
        </div><Button label="Terapkan" type="submit" :disabled="recapLoading||exporting"><template #icon>
            <Icon name="funnel" />
          </template></Button>
      </form>
      <p v-if="dirty" class="service-note" role="status">Pilihan belum diterapkan. Hasil dan CSV masih
        mengikuti bulan pada hasil.</p>
    </section>
    <section class="service-panel">
      <header class="service-heading">
        <h2>{{ periodLabel }}</h2>
        <p>Jumlah = (perjalanan datang + perjalanan pulang) × tarif per perjalanan. Siswa terdaftar tanpa
          perjalanan ditampilkan dengan jumlah nol.</p>
      </header>
      <div class="service-toolbar">
        <div class="service-field"><label for="transport-search">Cari siswa pada rekap</label>
          <SearchField input-id="transport-search" v-model="recapQuery" placeholder="Nama, NIS, atau armada"
            hint="Mencari pada seluruh hasil rekap yang dimuat." />
        </div>
        <div class="service-buttons"><Button label="Muat ulang rekap" severity="secondary"
            :disabled="recapLoading||exporting" @click="loadRecap"><template #icon>
              <Icon name="arrows-clockwise" />
            </template></Button><Button label="Unduh CSV" severity="secondary"
            :disabled="!recapReady||!filteredRecap.length" @click="csv"><template #icon>
              <Icon name="download" />
            </template></Button><Button label="CSV format lama" severity="secondary" text
            :disabled="!recapReady||exporting" :loading="exporting" @click="legacy" /></div>
      </div>
      <div v-if="exportError" class="service-notice">
        <Message severity="error" :closable="false">{{ exportError }}</Message>
      </div>
      <ServiceRecap kind="jemputan" :rows="filteredRecap" :loading="recapLoading" :error="recapError"
        :filtered="!!recapQuery.trim()" @retry="loadRecap" @clear-search="recapQuery=''" />
      <p class="service-note service-recap-note">Rekap memakai siswa aktif, pendaftaran dan tarif saat ini,
        termasuk saat membuka arsip. Jika satu siswa memiliki beberapa pendaftaran, tarif dan armada memakai
        pendaftaran terbaru, sesuai aturan tagihan. Rekap bukan bukti tagihan sudah dibuat atau dibayar. CSV
        mengikuti pencarian; CSV format lama memakai seluruh cakupan endpoint bulanan.</p>
    </section>
  </div>
  <Dialog :visible="visible" @update:visible="value=>{if(!saving)visible=value}"
    :header="formKind==='armada'?(editing?'Ubah armada':'Tambah armada'):(editing?'Ubah pendaftaran':'Daftarkan jemputan')"
    class="service-dialog" modal :closable="!saving" :close-on-escape="!saving"><template #closeicon>
      <Icon name="x" />
    </template>
    <form id="transport-form" @submit.prevent="save">
      <fieldset class="service-form" :disabled="saving">
        <template v-if="formKind==='armada'">
          <div class="service-field"><label for="fleet-driver">Nama pengemudi (wajib)</label>
            <InputText id="fleet-driver" v-model="fleetForm.nama_supir" :maxlength="100"
              :invalid="attempted&&!fleetForm.nama_supir.trim()"
              :aria-invalid="attempted&&!fleetForm.nama_supir.trim()" fluid />
          </div>
          <div class="service-field"><label for="fleet-car">Jenis mobil</label>
            <InputText id="fleet-car" v-model="fleetForm.jenis_mobil" :maxlength="50" fluid
              placeholder="Contoh: Avanza" />
          </div>
          <div class="service-field"><label for="fleet-capacity">Kapasitas penumpang</label>
            <InputNumber input-id="fleet-capacity" v-model="fleetForm.kapasitas" :min="0"
              :max-fraction-digits="0"
              :invalid="attempted&&(fleetForm.kapasitas==null||fleetForm.kapasitas<0)" fluid />
          </div>
          <div class="service-field"><label for="fleet-route">Keterangan / rute</label><Textarea
              id="fleet-route" v-model="fleetForm.keterangan" :maxlength="255" rows="3" auto-resize fluid />
          </div>
        </template>
        <template v-else>
          <div class="service-field"><label for="transport-student">Siswa (wajib)</label><Select :key="(saving) ? 'locked' : 'editable'"
              input-id="transport-student" :disabled="saving" v-model="registrationForm.siswa"
              :options="studentOptions" option-label="label" option-value="id" filter
              :invalid="attempted&&!registrationForm.siswa" placeholder="Pilih siswa" fluid><template
                #dropdownicon>
                <Icon name="caret-down" />
              </template><template #filtericon>
                <Icon name="magnifying-glass" />
              </template></Select></div>
          <div class="service-field"><label>Alamat dari profil siswa</label>
            <p class="transport-address">
              {{ registrationForm.siswa?studentMap.get(registrationForm.siswa)?.alamat||'Alamat belum diisi':'Pilih siswa untuk melihat alamat.' }}
            </p>
          </div>
          <div class="service-field"><label for="transport-fleet">Armada</label><Select :key="(saving) ? 'locked' : 'editable'"
              input-id="transport-fleet" :disabled="saving" v-model="registrationForm.armada"
              :options="fleetOptions" option-label="label" option-value="id" show-clear
              placeholder="Belum ditentukan" fluid><template #dropdownicon>
                <Icon name="caret-down" />
              </template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
          <div class="service-field"><label for="transport-price">Tarif per perjalanan (wajib)</label>
            <InputNumber input-id="transport-price" v-model="registrationForm.harga" :min="0"
              :max-fraction-digits="2" locale="id-ID" :invalid="attempted&&registrationForm.harga==null"
              aria-describedby="transport-price-help" fluid /><small id="transport-price-help">Satu datang
              atau satu pulang dihitung satu perjalanan. Angka awal {{ formatRp(JEMPUTAN_TARIF_MINIMAL) }}
              dapat disesuaikan; nol tetap diperbolehkan.</small>
          </div>
        </template>
      </fieldset>
      <Message v-if="formError" severity="error" :closable="false" role="alert">{{ formError }}</Message>
    </form><template #footer><Button label="Kembali" severity="secondary" :disabled="saving"
        @click="visible=false" /><Button label="Simpan" type="submit" form="transport-form" :loading="saving"
        :disabled="saving" /></template>
  </Dialog>
</PageLayout>
</template>
<style scoped>
.service-buttons {
  display: flex;
  align-items: center;
  gap: var(--bee-space-2);
  flex-wrap: wrap
}

.service-money {
  font-variant-numeric: tabular-nums;
  white-space: nowrap
}

.transport-address {
  margin: 0;
  font-size: var(--bee-type-ui);
  color: var(--app-text-muted);
  overflow-wrap: anywhere
}

.service-recap-note {
  padding-top: var(--bee-space-4)
}
</style>
