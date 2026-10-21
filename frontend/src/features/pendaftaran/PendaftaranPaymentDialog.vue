<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import DatePicker from 'primevue/datepicker';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import Message from 'primevue/message';
import Icon from '@/shared/components/PhosphorIcon.vue';
import { calendarTextMatches, formatLocalDate } from '@/core/format';
import type { BayarPendaftaranInput, Coa, PendaftaranSiswa } from '@/types/api';
import { components, money, receivable } from './presentation';
const props = defineProps<{
    modelValue: boolean;
    row: PendaftaranSiswa | null;
    accounts: Coa[];
    accountsLoading: boolean;
    accountsError: string;
    saving: boolean;
    error: string;
    uncertain: boolean;
}>();
const emit = defineEmits<{
    'update:modelValue': [
        value: boolean
    ];
    save: [
        payload: BayarPendaftaranInput
    ];
    retry: [
    ];
    reloadAccounts: [
    ];
}>();
const form = reactive({ tanggal: new Date() as Date | null, no_bukti: '', akun_kas: null as string | null });
const selected = ref<('SITIN' | 'FORMULIR')[]>([]), attempted = ref(false), badDate = ref(false);
const options = computed(() => props.row ? components(props.row) : []);
const total = computed(() => options.value.filter(row => selected.value.includes(row.kode) && row.paid === false && (row.nominal ?? 0) > 0).reduce((sum, row) => sum + row.nominal!, 0));
const invalidDate = computed(() => badDate.value || !form.tanggal || !Number.isFinite(form.tanggal.getTime()));
watch(() => props.modelValue, open => {
    if (open) {
        Object.assign(form, { tanggal: new Date(), no_bukti: '', akun_kas: null });
        attempted.value = false;
        badDate.value = false;
        selected.value = options.value.filter(row => row.paid === false && (row.nominal ?? 0) > 0).map(row => row.kode);
    }
}, { immediate: true });
function dateInput(event: Event) {
    badDate.value = !calendarTextMatches((event.target as HTMLInputElement).value, form.tanggal);
}
function save() {
    attempted.value = true;
    if (props.saving || props.uncertain || props.accountsLoading || props.accountsError || !props.row || !receivable(props.row) || invalidDate.value || !form.no_bukti.trim() || form.no_bukti.length > 50 || !props.accounts.some(row => row.kode_akun === form.akun_kas) || total.value <= 0)
        return;
    if (selected.value.some(code => !options.value.some(row => row.kode === code && row.paid === false && (row.nominal ?? 0) > 0)))
        return;
    emit('save', { tanggal: formatLocalDate(form.tanggal!), no_bukti: form.no_bukti.trim(), akun_kas: form.akun_kas!, komponen: [...selected.value], nominal: (total.value / 100).toFixed(2) });
}
</script>
<template>
<Dialog :visible="modelValue" @update:visible="value=>{if(!saving)emit('update:modelValue',value)}"
  header="Catat penerimaan pendaftaran" class="admission-dialog" modal :closable="!saving"
  :close-on-escape="!saving"><template #closeicon>
    <Icon name="x" />
  </template>
  <form id="admission-payment" @submit.prevent="save">
    <p class="admission-person">{{ row?.nama_calon }}</p>
    <p class="admission-help">Pilih komponen yang benar-benar diterima. Setiap pilihan mencakup nilai penuh
      komponen tersebut.</p>
    <fieldset class="admission-form" :disabled="saving||uncertain">
      <div class="admission-payment-components"><label v-for="option in options" :key="option.kode"
          :for="`bayar-${option.kode}`"><input :id="`bayar-${option.kode}`" type="checkbox"
            :value="option.kode" v-model="selected"
            :disabled="saving||uncertain||option.paid!==false||(option.nominal??0)<=0" /><span><strong>{{ option.label }}</strong><small>{{ money(option.nominal==null?null:option.nominal/100) }}
              ·
              {{ option.paid?'Sudah diterima':option.nominal===0?'Tidak dikenakan':'Belum diterima' }}</small></span></label>
      </div>
      <div class="admission-field"><label for="bayar-tanggal">Tanggal penerimaan (wajib)</label>
        <DatePicker :key="saving||uncertain?'locked':'editable'" input-id="bayar-tanggal" v-model="form.tanggal" date-format="dd/mm/yy"
          :disabled="saving||uncertain" @input="dateInput" @update:model-value="badDate=false"
          :invalid="attempted&&invalidDate"
          :input-props="{'aria-invalid':attempted&&invalidDate,'aria-describedby':attempted&&invalidDate?'payment-date-error':undefined}"
          fluid><template #previcon>
            <Icon name="caret-left" />
          </template><template #nexticon>
            <Icon name="caret-right" />
          </template></DatePicker><small v-if="attempted&&invalidDate" id="payment-date-error"
          class="admission-field-error">Periksa atau pilih ulang tanggal penerimaan.</small>
      </div>
      <div class="admission-field"><label for="bayar-bukti">Nomor bukti penerimaan (wajib)</label>
        <InputText id="bayar-bukti" :disabled="saving||uncertain" v-model="form.no_bukti" :maxlength="50"
          :invalid="attempted&&!form.no_bukti.trim()" fluid />
      </div>
      <div class="admission-field"><label for="bayar-kas">Kas/Bank penerima (wajib)</label><Select :key="(saving||uncertain||accountsLoading) ? 'locked' : 'editable'"
          input-id="bayar-kas" v-model="form.akun_kas" :options="accounts"
          :option-label="account=>`${account.kode_akun} · ${account.nama_akun}`" option-value="kode_akun"
          placeholder="Pilih Kas/Bank aktif" :loading="accountsLoading"
          :disabled="saving||uncertain||accountsLoading" :invalid="attempted&&!form.akun_kas" fluid><template
            #dropdownicon>
            <Icon name="caret-down" />
          </template></Select></div>
    </fieldset>
    <div v-if="accountsError||(!accountsLoading&&!accounts.length)" class="admission-notice">
      <Message severity="warn" :closable="false">
        {{ accountsError||'Belum ada akun Kas/Bank aktif yang memenuhi syarat penerimaan.' }}</Message><Button
        label="Muat ulang Kas/Bank" severity="secondary" :disabled="saving" @click="emit('reloadAccounts')" />
    </div>
    <div class="admission-total"><span>Jumlah diterima</span><strong>{{ money(total/100) }}</strong></div>
    <p class="admission-help">Penerimaan membuat jurnal yang menunggu pencatatan Finance. Finalisasi siswa
      dikerjakan terpisah.</p>
    <Message v-if="attempted&&(!selected.length||!form.no_bukti.trim()||!form.akun_kas)" severity="error"
      :closable="false">Pilih komponen, tanggal, nomor bukti, dan Kas/Bank penerima.</Message>
    <Message v-if="error" severity="error" :closable="false" role="alert">{{ error }} Input tetap ada.
    </Message>
    <Message v-if="uncertain" severity="warn" :closable="false">Hasil pengiriman belum pasti. Coba ulang
      memakai rincian yang sama; backend memeriksa penerimaan sebelumnya. Untuk mengubah rincian, kembali dan
      muat ulang pendaftaran lebih dulu.</Message>
  </form><template #footer><Button label="Kembali" severity="secondary" :disabled="saving"
      @click="emit('update:modelValue',false)" /><Button v-if="uncertain" label="Coba ulang penerimaan"
      :disabled="saving" :loading="saving" @click="emit('retry')" /><Button v-else label="Simpan penerimaan"
      type="submit" form="admission-payment"
      :disabled="saving||accountsLoading||!!accountsError||!accounts.length" :loading="saving" /></template>
</Dialog>
</template>
