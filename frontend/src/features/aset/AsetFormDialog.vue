<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useConfirm } from 'primevue/useconfirm'
import { calendarTextMatches, formatLocalDate } from '@/core/format'
import { filterCoaAsetTetap, filterCoaBebanPenyusutan } from '@/features/coa/filters'
import { cents, money } from '@/features/kepegawaian/payroll'
import Icon from '@/shared/components/PhosphorIcon.vue'
import type { Coa, FixedAsset } from '@/types/api'

const props = defineProps<{
  row: FixedAsset | null
  accounts: Coa[]
  accountsLoading: boolean
  accountsError: string
  saving: boolean
  uncertain: boolean
  error: string
}>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{
  save: [payload: Partial<FixedAsset>]
  reloadAccounts: []
  review: []
  dirty: [value: boolean]
}>()
const confirm = useConfirm()
const form = reactive({ nama: '', tanggal: null as Date | null, harga: null as number | null, umur: null as number | null, akunAset: null as string | null, akunAkumulasi: null as string | null, akunBeban: null as string | null })
const attempted = ref(false), badDate = ref(false), initial = ref(''), element = ref<HTMLFormElement | null>(null), errorElement = ref<HTMLElement | null>(null)
const locked = computed(() => props.saving || props.uncertain)
const dirty = computed(() => visible.value && JSON.stringify(form) !== initial.value)
const dateInvalid = computed(() => badDate.value || !form.tanggal || !Number.isFinite(form.tanggal.getTime()))
const priceInvalid = computed(() => cents(form.harga) == null || (form.harga ?? 0) <= 0)
const lifeInvalid = computed(() => !Number.isInteger(form.umur) || !form.umur || form.umur < 1 || form.umur > 2147483647)
const invalid = computed(() => !form.nama.trim() || form.nama.trim().length > 150 || dateInvalid.value || priceInvalid.value || lifeInvalid.value || !form.akunAset || !form.akunAkumulasi || !form.akunBeban)

function options(filtered: Coa[], selected: string | null) {
  const selectedAccount = props.accounts.find(account => account.kode_akun === selected)
  if (selected && !selectedAccount) return [{ value: selected, label: `${selected} · Akun tidak tersedia dalam daftar` }, ...filtered.map(account => ({ value: account.kode_akun, label: `${account.kode_akun} · ${account.nama_akun}` }))]
  const list = selectedAccount && !filtered.some(account => account.kode_akun === selected) ? [selectedAccount, ...filtered] : filtered
  return list.map(account => ({ value: account.kode_akun, label: `${account.kode_akun} · ${account.nama_akun}${account.is_active ? '' : ' (nonaktif)'}` }))
}
const assetOptions = computed(() => options(filterCoaAsetTetap(props.accounts), form.akunAset))
const accumulationOptions = computed(() => options(filterCoaAsetTetap(props.accounts), form.akunAkumulasi))
const expenseOptions = computed(() => options(filterCoaBebanPenyusutan(props.accounts), form.akunBeban))

watch(visible, open => {
  if (!open) return
  const row = props.row
  Object.assign(form, { nama: row?.nama ?? '', tanggal: row ? new Date(`${row.tanggal_perolehan}T12:00:00`) : new Date(), harga: row ? Number(row.harga_perolehan) : null, umur: row?.umur_manfaat_bulan ?? null, akunAset: row?.akun_aset ?? null, akunAkumulasi: row?.akun_akumulasi ?? null, akunBeban: row?.akun_beban_depr ?? null })
  attempted.value = false; badDate.value = false; initial.value = JSON.stringify(form)
}, { immediate: true })
watch(dirty, value => emit('dirty', value))
watch(() => props.error, async error => { if (error) { await nextTick(); errorElement.value?.focus() } })

function close() {
  if (props.saving) return
  if (!dirty.value || props.uncertain) { visible.value = false; return }
  confirm.require({ header: 'Tutup tanpa menyimpan?', message: 'Perubahan data aset pada form ini belum disimpan.', acceptLabel: 'Tutup tanpa menyimpan', rejectLabel: 'Lanjutkan mengisi', acceptProps: { severity: 'danger' }, accept: () => { visible.value = false } })
}
async function save() {
  if (locked.value || props.accountsLoading || props.accountsError) return
  attempted.value = true
  if (invalid.value) { await nextTick(); element.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(); return }
  emit('save', { nama: form.nama.trim(), tanggal_perolehan: formatLocalDate(form.tanggal!), harga_perolehan: form.harga!.toFixed(2), umur_manfaat_bulan: form.umur!, akun_aset: form.akunAset!, akun_akumulasi: form.akunAkumulasi!, akun_beban_depr: form.akunBeban! })
}
</script>

<template>
  <Dialog :visible="visible" @update:visible="value => { if (!value) close() }" :header="row ? 'Ubah aset tetap' : 'Tambah aset tetap'" class="employee-form-dialog asset-form-dialog" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup form aset' }"><template #closeicon><Icon name="x" /></template>
    <p class="employee-intro">Catat nilai perolehan dan akun yang digunakan saat membuat jurnal penyusutan. Metode yang tersedia saat ini adalah garis lurus.</p>
    <div v-if="accountsError" class="employee-notice"><Message severity="warn" :closable="false">{{ accountsError }}</Message><Button label="Muat ulang daftar akun" severity="secondary" :disabled="locked" :loading="accountsLoading" @click="emit('reloadAccounts')" /></div>
    <form id="asset-form" ref="element" novalidate @submit.prevent="save" :aria-busy="saving">
      <fieldset class="employee-form-section" :disabled="locked || accountsLoading"><legend>Data dan nilai aset</legend><div class="employee-fields">
        <div class="employee-field employee-full"><label for="asset-name">Nama aset (wajib)</label><InputText id="asset-name" v-model="form.nama" maxlength="150" :invalid="attempted && (!form.nama.trim() || form.nama.trim().length > 150)" :aria-invalid="attempted && (!form.nama.trim() || form.nama.trim().length > 150)" fluid /><small v-if="attempted && !form.nama.trim()" class="employee-field-error">Isi nama aset.</small></div>
        <div class="employee-field"><label for="asset-date">Tanggal perolehan (wajib)</label><DatePicker :key="locked ? 'locked' : 'editable'" input-id="asset-date" v-model="form.tanggal" date-format="dd/mm/yy" :invalid="attempted && dateInvalid" :input-props="{ 'aria-invalid': attempted && dateInvalid }" @input="badDate = !calendarTextMatches(($event.target as HTMLInputElement).value, form.tanggal)" @update:model-value="badDate = false" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted && dateInvalid" class="employee-field-error">Pilih tanggal yang valid.</small></div>
        <div class="employee-field"><label for="asset-price">Harga perolehan (Rp)</label><InputNumber input-id="asset-price" v-model="form.harga" locale="id-ID" :min="0" :max-fraction-digits="2" :invalid="attempted && priceInvalid" :input-props="{ 'aria-invalid': attempted && priceInvalid }" fluid /><small v-if="attempted && priceInvalid" class="employee-field-error">Isi nominal lebih dari nol, maksimal dua desimal.</small></div>
        <div class="employee-field"><label for="asset-life">Masa manfaat (bulan)</label><InputNumber input-id="asset-life" v-model="form.umur" :min="1" :use-grouping="false" :invalid="attempted && lifeInvalid" :input-props="{ 'aria-invalid': attempted && lifeInvalid }" fluid /><small v-if="attempted && lifeInvalid" class="employee-field-error">Isi jumlah bulan bulat minimal 1.</small></div>
      </div></fieldset>
      <fieldset class="employee-form-section" :disabled="locked || accountsLoading"><legend>Akun jurnal penyusutan</legend><div class="employee-fields">
        <div class="employee-field employee-full"><label for="asset-account">Akun aset (wajib)</label><Select input-id="asset-account" v-model="form.akunAset" :options="assetOptions" option-label="label" option-value="value" filter placeholder="Pilih akun aset" :invalid="attempted && !form.akunAset" :aria-invalid="attempted && !form.akunAset" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div class="employee-field employee-full"><label for="asset-accumulation">Akun akumulasi penyusutan (wajib)</label><Select input-id="asset-accumulation" v-model="form.akunAkumulasi" :options="accumulationOptions" option-label="label" option-value="value" filter placeholder="Pilih akun akumulasi" :invalid="attempted && !form.akunAkumulasi" :aria-invalid="attempted && !form.akunAkumulasi" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
        <div class="employee-field employee-full"><label for="asset-expense">Akun beban penyusutan (wajib)</label><Select input-id="asset-expense" v-model="form.akunBeban" :options="expenseOptions" option-label="label" option-value="value" filter placeholder="Pilih akun beban" :invalid="attempted && !form.akunBeban" :aria-invalid="attempted && !form.akunBeban" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
      </div></fieldset>
      <div class="employee-preview"><div><span>Harga perolehan</span><strong>{{ money(form.harga) }}</strong></div><div><span>Masa manfaat</span><strong>{{ form.umur && Number.isInteger(form.umur) ? `${form.umur} bulan` : 'Belum diisi' }}</strong></div></div>
      <p class="employee-small-note">Nominal penyusutan bulanan dihitung server setelah aset disimpan. Jurnal baru dibuat saat tindakan Catat penyusutan dipilih.</p>
      <Message v-if="attempted && invalid" severity="error" :closable="false">Lengkapi nama, tanggal, harga, masa manfaat, dan ketiga akun jurnal.</Message>
      <div v-if="error" ref="errorElement" tabindex="-1"><Message severity="error" :closable="false">{{ error }} Input tetap ada.</Message></div>
      <Message v-if="uncertain" severity="warn" :closable="false">Hasil penyimpanan belum terkonfirmasi. Periksa daftar aset sebelum mencoba kembali.</Message>
    </form>
    <template #footer><Button label="Kembali" severity="secondary" :disabled="saving" @click="close" /><Button v-if="uncertain" label="Periksa daftar aset" severity="secondary" @click="emit('review')" /><Button v-else :label="row ? 'Simpan perubahan' : 'Simpan aset'" type="submit" form="asset-form" :loading="saving" :disabled="saving || accountsLoading || !!accountsError"><template #icon><Icon name="check" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
