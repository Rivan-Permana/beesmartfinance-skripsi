<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import Textarea from 'primevue/textarea';
import Message from 'primevue/message';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { friendlyError, notifySuccess } from '@/core/errors';
import type { MenuKatering } from '@/types/api';
import { formatTanggalId, menuKateringApi, weekdaysOfWeek, weekRange } from './api';
const emit = defineEmits<{
    busy: [
        value: boolean
    ];
}>();
const toast = useToast(), confirm = useConfirm();
const anchor = ref(new Date()), records = ref<MenuKatering[]>([]), loading = ref(false), error = ref(''), actionError = ref('');
const dates = computed(() => weekdaysOfWeek(anchor.value));
const weekLabel = computed(() => `${formatTanggalId(dates.value[0]!)} – ${formatTanggalId(dates.value[4]!)}`);
const rows = computed(() => dates.value.map(date => ({ date, menu: records.value.find(row => row.tanggal === date) })));
const visible = ref(false), saving = ref(false), editing = ref<number | null>(null), formError = ref(''), uncertain = ref(false);
const form = reactive({ tanggal: '', keterangan: '' }), file = ref<File | null>(null), preview = ref<string | null>(null);
let sequence = 0;
function message(e: unknown) {
    const value = friendlyError(e, 'Menu belum berhasil diproses');
    return [value.summary, value.detail].filter(Boolean).join('. ');
}
watch(saving, value => emit('busy', value));
async function load() {
    const request = ++sequence, range = weekRange([...dates.value]);
    loading.value = true;
    error.value = '';
    records.value = [];
    try {
        const result = await menuKateringApi.listAll(range);
        if (request === sequence)
            records.value = result;
    }
    catch (e) {
        if (request === sequence)
            error.value = message(e);
    }
    finally {
        if (request === sequence)
            loading.value = false;
    }
}
function clearPreview() {
    if (preview.value?.startsWith('blob:'))
        URL.revokeObjectURL(preview.value);
    preview.value = null;
}
function open(date: string, row?: MenuKatering) {
    if (saving.value)
        return;
    clearPreview();
    editing.value = row?.id ?? null;
    form.tanggal = date;
    form.keterangan = row?.keterangan ?? '';
    file.value = null;
    preview.value = row?.gambar_url ?? null;
    formError.value = '';
    uncertain.value = false;
    visible.value = true;
}
function chooseFile(event: Event) {
    const selected = (event.target as HTMLInputElement).files?.[0];
    if (!selected)
        return;
    if (!selected.type.startsWith('image/')) {
        formError.value = 'Pilih file gambar untuk foto menu.';
        return;
    }
    clearPreview();
    file.value = selected;
    preview.value = URL.createObjectURL(selected);
    formError.value = '';
}
async function save() {
    if (saving.value)
        return;
    formError.value = '';
    if (!form.keterangan.trim() && !file.value && !preview.value) {
        formError.value = 'Isi keterangan atau pilih foto menu terlebih dahulu.';
        return;
    }
    if (form.keterangan.length > 255) {
        formError.value = 'Keterangan maksimal 255 karakter.';
        return;
    }
    saving.value = true;
    try {
        // shortcut: creates have no request ID; inspect the unique date after an ambiguous response.
        if (uncertain.value && !editing.value) {
            const existing = await menuKateringApi.listAll({ tanggal: form.tanggal });
            if (existing.length) {
                formError.value = 'Menu tanggal ini sudah ada. Tutup form dan muat ulang menu untuk memeriksa hasil, lalu pilih Ubah menu bila perlu.';
                return;
            }
        }
        if (editing.value) {
            if (file.value)
                await menuKateringApi.updateWithForm(editing.value, { keterangan: form.keterangan, gambar: file.value });
            else
                await menuKateringApi.update(editing.value, { keterangan: form.keterangan });
        }
        else
            await menuKateringApi.createWithForm({ tanggal: form.tanggal, keterangan: form.keterangan, gambar: file.value ?? undefined });
        notifySuccess(toast, 'Menu tersimpan');
        visible.value = false;
        clearPreview();
        await load();
    }
    catch (e) {
        uncertain.value = true;
        formError.value = message(e) + '. Input tetap ada. Hasil pengiriman akan diperiksa sebelum mencoba membuat menu kembali.';
    }
    finally {
        saving.value = false;
    }
}
function remove(row: MenuKatering) {
    confirm.require({ header: 'Hapus menu?', message: `Menu ${formatTanggalId(row.tanggal)} beserta fotonya akan dihapus dari daftar.`, acceptLabel: 'Hapus menu', rejectLabel: 'Kembali', acceptProps: { severity: 'danger' }, accept: async () => {
            if (saving.value)
                return;
            saving.value = true;
            actionError.value = '';
            try {
                await menuKateringApi.remove(row.id);
                notifySuccess(toast, 'Menu dihapus');
                await load();
            }
            catch (e) {
                actionError.value = message(e) + '. Muat ulang menu untuk memeriksa hasil sebelum mencoba lagi.';
            }
            finally {
                saving.value = false;
            }
        } });
}
function shift(delta: number) {
    const next = new Date(anchor.value);
    next.setDate(next.getDate() + delta * 7);
    anchor.value = next;
}
watch(anchor, load);
onMounted(load);
onBeforeRouteLeave(() => !saving.value);
onBeforeUnmount(() => {
    sequence++;
    clearPreview();
    emit('busy', false);
});
</script>
<template>
<section class="service-panel">
  <header class="service-heading">
    <h2>Menu mingguan</h2>
    <p>Atur menu Senin–Jumat. Keterangan, foto, atau keduanya dapat digunakan.</p>
  </header>
  <div class="service-toolbar">
    <div class="menu-week-controls"><Button aria-label="Minggu sebelumnya" severity="secondary"
        :disabled="saving" @click="shift(-1)"><template #icon>
          <Icon name="caret-left" />
        </template></Button><strong>{{ weekLabel }}</strong><Button aria-label="Minggu berikutnya"
        severity="secondary" :disabled="saving" @click="shift(1)"><template #icon>
          <Icon name="caret-right" />
        </template></Button></div>
    <div class="menu-week-controls"><Button label="Minggu ini" severity="secondary" :disabled="saving"
        @click="anchor=new Date()" /><Button label="Muat ulang menu" severity="secondary" text
        :disabled="saving||loading" @click="load"><template #icon>
          <Icon name="arrows-clockwise" />
        </template></Button></div>
  </div>
  <div v-if="actionError" class="service-notice">
    <Message severity="error" :closable="false">{{ actionError }}</Message>
  </div>
  <div v-if="loading" class="service-empty" role="status">
    <Icon name="arrows-clockwise" />
    <p>Memuat menu minggu ini…</p>
  </div>
  <div v-else-if="error" class="service-empty">
    <Icon name="warning-circle" />
    <h3>Menu belum dapat ditampilkan</h3>
    <p role="alert">{{ error }}</p><Button label="Coba muat menu" severity="secondary" @click="load" />
  </div>
  <ol v-else class="menu-days">
    <li v-for="row in rows" :key="row.date">
      <div class="menu-day-content"><small>{{ row.menu ? 'Menu tersedia' : 'Belum diisi' }}</small>
        <h3>{{ formatTanggalId(row.date) }}</h3>
        <p>
          {{ row.menu?.keterangan || (row.menu?.gambar_url ? 'Lihat foto menu untuk hari ini.' : 'Belum ada menu. Isi keterangan atau unggah foto.') }}
        </p>
        <div class="menu-day-actions"><Button :label="row.menu?'Ubah menu':'Isi menu'"
            :aria-label="`${row.menu?'Ubah menu':'Isi menu'} ${formatTanggalId(row.date)}`"
            severity="secondary" :disabled="saving" @click="open(row.date,row.menu)"><template #icon>
              <Icon :name="row.menu?'pencil-simple':'plus'" />
            </template></Button><Button v-if="row.menu"
            :aria-label="`Hapus menu ${formatTanggalId(row.date)}`" severity="danger" text :disabled="saving"
            @click="remove(row.menu)"><template #icon>
              <Icon name="trash" />
            </template></Button></div>
      </div><img v-if="row.menu?.gambar_url" :src="row.menu.gambar_url"
        :alt="`Foto menu ${formatTanggalId(row.date)}`" loading="lazy" />
    </li>
  </ol>
</section>
<Dialog :visible="visible" @update:visible="value=>{if(!saving)visible=value}"
  :header="editing?'Ubah menu':'Isi menu'" class="service-dialog" modal :closable="!saving"
  :close-on-escape="!saving"><template #closeicon>
    <Icon name="x" />
  </template>
  <form id="catering-menu-form" @submit.prevent="save">
    <fieldset class="service-form" :disabled="saving">
      <div class="service-field"><label>Tanggal
          menu</label><strong>{{ formatTanggalId(form.tanggal) }}</strong></div>
      <div class="service-field"><label for="menu-keterangan">Keterangan menu</label><Textarea
          id="menu-keterangan" v-model="form.keterangan" rows="4" :maxlength="255" auto-resize fluid
          aria-describedby="menu-input-help" placeholder="Contoh: Nasi, ayam, sayur bayam, dan pepaya" />
      </div>
      <div class="service-field"><label for="menu-foto">Foto menu</label>
        <span class="menu-file-picker"><Icon name="image" /><span>Pilih foto</span><input id="menu-foto" type="file" accept="image/*" aria-label="Pilih foto menu" aria-describedby="menu-input-help menu-file-name" @change="chooseFile" /></span>
        <small id="menu-file-name">{{ file?.name || (preview ? 'Foto tersimpan digunakan.' : 'Belum ada foto dipilih.') }}</small><small
          id="menu-input-help">Isi keterangan, unggah foto, atau keduanya. Keterangan maksimal 255
          karakter.</small><img v-if="preview" :src="preview" alt="Pratinjau foto menu katering"
          class="service-preview" /></div>
    </fieldset>
    <Message v-if="formError" severity="error" :closable="false" role="alert">{{ formError }}</Message>
  </form>
  <template #footer><Button label="Kembali" severity="secondary" :disabled="saving"
      @click="visible=false" /><Button label="Simpan menu" type="submit" form="catering-menu-form"
      :loading="saving" :disabled="saving" /></template>
</Dialog>
</template>
<style scoped>
.menu-file-picker{display:inline-flex;position:relative;align-items:center;gap:var(--bee-space-2);justify-self:start;min-height:44px;padding:var(--bee-space-2) var(--bee-space-4);border:1px solid var(--bee-color-control-border);border-radius:var(--bee-radius-control);font-size:var(--bee-type-ui);cursor:pointer}
.menu-file-picker input[type=file]{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}
.menu-file-picker:focus-within{outline:2px solid var(--bee-color-brand);outline-offset:2px}
#menu-file-name{overflow-wrap:anywhere}

.menu-week-controls {
  display: flex;
  align-items: center;
  gap: var(--bee-space-3);
  min-width: 0
}

.menu-week-controls strong {
  font-size: var(--bee-type-ui);
  font-weight: 500;
  max-width: 28ch;
  text-align: center
}

.menu-days {
  list-style: none;
  padding: 0;
  margin: 0
}

.menu-days li {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: var(--bee-space-5);
  padding: var(--bee-space-5);
  border-top: 1px solid var(--app-border)
}

.menu-day-content {
  min-width: 0;
  flex: 1
}

.menu-day-content>small {
  color: var(--app-text-muted);
  font-size: var(--bee-type-caption)
}

.menu-day-content h3 {
  font-size: var(--bee-type-section);
  font-weight: 500;
  margin: var(--bee-space-2) 0
}

.menu-day-content p {
  max-width: 65ch;
  overflow-wrap: anywhere;
  color: var(--app-text-muted);
  font-size: var(--bee-type-ui)
}

.menu-day-actions {
  display: flex;
  gap: var(--bee-space-2);
  flex-wrap: wrap
}

.menu-days img {
  width: 180px;
  max-height: 160px;
  object-fit: contain;
  border: 1px solid var(--app-border);
  border-radius: var(--bee-radius-control)
}

@container service-panel (max-width:500px) {
  .menu-days li {
    flex-direction: column;
    padding: var(--bee-space-4)
  }

  .menu-days img {
    width: 100%;
    max-height: 220px
  }

  .menu-week-controls strong {
    font-size: var(--bee-type-caption)
  }
}
</style>
