<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { onBeforeRouteLeave, RouterLink } from 'vue-router';
import Button from 'primevue/button';
import DatePicker from 'primevue/datepicker';
import Message from 'primevue/message';
import Select from 'primevue/select';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import PageLayout from '@/shared/components/PageLayout.vue';
import Icon from '@/shared/components/PhosphorIcon.vue';
import SearchField from '@/shared/components/SearchField.vue';
import { useTableSearch } from '@/shared/composables/useTableSearch';
import { calendarTextMatches, formatLocalDate } from '@/core/format';
import { friendlyError, notifySuccess } from '@/core/errors';
import { siswaApi } from '@/features/siswa/api';
import { useAuthStore } from '@/stores/auth';
import type { Jenjang, Kelompok, Siswa } from '@/types/api';
import AttendanceGrid from './AttendanceGrid.vue';
import { jenjangApi, kelompokApi, kehadiranApi } from './api';
import { attendanceChanged, attendanceFromRecord, attendanceNeedsSave, attendancePayload, emptyAttendance, type AttendanceRow } from './presentation';
interface Scope {
    tanggal: string;
    jenjang: Jenjang;
    kelompok: Kelompok;
}
const auth = useAuthStore(), toast = useToast(), confirm = useConfirm();
const canEdit = computed(() => auth.hasRole(['Administration']));
const levels = ref<Jenjang[]>([]), groups = ref<Kelompok[]>([]);
const level = ref<number | null>(null), group = ref<number | null>(null), date = ref<Date | null>(new Date());
const levelsLoading = ref(false), groupsLoading = ref(false), levelsError = ref(''), groupsError = ref('');
const invalidDate = ref(false), attempted = ref(false), choosing = ref(false);
const scope = ref<Scope | null>(null), students = ref<Siswa[]>([]);
const attendance = ref<Record<number, AttendanceRow>>({}), baseline = ref<Record<number, AttendanceRow>>({});
const loading = ref(false), saving = ref(false), loadError = ref(''), saveError = ref(''), failedIds = ref<number[]>([]), saveMessage = ref('');
const { query, filtered: visibleStudents } = useTableSearch(students, student => [student.nama, student.nis]);
let groupSequence = 0, gridSequence = 0;
const dateString = computed(() => date.value && Number.isFinite(date.value.getTime()) ? formatLocalDate(date.value) : '');
const hasChanges = computed(() => Object.values(attendance.value).some(row => attendanceChanged(row, baseline.value[row.siswaId])));
const hasDraft = computed(() => hasChanges.value || failedIds.value.length > 0);
const unresolvedCount = computed(() => new Set([...pendingRows.value.map(row => row.siswaId), ...failedIds.value]).size);
const pendingRows = computed(() => Object.values(attendance.value).filter(row => attendanceNeedsSave(row, baseline.value[row.siswaId])));
const visibleRows = computed(() => visibleStudents.value.map(student => attendance.value[student.id]).filter((row): row is AttendanceRow => !!row));
const absentVisible = computed(() => visibleRows.value.filter(row => row.status !== 'hadir').length);
const cateringMissing = computed(() => visibleRows.value.filter(row => row.status === 'hadir' && !row.ikut_katering).length);
const contextChanged = computed(() => !!scope.value && (level.value !== scope.value.jenjang.id || group.value !== scope.value.kelompok.id || dateString.value !== scope.value.tanggal || invalidDate.value));
function message(error: unknown, fallback: string) { const result = friendlyError(error, fallback); return [result.summary, result.detail].filter(Boolean).join('. '); }
async function loadLevels() { levelsLoading.value = true; levelsError.value = ''; try {
    levels.value = await jenjangApi.listAll();
}
catch (e) {
    levelsError.value = message(e, 'Jenjang belum berhasil dimuat');
}
finally {
    levelsLoading.value = false;
} }
async function loadGroups() {
    const request = ++groupSequence, id = level.value;
    groups.value = [];
    groupsError.value = '';
    if (!id) {
        groupsLoading.value = false;
        return;
    }
    groupsLoading.value = true;
    try {
        const data = await kelompokApi.listAll({ jenjang: id });
        if (request === groupSequence) {
            groups.value = data;
            // A level with a single group has nothing to choose; select it.
            if (data.length === 1)
                group.value = data[0]!.id;
        }
    }
    catch (e) {
        if (request === groupSequence)
            groupsError.value = message(e, 'Kelompok belum berhasil dimuat');
    }
    finally {
        if (request === groupSequence)
            groupsLoading.value = false;
    }
}
watch(level, () => { group.value = null; void loadGroups(); });
function checkDate(event: Event) { if (event.target instanceof HTMLInputElement)
    invalidDate.value = !calendarTextMatches(event.target.value, date.value); }
function ask(message: string, header = 'Perubahan belum disimpan') {
    return new Promise<boolean>(resolve => confirm.require({ header, message, acceptLabel: 'Lanjutkan tanpa menyimpan', rejectLabel: 'Tetap di sini', acceptProps: { severity: 'danger' }, accept: () => resolve(true), reject: () => resolve(false), onHide: () => resolve(false) }));
}
async function loadGrid(target: Scope) {
    const request = ++gridSequence;
    scope.value = { ...target };
    loading.value = true;
    loadError.value = '';
    saveError.value = '';
    saveMessage.value = '';
    students.value = [];
    attendance.value = {};
    baseline.value = {};
    failedIds.value = [];
    try {
        const [roster, records] = await Promise.all([siswaApi.listAll({ kelompok: target.kelompok.id, status: 'aktif' }), kehadiranApi.listAll({ tanggal: target.tanggal, kelompok: target.kelompok.id })]);
        if (request !== gridSequence)
            return;
        const saved = new Map(records.map(record => [record.siswa, record]));
        students.value = roster;
        const values: Record<number, AttendanceRow> = {};
        for (const student of roster) {
            const record = saved.get(student.id);
            values[student.id] = record ? attendanceFromRecord(record) : emptyAttendance(student.id);
        }
        attendance.value = values;
        baseline.value = structuredClone(values);
    }
    catch (e) {
        if (request === gridSequence)
            loadError.value = message(e, 'Data absensi belum berhasil dimuat');
    }
    finally {
        if (request === gridSequence)
            loading.value = false;
    }
}
async function apply() {
    if (saving.value || loading.value || choosing.value)
        return;
    attempted.value = true;
    const selectedLevel = levels.value.find(item => item.id === level.value), selectedGroup = groups.value.find(item => item.id === group.value);
    if (!selectedLevel || !selectedGroup || !dateString.value || invalidDate.value)
        return;
    const target: Scope = { tanggal: dateString.value, jenjang: { ...selectedLevel }, kelompok: { ...selectedGroup } };
    choosing.value = true;
    try {
        if (hasDraft.value && !await ask('Menampilkan kelompok atau tanggal lain akan membuang perubahan pada daftar saat ini.'))
            return;
        query.value = '';
        await loadGrid(target);
    }
    finally {
        choosing.value = false;
    }
}
async function refresh() { if (!scope.value || saving.value || loading.value)
    return; if (hasDraft.value && !await ask('Muat ulang akan mengganti pilihan yang belum disimpan dengan catatan terbaru.'))
    return; await loadGrid(scope.value); }
async function save() {
    const current = scope.value;
    if (!current || !canEdit.value || saving.value || loading.value || loadError.value || !unresolvedCount.value)
        return;
    saving.value = true;
    saveError.value = '';
    saveMessage.value = '';
    try {
        // Re-read IDs before retrying: an interrupted create may already have succeeded.
        const records = await kehadiranApi.listAll({ tanggal: current.tanggal, kelompok: current.kelompok.id });
        const saved = new Map(records.map(record => [record.siswa, record]));
        for (const row of Object.values(attendance.value)) {
            const record = saved.get(row.siswaId);
            if (record && (!row.existingId || failedIds.value.includes(row.siswaId))) {
                const actual = attendanceFromRecord(record);
                attendance.value[row.siswaId] = failedIds.value.includes(row.siswaId) || attendanceChanged(row, baseline.value[row.siswaId]) ? { ...row, existingId: record.id } : actual;
                baseline.value[row.siswaId] = { ...actual };
            }
        }
        const pending = [...pendingRows.value];
        failedIds.value = [];
        // shortcut: saves are per record; use an atomic bulk endpoint when the backend supports it.
        const results = await Promise.allSettled(pending.map(row => { const payload = attendancePayload(row, current.tanggal); return row.existingId ? kehadiranApi.update(row.existingId, payload) : kehadiranApi.create(payload); }));
        let savedCount = 0;
        const errors: string[] = [];
        results.forEach((result, index) => {
            const row = pending[index]!;
            if (result.status === 'fulfilled') {
                const actual = attendanceFromRecord(result.value);
                attendance.value[row.siswaId] = actual;
                baseline.value[row.siswaId] = { ...actual };
                savedCount += 1;
            }
            else {
                failedIds.value.push(row.siswaId);
                errors.push(message(result.reason, 'Catatan belum terkonfirmasi'));
            }
        });
        if (failedIds.value.length)
            saveError.value = `${savedCount} catatan berhasil disimpan; ${failedIds.value.length} belum terkonfirmasi. ${errors[0]}. Pilihan tetap ada. Saat dicoba ulang, hasil sebelumnya diperiksa lebih dulu.`;
        else {
            saveMessage.value = savedCount ? `${savedCount} catatan disimpan untuk ${current.tanggal}.` : 'Catatan sudah sesuai dengan pilihan pada daftar ini.';
            notifySuccess(toast, 'Absensi tersimpan', { detail: saveMessage.value });
        }
    }
    catch (e) {
        saveError.value = message(e, 'Hasil simpan sebelumnya belum dapat diperiksa') + '. Pilihan tetap ada; belum ada pengiriman baru pada percobaan ini.';
    }
    finally {
        saving.value = false;
    }
}
// Bulk actions only touch students visible under the current search; changes stay drafts until saved.
function markVisiblePresent() {
    if (saving.value || !canEdit.value)
        return;
    const next = { ...attendance.value };
    for (const row of visibleRows.value)
        if (row.status !== 'hadir')
            next[row.siswaId] = { ...row, status: 'hadir' };
    attendance.value = next;
}
function cateringForVisiblePresent() {
    if (saving.value || !canEdit.value)
        return;
    const next = { ...attendance.value };
    for (const row of visibleRows.value)
        if (row.status === 'hadir' && !row.ikut_katering)
            next[row.siswaId] = { ...row, ikut_katering: true };
    attendance.value = next;
}
function remove(studentId: number) {
    const row = attendance.value[studentId], current = scope.value, student = students.value.find(item => item.id === studentId);
    if (!row?.existingId || !current || !canEdit.value || saving.value)
        return;
    confirm.require({ header: 'Hapus catatan absensi?', message: `Catatan ${student?.nama} pada ${current.tanggal} akan dihapus. Pilihan siswa lain tetap dipertahankan.`, acceptLabel: 'Hapus catatan', rejectLabel: 'Kembali', acceptProps: { severity: 'danger' }, accept: async () => {
            if (saving.value)
                return;
            saving.value = true;
            saveError.value = '';
            saveMessage.value = '';
            try {
                await kehadiranApi.remove(row.existingId!);
                attendance.value[studentId] = emptyAttendance(studentId);
                baseline.value[studentId] = emptyAttendance(studentId);
                failedIds.value = failedIds.value.filter(id => id !== studentId);
                saveMessage.value = 'Catatan dihapus. Pilihan Hadir pada form belum disimpan kembali.';
            }
            catch (e) {
                saveError.value = message(e, 'Catatan belum berhasil dihapus') + '. Pilihan pada daftar tetap dipertahankan.';
            }
            finally {
                saving.value = false;
            }
        } });
}
function beforeUnload(event: BeforeUnloadEvent) { if (saving.value || hasDraft.value) {
    event.preventDefault();
    event.returnValue = '';
} }
onBeforeRouteLeave(async () => { if (saving.value)
    return false; return !hasDraft.value || await ask('Ada perubahan absensi yang belum disimpan. Tinggalkan halaman ini?'); });
onMounted(() => { void loadLevels(); window.addEventListener('beforeunload', beforeUnload); });
onBeforeUnmount(() => { gridSequence += 1; groupSequence += 1; window.removeEventListener('beforeunload', beforeUnload); });
</script>
<template>
<PageLayout class="absensi-page" title="Absensi siswa"
  subtitle="Catat kehadiran dan layanan harian sesuai kelompok dan tanggal." :surface="false"><template
    #actions>
    <RouterLink class="attendance-nav-link" to="/rekap-siswa">
      <Icon name="chart-bar" />Buka rekap
    </RouterLink>
  </template>
  <section class="attendance-panel">
    <header class="attendance-panel-heading">
      <h2>Pilih daftar absensi</h2>
      <p>Tentukan tanggal dan kelompok, lalu tampilkan siswa aktif.</p>
    </header>
    <form class="attendance-controls" @submit.prevent="apply">
      <div class="attendance-field"><label for="attendance-date">Tanggal absensi</label>
        <DatePicker :key="saving ? 'locked' : 'editable'" input-id="attendance-date" v-model="date" date-format="dd/mm/yy" :disabled="saving"
          :invalid="attempted&&(!dateString||invalidDate)"
          :input-props="{'aria-invalid':attempted&&(!dateString||invalidDate),'aria-describedby':attempted&&(!dateString||invalidDate)?'attendance-date-error':undefined}"
          @input="checkDate" @update:model-value="invalidDate=false" fluid><template #previcon>
            <Icon name="caret-left" />
          </template><template #nexticon>
            <Icon name="caret-right" />
          </template></DatePicker><small v-if="attempted&&(!dateString||invalidDate)"
          id="attendance-date-error" class="attendance-field-error">Periksa atau pilih ulang tanggal yang
          valid.</small>
      </div>
      <div class="attendance-field"><label for="attendance-level">Jenjang</label><Select :key="(saving||levelsLoading) ? 'locked' : 'editable'"
          input-id="attendance-level" v-model="level" :options="levels" option-label="nama" option-value="id"
          :loading="levelsLoading" :disabled="saving||levelsLoading" placeholder="Pilih jenjang"
          :invalid="attempted&&!level" :aria-invalid="attempted&&!level"><template #dropdownicon>
            <Icon name="caret-down" />
          </template></Select><small v-if="attempted&&!level" class="attendance-field-error">Pilih jenjang
          siswa.</small></div>
      <div class="attendance-field"><label for="attendance-group">Kelompok</label><Select :key="(saving||!level||groupsLoading) ? 'locked' : 'editable'"
          input-id="attendance-group" v-model="group" :options="groups" option-label="nama" option-value="id"
          :loading="groupsLoading" :disabled="saving||!level||groupsLoading" placeholder="Pilih kelompok"
          :invalid="attempted&&!!level&&!group" :aria-invalid="attempted&&!!level&&!group"><template #dropdownicon>
            <Icon name="caret-down" />
          </template></Select><small v-if="attempted&&!!level&&!group" class="attendance-field-error">Pilih
          kelompok.</small></div><Button label="Tampilkan siswa" type="submit" severity="secondary"
        :disabled="saving||loading||choosing||groupsLoading"><template #icon>
          <Icon name="users" />
        </template></Button>
    </form>
    <div v-if="levelsError||groupsError" class="attendance-notice">
      <Message severity="error" :closable="false">{{ levelsError||groupsError }}</Message><Button
        :label="levelsError?'Muat ulang jenjang':'Muat ulang kelompok'" severity="secondary"
        :disabled="saving" @click="levelsError?loadLevels():loadGroups()" />
    </div>
    <p v-else-if="level&&!groupsLoading&&!groups.length" class="attendance-small-note">Belum ada kelompok pada
      jenjang ini.</p>
    <p v-if="contextChanged" class="attendance-small-note" role="status">Pilihan belum diterapkan. Daftar dan
      tombol Simpan tetap mengikuti tanggal serta kelompok yang tertulis di bawah.</p>
  </section>
  <section v-if="scope" class="attendance-panel attendance-roster" :aria-busy="loading||saving">
    <header class="attendance-panel-heading">
      <h2>{{ scope.kelompok.nama }}</h2>
      <p>{{ scope.jenjang.nama }} · <strong>{{ scope.tanggal.split('-').reverse().join('/') }}</strong></p>
      <p v-if="!loading&&!loadError">{{ unresolvedCount }} catatan {{ failedIds.length?'belum terkonfirmasi':'belum tersimpan' }}</p>
    </header>
    <div v-if="loading" class="attendance-empty" role="status">
      <Icon name="arrows-clockwise" />
      <p>Memuat siswa dan seluruh catatan absensi pada tanggal ini…</p>
    </div>
    <div v-else-if="loadError" class="attendance-empty">
      <Icon name="warning-circle" />
      <h3>Daftar absensi belum dapat ditampilkan</h3>
      <p role="alert">{{ loadError }}</p><Button label="Muat ulang siswa" severity="secondary"
        @click="refresh" />
    </div>
    <div v-else-if="!students.length" class="attendance-empty">
      <Icon name="users" />
      <h3>Belum ada siswa aktif di kelompok ini</h3>
      <p>Periksa kelompok atau status siswa di menu Data siswa.</p>
    </div>
    <template v-else>
      <div v-if="saveError" class="attendance-notice">
        <Message severity="error" :closable="false">{{ saveError }}</Message>
      </div>
      <p v-if="saveMessage" class="attendance-saved-note" role="status">
        <Icon name="check-circle" />{{ saveMessage }}
      </p>
      <div class="attendance-toolbar">
        <div class="attendance-field attendance-search"><label for="attendance-search">Cari dalam daftar</label>
          <SearchField input-id="attendance-search" v-model="query" placeholder="Nama atau NIS" /></div>
        <div class="attendance-bulk" role="group" aria-label="Aksi untuk siswa yang ditampilkan"><Button
            label="Tandai semua hadir" severity="secondary" :disabled="saving||!canEdit||!absentVisible"
            @click="markVisiblePresent"><template #icon>
              <Icon name="check" />
            </template></Button><Button label="Katering untuk semua yang hadir" severity="secondary"
            :disabled="saving||!canEdit||!cateringMissing" @click="cateringForVisiblePresent"><template #icon>
              <Icon name="fork-knife" />
            </template></Button><Button label="Muat ulang catatan" severity="secondary" text :disabled="saving"
            @click="refresh"><template #icon>
              <Icon name="arrows-clockwise" />
            </template></Button></div>
      </div>
      <p class="attendance-small-note">{{ visibleStudents.length }} dari {{ students.length }} siswa ditampilkan.
        Siswa tanpa catatan disiapkan sebagai Hadir. Aksi massal hanya mengubah siswa yang ditampilkan; Simpan
        mencakup seluruh pilihan, termasuk yang tersembunyi oleh pencarian.</p>
      <div v-if="!visibleStudents.length" class="attendance-empty">
        <Icon name="magnifying-glass" />
        <h3>Tidak ada siswa yang cocok</h3><Button label="Hapus pencarian" severity="secondary"
          @click="query=''" />
      </div>
      <AttendanceGrid v-else :students="visibleStudents" v-model="attendance" :baseline="baseline"
        :readonly="saving||!canEdit" :failed-ids="failedIds" @delete="remove" />
      <div class="attendance-savebar">
        <strong>{{ unresolvedCount }} catatan {{ failedIds.length?'belum terkonfirmasi':'belum tersimpan' }}<span
            class="attendance-savebar-total"> · {{ students.length }} siswa</span></strong>
        <div class="attendance-save-actions"><Button :label="saving?'Menyimpan…':'Simpan absensi'" :loading="saving"
            :disabled="!canEdit||!unresolvedCount" @click="save"><template #icon>
              <Icon name="check" />
            </template><template #loadingicon>
              <Icon name="arrows-clockwise" class="bee-spin" />
            </template></Button></div>
      </div>
    </template>
  </section>
  <div v-else class="attendance-empty attendance-start">
    <Icon name="calendar-blank" />
    <h2>Mulai dari tanggal dan kelompok</h2>
    <p>Catatan tersimpan per siswa dan per tanggal. Katering dan jemputan hanya dapat dipilih saat siswa
      hadir.</p>
  </div>
</PageLayout>
</template>
<style src="./attendance.css"></style>
