<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, reactive, ref, watch } from 'vue';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import Select from 'primevue/select';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import DatePicker from 'primevue/datepicker';
import Message from 'primevue/message';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { calendarTextMatches, formatLocalDate } from '@/core/format';
import type { Jenjang, PendaftaranSiswa, PendaftaranSiswaInput } from '@/types/api';
import { cents, money } from './presentation';
const props = defineProps<{
    modelValue: boolean;
    row: PendaftaranSiswa | null;
    levels: Jenjang[];
    levelsLoading: boolean;
    levelsError: string;
    saving: boolean;
    error: string;
}>();
const emit = defineEmits<{
    'update:modelValue': [
        value: boolean
    ];
    save: [
        payload: PendaftaranSiswaInput
    ];
    reloadLevels: [
    ];
}>();
const form = reactive({ nama_calon: '', jenjang: null as number | null, tanggal_daftar: new Date() as Date | null, biaya_sitin: null as number | null, biaya_formulir: null as number | null });
const attempted = ref(false), badDate = ref(false);
const total = computed(() => {
    const sitin = cents(form.biaya_sitin), fee = cents(form.biaya_formulir);
    return sitin == null || fee == null || !Number.isSafeInteger(sitin + fee) ? null : (sitin + fee) / 100;
});
const dateInvalid = computed(() => badDate.value || !form.tanggal_daftar || !Number.isFinite(form.tanggal_daftar.getTime()));
watch(() => props.modelValue, open => {
    if (open) {
        const row = props.row;
        attempted.value = false;
        badDate.value = false;
        Object.assign(form, { nama_calon: row?.nama_calon ?? '', jenjang: row?.jenjang ?? null, tanggal_daftar: row ? new Date(row.tanggal_daftar + 'T00:00:00') : new Date(), biaya_sitin: row ? Number(row.biaya_sitin) : null, biaya_formulir: row?.biaya_formulir == null ? null : Number(row.biaya_formulir) });
    }
}, { immediate: true });
function checkDate(event: Event) {
    badDate.value = !calendarTextMatches((event.target as HTMLInputElement).value, form.tanggal_daftar);
}
function save() {
    attempted.value = true;
    if (props.saving || !form.nama_calon.trim() || form.nama_calon.length > 100 || dateInvalid.value || total.value == null)
        return;
    emit('save', { nama_calon: form.nama_calon.trim(), jenjang: form.jenjang, tanggal_daftar: formatLocalDate(form.tanggal_daftar!), biaya_sitin: form.biaya_sitin!.toFixed(2), biaya_formulir: form.biaya_formulir!.toFixed(2) });
}
</script>
<template>
<Dialog :visible="modelValue" @update:visible="value=>{if(!saving)emit('update:modelValue',value)}"
  :header="row?'Ubah calon siswa':'Daftar calon siswa'" class="admission-dialog" modal :closable="!saving"
  :close-on-escape="!saving"><template #closeicon>
    <Icon name="x" />
  </template>
  <form id="admission-form" @submit.prevent="save">
    <Message v-if="row?.perlu_rekonsiliasi" severity="warn" :closable="false">Nilai lama
      {{ money(row.biaya_pendaftaran) }} tetap menjadi catatan historis. Isi rincian biaya setelah dicocokkan
      dengan bukti; nilai lama tidak disalin otomatis.</Message>
    <fieldset :disabled="saving" class="admission-form">
      <div class="admission-field"><label for="nama-calon">Nama calon (wajib)</label>
        <InputText id="nama-calon" :disabled="saving" v-model="form.nama_calon" :maxlength="100"
          :invalid="attempted&&!form.nama_calon.trim()"
          :aria-describedby="attempted&&!form.nama_calon.trim()?'admission-name-error':undefined" fluid />
        <small v-if="attempted&&!form.nama_calon.trim()" id="admission-name-error"
          class="admission-field-error">Isi nama calon siswa.</small>
      </div>
      <div class="admission-field"><label for="jenjang">Jenjang</label><Select :key="(saving||levelsLoading) ? 'locked' : 'editable'" input-id="jenjang"
          v-model="form.jenjang" :options="levels" option-label="nama" option-value="id" show-clear
          placeholder="Belum dipilih" :disabled="saving||levelsLoading" fluid><template #dropdownicon>
            <Icon name="caret-down" />
          </template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select><small>Jenjang dapat dilengkapi kemudian.</small>
        <div v-if="levelsError">
          <Message severity="warn" :closable="false">{{ levelsError }}</Message><Button
            label="Muat ulang jenjang" severity="secondary" :disabled="saving"
            @click="emit('reloadLevels')" />
        </div>
      </div>
      <div class="admission-field"><label for="tanggal">Tanggal daftar (wajib)</label>
        <DatePicker :key="saving?'locked':'editable'" input-id="tanggal" v-model="form.tanggal_daftar" date-format="dd/mm/yy" @input="checkDate"
          @update:model-value="badDate=false" :disabled="saving" :invalid="attempted&&dateInvalid"
          :input-props="{'aria-invalid':attempted&&dateInvalid,'aria-describedby':attempted&&dateInvalid?'admission-date-error':undefined}"
          fluid><template #previcon>
            <Icon name="caret-left" />
          </template><template #nexticon>
            <Icon name="caret-right" />
          </template></DatePicker><small v-if="attempted&&dateInvalid" id="admission-date-error"
          class="admission-field-error">Periksa atau pilih ulang tanggal daftar.</small>
      </div>
      <div class="admission-fee-fields">
        <div class="admission-field"><label for="formulir">Biaya formulir (wajib)</label>
          <InputNumber input-id="formulir" :disabled="saving" v-model="form.biaya_formulir" :min="0"
            :max-fraction-digits="2" locale="id-ID" :invalid="attempted&&cents(form.biaya_formulir)==null"
            fluid />
        </div>
        <div class="admission-field"><label for="sitin">Biaya sit-in / observasi (wajib)</label>
          <InputNumber input-id="sitin" :disabled="saving" v-model="form.biaya_sitin" :min="0"
            :max-fraction-digits="2" locale="id-ID" :invalid="attempted&&cents(form.biaya_sitin)==null"
            fluid />
        </div>
      </div><small>Isi biaya sesuai kesepakatan sekolah. Isi 0 jika komponen memang tidak dikenakan.</small>
    </fieldset>
    <div class="admission-total"><span>Total biaya
        pendaftaran</span><strong>{{ total==null?'Isi kedua komponen':money(total) }}</strong></div>
    <Message v-if="attempted&&total==null" severity="error" :closable="false">Isi kedua komponen biaya dengan
      angka nol atau lebih yang dapat dicatat.</Message>
    <Message v-if="error" severity="error" :closable="false" role="alert">{{ error }} Input tetap ada.
    </Message>
  </form>
  <template #footer><Button label="Kembali" severity="secondary" :disabled="saving"
      @click="emit('update:modelValue',false)" /><Button label="Simpan calon" type="submit"
      form="admission-form" :loading="saving" :disabled="saving" /></template>
</Dialog>
</template>
