<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave, RouterLink } from 'vue-router';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputNumber from 'primevue/inputnumber';
import Select from 'primevue/select';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import PageLayout from '@/shared/components/PageLayout.vue';
import SearchField from '@/shared/components/SearchField.vue';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { useTableSearch } from '@/shared/composables/useTableSearch';
import { friendlyError, notifySuccess } from '@/core/errors';
import { jenjangApi } from '@/features/absensi/api';
import { coaApi } from '@/features/jurnal/api';
import type { BayarPendaftaranInput, Coa, Jenjang, PendaftaranSiswa, PendaftaranSiswaInput, PendaftaranSiswaStatus } from '@/types/api';
import { pendaftaranSiswaApi } from './api';
import { cents, components, dateLabel, editable, finalizable, journalLabels, money, receivable, statusLabels, statusOptions, statusSeverity } from './presentation';
import PendaftaranDirectory from './PendaftaranDirectory.vue';
import PendaftaranFormDialog from './PendaftaranFormDialog.vue';
import PendaftaranPaymentDialog from './PendaftaranPaymentDialog.vue';
import './admission.css';
const toast = useToast(), confirm = useConfirm();
const rows = ref<PendaftaranSiswa[]>([]), loading = ref(false), error = ref(''), actionError = ref('');
const levels = ref<Jenjang[]>([]), levelsLoading = ref(false), levelsError = ref('');
const names = computed(() => new Map(levels.value.map(row => [row.id, row.nama])));
const status = ref<PendaftaranSiswaStatus | null>(null), scoped = computed(() => rows.value.filter(row => !status.value || row.status === status.value));
const { query, filtered } = useTableSearch(scoped, row => [row.nama_calon, row.jenjang ? names.value.get(row.jenjang) ?? '' : '', statusLabels[row.status]]);
const formOpen = ref(false), editing = ref<PendaftaranSiswa | null>(null), saving = ref(false), formError = ref(''), uncertainCreate = ref(false);
const detailTarget = ref<PendaftaranSiswa | null>(null), detailLoading = ref(false), detailError = ref('');
const paymentOpen = ref(false), paymentTarget = ref<PendaftaranSiswa | null>(null), paymentSaving = ref(false), paymentError = ref(''), paymentUncertain = ref(false), lastPayment = ref<BayarPendaftaranInput | null>(null);
const accounts = ref<Coa[]>([]), accountsLoading = ref(false), accountsError = ref('');
const finalOpen = ref(false), finalTarget = ref<PendaftaranSiswa | null>(null), finalSaving = ref(false), finalError = ref(''), spp = ref<number | null>(null), finalUncertain = ref(false), lastSpp = ref<string | null>(null);
const deleting = ref(false), busy = computed(() => saving.value || paymentSaving.value || finalSaving.value || deleting.value);
let listSequence = 0, detailSequence = 0, accountSequence = 0;
function message(e: unknown, fallback: string) {
    const result = friendlyError(e, fallback);
    return [result.summary, result.detail].filter(Boolean).join('. ');
}
function ambiguous(e: unknown) {
    const status = (e as {
        response?: {
            status?: number;
        };
    })?.response?.status;
    return !status || status >= 500;
}
function upsert(row: PendaftaranSiswa) {
    rows.value = [...rows.value.filter(item => item.id !== row.id), row].sort((a, b) => b.tanggal_daftar.localeCompare(a.tanggal_daftar) || a.id - b.id);
    if (detailTarget.value?.id === row.id)
        detailTarget.value = row;
}
async function load() {
    const request = ++listSequence;
    loading.value = true;
    error.value = '';
    rows.value = [];
    try {
        const data = await pendaftaranSiswaApi.listAll();
        if (request === listSequence) {
            rows.value = data;
            uncertainCreate.value = false;
        }
    }
    catch (e) {
        if (request === listSequence)
            error.value = message(e, 'Daftar pendaftaran belum berhasil dimuat');
    }
    finally {
        if (request === listSequence)
            loading.value = false;
    }
}
async function loadLevels() {
    levelsLoading.value = true;
    levelsError.value = '';
    try {
        levels.value = await jenjangApi.listAll();
    }
    catch (e) {
        levelsError.value = message(e, 'Jenjang belum berhasil dimuat');
    }
    finally {
        levelsLoading.value = false;
    }
}
async function detail(row: PendaftaranSiswa) {
    const request = ++detailSequence;
    detailTarget.value = row;
    detailLoading.value = true;
    detailError.value = '';
    actionError.value = '';
    try {
        const fresh = await pendaftaranSiswaApi.get(row.id);
        if (request === detailSequence)
            upsert(fresh);
    }
    catch (e) {
        if (request === detailSequence)
            detailError.value = message(e, 'Rincian terbaru belum berhasil diperiksa');
    }
    finally {
        if (request === detailSequence)
            detailLoading.value = false;
    }
}
function closeDetail() {
    detailSequence++;
    detailTarget.value = null;
    detailLoading.value = false;
}
function openCreate() {
    formError.value = '';
    editing.value = null;
    formOpen.value = true;
}
function openEdit(row: PendaftaranSiswa) {
    if (!editable(row))
        return;
    closeDetail();
    editing.value = row;
    formError.value = '';
    formOpen.value = true;
}
async function save(payload: PendaftaranSiswaInput) {
    if (saving.value)
        return;
    if (uncertainCreate.value && !editing.value) {
        formError.value = 'Hasil penambahan sebelumnya belum pasti. Kembali, muat ulang daftar, dan periksa calon sebelum membuat lagi.';
        return;
    }
    saving.value = true;
    formError.value = '';
    try {
        const result = editing.value ? await pendaftaranSiswaApi.update(editing.value.id, payload) : await pendaftaranSiswaApi.create(payload);
        upsert(result);
        formOpen.value = false;
        notifySuccess(toast, 'Data calon tersimpan');
    }
    catch (e) {
        uncertainCreate.value = !editing.value && ambiguous(e);
        formError.value = message(e, 'Data calon belum berhasil disimpan') + (uncertainCreate.value ? '. Kembali dan muat ulang daftar untuk memeriksa hasil sebelum menambah kembali.' : '');
    }
    finally {
        saving.value = false;
    }
}
function remove(row: PendaftaranSiswa) {
    if (!editable(row))
        return;
    confirm.require({ header: 'Hapus pendaftaran?', message: `Data calon ${row.nama_calon} akan dihapus dari daftar. Tindakan hanya tersedia sebelum calon menjadi siswa dan memiliki riwayat penerimaan.`, acceptLabel: 'Hapus calon', rejectLabel: 'Kembali', acceptProps: { severity: 'danger' }, accept: async () => {
            if (busy.value)
                return;
            deleting.value = true;
            actionError.value = '';
            try {
                await pendaftaranSiswaApi.remove(row.id);
                rows.value = rows.value.filter(item => item.id !== row.id);
                closeDetail();
                notifySuccess(toast, 'Data calon dihapus');
            }
            catch (e) {
                actionError.value = message(e, 'Data calon belum berhasil dihapus') + '. Muat ulang rincian untuk memeriksa hasil.';
            }
            finally {
                deleting.value = false;
            }
        } });
}
async function loadAccounts() {
    const request = ++accountSequence;
    accountsLoading.value = true;
    accountsError.value = '';
    accounts.value = [];
    try {
        const result = await coaApi.list();
        if (request === accountSequence)
            accounts.value = result.filter(row => row.is_active && ['111', '112', '1011', '1101', '1102'].includes(row.kode_akun));
    }
    catch (e) {
        if (request === accountSequence)
            accountsError.value = message(e, 'Kas/Bank belum berhasil dimuat');
    }
    finally {
        if (request === accountSequence)
            accountsLoading.value = false;
    }
}
function openPayment(row: PendaftaranSiswa) {
    if (!receivable(row))
        return;
    closeDetail();
    paymentTarget.value = row;
    paymentError.value = '';
    paymentUncertain.value = false;
    lastPayment.value = null;
    paymentOpen.value = true;
    void loadAccounts();
}
async function pay(payload: BayarPendaftaranInput) {
    if (!paymentTarget.value || paymentSaving.value)
        return;
    paymentSaving.value = true;
    paymentError.value = '';
    lastPayment.value = { ...payload, komponen: [...payload.komponen] };
    try {
        const result = await pendaftaranSiswaApi.bayar(paymentTarget.value.id, payload);
        upsert(result.pendaftaran);
        paymentOpen.value = false;
        paymentUncertain.value = false;
        notifySuccess(toast, 'Penerimaan tersimpan', { detail: 'Jurnal menunggu pencatatan Finance.' });
    }
    catch (e) {
        paymentUncertain.value = paymentUncertain.value || ambiguous(e);
        paymentError.value = message(e, 'Penerimaan belum berhasil dikonfirmasi');
    }
    finally {
        paymentSaving.value = false;
    }
}
function retryPayment() {
    if (paymentUncertain.value && lastPayment.value)
        void pay(lastPayment.value);
}
function openFinal(row: PendaftaranSiswa) {
    if (!finalizable(row))
        return;
    closeDetail();
    finalTarget.value = row;
    finalError.value = '';
    spp.value = null;
    lastSpp.value = null;
    finalUncertain.value = false;
    finalOpen.value = true;
}
async function finalize() {
    if (!finalTarget.value || finalSaving.value)
        return;
    if (!finalUncertain.value && cents(spp.value) == null) {
        finalError.value = 'Isi nominal SPP bulanan yang disepakati. Isi 0 jika memang tidak dikenakan.';
        return;
    }
    finalSaving.value = true;
    finalError.value = '';
    const amount = finalUncertain.value ? lastSpp.value! : spp.value!.toFixed(2);
    lastSpp.value = amount;
    try {
        const result = await pendaftaranSiswaApi.finalisasi(finalTarget.value.id, amount);
        upsert(result);
        finalOpen.value = false;
        finalUncertain.value = false;
        notifySuccess(toast, 'Calon resmi terdaftar', { detail: 'Finalisasi tidak mencatat penerimaan uang.' });
        void detail(result);
    }
    catch (e) {
        finalUncertain.value = finalUncertain.value || ambiguous(e);
        finalError.value = message(e, 'Finalisasi belum berhasil dikonfirmasi');
    }
    finally {
        finalSaving.value = false;
    }
}
function beforeUnload(event: BeforeUnloadEvent) {
    if (busy.value) {
        event.preventDefault();
        event.returnValue = '';
    }
}
onBeforeRouteLeave(() => !busy.value);
onMounted(() => {
    void load();
    void loadLevels();
    window.addEventListener('beforeunload', beforeUnload);
});
onBeforeUnmount(() => {
    listSequence++;
    detailSequence++;
    accountSequence++;
    window.removeEventListener('beforeunload', beforeUnload);
});
</script>
<template>
<PageLayout class="admission-page" title="Pendaftaran siswa"
  subtitle="Kelola calon, periksa biaya, lalu catat penerimaan atau finalisasi sesuai kebutuhan."
  :surface="false"><template #actions><Button label="Daftar calon baru" :disabled="busy||loading"
      @click="openCreate"><template #icon>
        <Icon name="user-plus" />
      </template></Button></template>
  <section class="admission-panel">
    <details class="admission-guide">
      <summary>Alur calon, penerimaan, dan finalisasi</summary>
      <ol>
        <li>Daftarkan calon dengan biaya formulir serta sit-in/observasi sesuai kesepakatan.</li>
        <li>Catat penerimaan hanya untuk komponen yang benar-benar dibayar. Jurnalnya menunggu pencatatan
          Finance.</li>
        <li>Finalisasi calon menjadi siswa aktif dengan SPP yang ditetapkan. Tindakan ini tidak mencatat
          pembayaran atau menganggap biaya lunas.</li>
      </ol>
    </details>
    <header class="admission-heading">
      <h2>Daftar calon siswa</h2>
      <p>Periksa rincian untuk melihat komponen biaya, bukti penerimaan, dan tindakan yang tersedia.</p>
    </header>
    <div class="admission-controls">
      <div class="admission-field"><label for="admission-search">Cari calon siswa</label>
        <SearchField input-id="admission-search" v-model="query" placeholder="Nama, jenjang, atau status"
          hint="Mencari pada seluruh pendaftaran yang dimuat, termasuk halaman lain." />
      </div>
      <div class="admission-field"><label for="admission-status">Status pendaftaran</label><Select
          input-id="admission-status" placeholder="Semua status" v-model="status" :options="statusOptions"
          option-label="label" option-value="value"><template #dropdownicon>
            <Icon name="caret-down" />
          </template></Select></div><Button label="Muat ulang daftar" severity="secondary"
        :disabled="loading||busy" @click="load"><template #icon>
          <Icon name="arrows-clockwise" />
        </template></Button>
    </div>
    <div v-if="levelsError" class="admission-notice">
      <Message severity="warn" :closable="false">{{ levelsError }} Data calon tetap ditampilkan.</Message>
      <Button label="Muat ulang jenjang" severity="secondary" :disabled="levelsLoading" @click="loadLevels" />
    </div>
    <div v-if="rows.some(row=>row.perlu_rekonsiliasi)" class="admission-notice">
      <Message severity="warn" :closable="false">Data lama yang belum jelas ditandai Perlu dicocokkan. Total,
        penerimaan, dan sisa belum dianggap pasti; penerimaan baru diblokir sampai rincian dicocokkan.
      </Message>
    </div>
    <PendaftaranDirectory :rows="filtered" :names="names" :loading="loading" :error="error"
      :filtered="!!query.trim()||!!status" @detail="detail" @retry="load" @clear="query='';status=null" />
  </section>
  <PendaftaranFormDialog v-model="formOpen" :row="editing" :levels="levels" :levels-loading="levelsLoading"
    :levels-error="levelsError" :saving="saving" :error="formError" @save="save"
    @reload-levels="loadLevels" />
  <PendaftaranPaymentDialog v-model="paymentOpen" :row="paymentTarget" :accounts="accounts"
    :accounts-loading="accountsLoading" :accounts-error="accountsError" :saving="paymentSaving"
    :error="paymentError" :uncertain="paymentUncertain" @save="pay" @retry="retryPayment"
    @reload-accounts="loadAccounts" />
  <Dialog :visible="!!detailTarget" @update:visible="closeDetail" header="Rincian pendaftaran"
    class="admission-dialog" modal :closable="!busy" :close-on-escape="!busy"><template #closeicon>
      <Icon name="x" />
    </template>
    <div v-if="detailTarget" class="admission-form">
      <div>
        <p class="admission-person">{{ detailTarget.nama_calon }}</p>
        <p class="admission-help">{{ dateLabel(detailTarget.tanggal_daftar) }} ·
          {{ detailTarget.jenjang?names.get(detailTarget.jenjang)??'Nama jenjang belum dimuat':'Jenjang belum dipilih' }}
        </p>
        <Tag :value="statusLabels[detailTarget.status]" :severity="statusSeverity[detailTarget.status]" />
      </div>
      <p v-if="detailLoading" role="status">Memeriksa rincian terbaru…</p>
      <div v-if="detailError" class="admission-notice">
        <Message severity="error" :closable="false">{{ detailError }} Tindakan menunggu rincian terbaru
          berhasil dimuat.</Message><Button label="Muat ulang rincian" severity="secondary"
          @click="detail(detailTarget)" />
      </div>
      <Message v-if="detailTarget.perlu_rekonsiliasi" severity="warn" :closable="false">Perlu dicocokkan
        dengan bukti sekolah. Nilai pendaftaran lama {{ money(detailTarget.biaya_pendaftaran) }} tetap
        tersimpan; total, penerimaan, dan sisa belum dapat dipastikan.</Message>
      <dl v-else class="admission-detail-grid">
        <div>
          <dt>Total biaya</dt>
          <dd>{{ money(detailTarget.total_biaya) }}</dd>
        </div>
        <div>
          <dt>Diterima</dt>
          <dd>{{ money(detailTarget.total_terbayar) }}</dd>
        </div>
        <div>
          <dt>Sisa</dt>
          <dd>{{ money(detailTarget.sisa_biaya) }}</dd>
        </div>
      </dl>
      <h3>Komponen biaya</h3>
      <div class="admission-payment-components">
        <div v-for="option in components(detailTarget)" :key="option.kode"><strong>{{ option.label }}</strong>
          <p class="admission-help">{{ money(option.nominal==null?null:option.nominal/100) }} ·
            {{ option.paid==null?'Penerimaan belum dipastikan':option.paid?'Sudah diterima':option.nominal===0?'Tidak dikenakan':'Belum diterima' }}
          </p>
        </div>
      </div>
      <h3>Bukti penerimaan</h3>
      <p v-if="!detailTarget.pembayaran.length" class="admission-help">Belum ada catatan penerimaan pada data
        ini.</p>
      <ul v-else class="admission-receipts">
        <li v-for="receipt in detailTarget.pembayaran" :key="receipt.jurnal_id">
          <strong>{{ receipt.no_bukti }}</strong>
          <p>{{ money(receipt.nominal) }} · {{ dateLabel(receipt.tanggal) }}</p>
          <p>{{ receipt.komponen.map(code=>code==='FORMULIR'?'Formulir':'Sit-in / observasi').join(' + ') }}
          </p>
          <Tag :value="receipt.dibatalkan?'Dibatalkan':journalLabels[receipt.status]??receipt.status"
            :severity="receipt.dibatalkan?'warn':receipt.status==='POSTED'?'success':'info'" />
        </li>
      </ul>
      <p class="admission-help">Data ini menampilkan jurnal terakhir tiap komponen yang tersedia. Koreksi
        penerimaan dilakukan oleh Finance/Kepala Sekolah sesuai status jurnal.</p>
      <Message v-if="actionError" severity="error" :closable="false">{{ actionError }}</Message>
    </div><template #footer>
      <div v-if="detailTarget" class="admission-detail-actions"><template
          v-if="!detailLoading&&!detailError"><Button v-if="editable(detailTarget)" label="Ubah calon"
            severity="secondary" :disabled="busy" @click="openEdit(detailTarget)"><template #icon>
              <Icon name="pencil-simple" />
            </template></Button><Button v-if="editable(detailTarget)" label="Hapus calon" severity="danger"
            text :disabled="busy" @click="remove(detailTarget)"><template #icon>
              <Icon name="trash" />
            </template></Button><Button v-if="finalizable(detailTarget)" label="Finalisasi"
            severity="secondary" :disabled="busy" @click="openFinal(detailTarget)" /><Button
            v-if="receivable(detailTarget)" label="Catat penerimaan" :disabled="busy"
            @click="openPayment(detailTarget)"><template #icon>
              <Icon name="money" />
            </template></Button>
          <RouterLink v-if="detailTarget.status==='REGISTERED'&&detailTarget.siswa"
            class="admission-student-link" to="/siswa">Buka data siswa
            <Icon name="arrow-right" />
          </RouterLink>
        </template><Button label="Tutup rincian" severity="secondary" text :disabled="busy"
          @click="closeDetail" /></div>
    </template>
  </Dialog>
  <Dialog :visible="finalOpen" @update:visible="value=>{if(!finalSaving)finalOpen=value}"
    header="Finalisasi pendaftaran" class="admission-dialog" modal :closable="!finalSaving"
    :close-on-escape="!finalSaving"><template #closeicon>
      <Icon name="x" />
    </template>
    <form id="admission-final" @submit.prevent="finalize">
      <p class="admission-person">{{ finalTarget?.nama_calon }}</p>
      <p class="admission-help">Finalisasi membuat calon menjadi siswa aktif. Finalisasi tidak mencatat
        penerimaan uang atau menganggap biaya sudah lunas.</p>
      <div class="admission-field"><label for="spp">SPP bulanan yang disepakati (wajib)</label>
        <InputNumber input-id="spp" v-model="spp" :min="0" :max-fraction-digits="2" locale="id-ID"
          :disabled="finalSaving||finalUncertain" :invalid="!!finalError&&cents(spp)==null" fluid /><small>Isi
          0 jika SPP memang tidak dikenakan. Profil siswa dapat dilengkapi setelah finalisasi.</small>
      </div>
      <Message v-if="finalError" severity="error" :closable="false" role="alert">{{ finalError }} Input tetap
        ada.</Message>
      <Message v-if="finalUncertain" severity="warn" :closable="false">Hasil sebelumnya belum pasti. Coba
        ulang menggunakan nominal SPP yang sama untuk memeriksa hasil finalisasi.</Message>
    </form><template #footer><Button label="Kembali" severity="secondary" :disabled="finalSaving"
        @click="finalOpen=false" /><Button :label="finalUncertain?'Coba ulang finalisasi':'Finalisasi siswa'"
        form="admission-final" type="submit" :disabled="finalSaving" :loading="finalSaving" /></template>
  </Dialog>
</PageLayout>
</template>
<style scoped>
.admission-student-link {
  display: inline-flex;
  align-items: center;
  gap: var(--bee-space-2);
  min-height: 44px;
  color: var(--bee-color-brand);
  text-decoration: none;
  font-size: var(--bee-type-ui)
}
</style>
