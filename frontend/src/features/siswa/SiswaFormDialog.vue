<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, nextTick, reactive, ref, watch } from "vue"
import Button from "primevue/button"
import Checkbox from "primevue/checkbox"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Textarea from "primevue/textarea"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { calendarTextMatches, formatLocalDate, formatRp } from "@/core/format"
import type { BiayaMasukField, Kelompok, Siswa, SiswaInput } from "@/types/api"
import { siswaApi } from "./api"
import { BIAYA_MASUK_FIELDS, biayaMasukBruto, DISKON_KATEGORI, jenisKelaminOptions, kelompokLabel, statusOptions } from "./presentation"

const props = defineProps<{ student: Siswa | null; kelompok: Kelompok[]; saving?: boolean; error?: string; groupError?: boolean }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ save: [payload: Partial<SiswaInput>] }>()
const form = reactive<Partial<SiswaInput>>({})
const attempted = ref(false)
const formElement = ref<HTMLFormElement | null>(null)
const errorElement = ref<HTMLElement | null>(null)
const spp = computed({
  get: () => form.spp_nominal === "" ? null : Number(form.spp_nominal),
  set: (value: number | null) => { form.spp_nominal = value == null ? "" : value.toFixed(2) },
})
function amount(field: BiayaMasukField | "diskon_nominal") {
  const value = form[field]
  return value === "" || value == null ? null : Number(value)
}
function setAmount(field: BiayaMasukField | "diskon_nominal", value: number | null) {
  if (field === "diskon_nominal") form.diskon_nominal = (value ?? 0).toFixed(2)
  else form[field] = value == null ? null : value.toFixed(2)
}
const bruto = computed(() => biayaMasukBruto(form))
const diskon = computed(() => Number(form.diskon_nominal || 0))
const diskonInvalid = computed(() => diskon.value > bruto.value)
const loadingDefaults = ref(false)
const defaultsError = ref("")
async function fillFromPriceList() {
  if (form.kelompok == null || loadingDefaults.value) return
  loadingDefaults.value = true
  defaultsError.value = ""
  try {
    const defaults = await siswaApi.biayaMasukDefault(form.kelompok)
    BIAYA_MASUK_FIELDS.forEach(({ field }) => { form[field] = defaults[field] })
    if (BIAYA_MASUK_FIELDS.every(({ field }) => defaults[field] == null)) defaultsError.value = "Daftar harga untuk jenjang ini belum tersedia. Isi nominal secara manual."
  } catch {
    defaultsError.value = "Daftar harga belum berhasil dimuat. Isi nominal secara manual."
  } finally {
    loadingDefaults.value = false
  }
}
const birthDate = ref<Date | null>(null)
const badBirthDate = ref(false)
function checkBirthDate(event: Event) { badBirthDate.value = !calendarTextMatches((event.target as HTMLInputElement).value, birthDate.value) }
const birthDateInvalid = computed(() => badBirthDate.value || (birthDate.value != null && birthDate.value > new Date()))
const nameInvalid = computed(() => !form.nama?.trim())
const sppInvalid = computed(() => !form.spp_nominal || !Number.isFinite(Number(form.spp_nominal)) || Number(form.spp_nominal) < 0)
const groupOptions = computed(() => {
  const options = props.kelompok.map((item) => ({ value: item.id, label: kelompokLabel(item) }))
  const current = props.student?.kelompok
  if (current != null && !options.some(option => option.value === current)) options.push({ value: current, label: "Kelompok saat ini (nama belum dimuat)" })
  return options
})
watch(visible, (open) => {
  if (!open) return
  attempted.value = false
  badBirthDate.value = false
  birthDate.value = props.student?.tanggal_lahir ? new Date(props.student.tanggal_lahir + "T12:00:00") : null
  Object.assign(form, {
    nis: props.student?.nis ?? "", nama: props.student?.nama ?? "", status: props.student?.status ?? "aktif",
    nama_panggilan: props.student?.nama_panggilan ?? "", jenis_kelamin: props.student?.jenis_kelamin ?? null,
    tempat_lahir: props.student?.tempat_lahir ?? "",
    spp_nominal: props.student?.spp_nominal ?? "0.00", kelompok: props.student?.kelompok ?? null,
    nama_ayah: props.student?.nama_ayah ?? "", kontak_ayah: props.student?.kontak_ayah ?? "",
    nama_ibu: props.student?.nama_ibu ?? "", kontak_ibu: props.student?.kontak_ibu ?? "", alamat: props.student?.alamat ?? "",
    diskon_kategori: [...(props.student?.diskon_kategori ?? [])], diskon_nominal: props.student?.diskon_nominal ?? "0.00",
    uang_masuk: props.student?.uang_masuk ?? null, uang_pengembangan: props.student?.uang_pengembangan ?? null,
    uang_kegiatan: props.student?.uang_kegiatan ?? null, uang_seragam: props.student?.uang_seragam ?? null,
  })
  defaultsError.value = ""
}, { immediate: true })
watch(() => props.error, async (message) => { if (message) { await nextTick(); errorElement.value?.focus() } })
async function submit() {
  if (props.saving) return
  attempted.value = true
  if (nameInvalid.value || sppInvalid.value || diskonInvalid.value || birthDateInvalid.value) {
    await nextTick()
    formElement.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
    return
  }
  emit("save", {
    ...form, nama: form.nama!.trim(), nis: form.nis?.trim() || null,
    nama_panggilan: form.nama_panggilan?.trim() || null, tempat_lahir: form.tempat_lahir?.trim() || null,
    tanggal_lahir: birthDate.value ? formatLocalDate(birthDate.value) : null,
  })
}
</script>

<template>
  <Dialog v-model:visible="visible" :header="student ? 'Ubah data siswa' : 'Tambah siswa'" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" class="siswa-form-dialog" :style="{ width: '640px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup form siswa' }">
    <template #closeicon><Icon name="x" /></template>
    <p class="siswa-form-intro">{{ student ? 'Perbarui profil dan tarif SPP siswa. Perubahan tidak mengubah tagihan yang sudah dibuat.' : 'Isi data utama siswa. Data diri lain dan kontak orang tua dapat dilengkapi kemudian.' }}</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="siswa-save-error"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Input tetap tersimpan di form ini.</Message></div>
    <form id="siswa-form" ref="formElement" novalidate :aria-busy="saving" @submit.prevent="submit">
      <fieldset :disabled="saving" class="siswa-form-section">
        <legend>Data siswa</legend>
        <div class="siswa-fields">
          <div class="siswa-field"><label for="siswa-nis">Nomor induk siswa <span>(NIS)</span></label><InputText id="siswa-nis" v-model="form.nis as string" maxlength="20" aria-describedby="siswa-nis-help" fluid /><small id="siswa-nis-help">Boleh dikosongkan jika belum tersedia.</small></div>
          <div class="siswa-field"><label for="siswa-status">Status siswa</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="siswa-status" v-model="form.status" :disabled="saving" :options="statusOptions" option-label="label" option-value="value" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
          <div class="siswa-field siswa-field-full"><label for="siswa-name">Nama lengkap <span>(wajib)</span></label><InputText id="siswa-name" v-model="form.nama" autofocus required maxlength="100" :invalid="attempted && nameInvalid" :aria-invalid="attempted && nameInvalid" :aria-describedby="attempted && nameInvalid ? 'siswa-name-error' : undefined" fluid /><small v-if="attempted && nameInvalid" id="siswa-name-error" class="siswa-field-error">Isi nama lengkap siswa.</small></div>
          <div class="siswa-field"><label for="siswa-nickname">Nama panggilan</label><InputText id="siswa-nickname" v-model="form.nama_panggilan as string" maxlength="50" fluid /></div>
          <div class="siswa-field"><label for="siswa-gender">Jenis kelamin</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="siswa-gender" v-model="form.jenis_kelamin" :disabled="saving" :options="jenisKelaminOptions" option-label="label" option-value="value" placeholder="Pilih" show-clear fluid><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select></div>
          <div class="siswa-field"><label for="siswa-birthplace">Tempat lahir</label><InputText id="siswa-birthplace" v-model="form.tempat_lahir as string" maxlength="100" fluid /></div>
          <div class="siswa-field"><label for="siswa-birthdate">Tanggal lahir</label><DatePicker :key="(saving) ? 'locked' : 'editable'" input-id="siswa-birthdate" v-model="birthDate" date-format="dd/mm/yy" :max-date="new Date()" :disabled="saving" @input="checkBirthDate" @update:model-value="badBirthDate = false" :invalid="attempted && birthDateInvalid" :input-props="{ 'aria-invalid': attempted && birthDateInvalid, 'aria-describedby': attempted && birthDateInvalid ? 'siswa-birthdate-error' : 'siswa-birthdate-help' }" fluid><template #previcon><Icon name="caret-left" /></template><template #nexticon><Icon name="caret-right" /></template></DatePicker><small v-if="attempted && birthDateInvalid" id="siswa-birthdate-error" class="siswa-field-error">Periksa atau pilih ulang tanggal lahir.</small><small v-else id="siswa-birthdate-help">Format hh/bb/tttt.</small></div>
          <div class="siswa-field"><label for="siswa-kelompok">Kelompok belajar</label><Select :key="(groupError || saving) ? 'locked' : 'editable'" input-id="siswa-kelompok" v-model="form.kelompok" :options="groupOptions" option-label="label" option-value="value" placeholder="Belum dikelompokkan" show-clear filter :disabled="groupError || saving" empty-filter-message="Kelompok tidak ditemukan" aria-describedby="siswa-group-help" fluid><template #filtericon><Icon name="magnifying-glass" /></template><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select><small id="siswa-group-help">{{ groupError ? 'Pilihan kelompok belum tersedia. Kelompok siswa saat ini tetap dipertahankan.' : 'Pilih sesuai kelompok belajar siswa.' }}</small></div>
          <div class="siswa-field"><label for="siswa-spp">SPP per bulan <span>(Rp)</span></label><InputNumber input-id="siswa-spp" v-model="spp" locale="id-ID" :min="0" :max-fraction-digits="2" :invalid="attempted && sppInvalid" :input-props="{ 'aria-invalid': attempted && sppInvalid, 'aria-describedby': attempted && sppInvalid ? 'siswa-spp-error' : 'siswa-spp-help' }" fluid /><small v-if="attempted && sppInvalid" id="siswa-spp-error" class="siswa-field-error">Isi nominal nol atau lebih besar.</small><small v-else id="siswa-spp-help">Tarif siswa, bukan pembayaran yang diterima.</small></div>
        </div>
      </fieldset>
      <fieldset :disabled="saving" class="siswa-form-section">
        <legend>Biaya masuk <span>Opsional</span></legend>
        <p class="siswa-section-help">Nominal yang diisi menjadi tagihan biaya masuk siswa ini. Setelah disimpan, penerimaan dicatat dari daftar siswa dan boleh dibayar sebagian.</p>
        <div class="siswa-fee-toolbar"><Button label="Isi dari daftar harga" severity="secondary" text :disabled="form.kelompok == null || saving" :loading="loadingDefaults" @click="fillFromPriceList"><template #icon><Icon name="clipboard-text" /></template></Button><small v-if="form.kelompok == null">Pilih kelompok dulu untuk memakai daftar harga.</small></div>
        <p v-if="defaultsError" class="siswa-field-error siswa-section-help" role="alert">{{ defaultsError }}</p>
        <div class="siswa-fields">
          <div v-for="item in BIAYA_MASUK_FIELDS" :key="item.field" class="siswa-field"><label :for="`siswa-${item.field}`">{{ item.label }} <span>(Rp)</span></label><InputNumber :input-id="`siswa-${item.field}`" :model-value="amount(item.field)" @update:model-value="setAmount(item.field, $event)" locale="id-ID" :min="0" :max-fraction-digits="2" placeholder="Tidak ditagih" fluid /></div>
        </div>
        <div class="siswa-discount" role="group" aria-labelledby="siswa-discount-label">
          <span id="siswa-discount-label" class="siswa-discount-label">Status diskon</span>
          <div class="siswa-discount-options"><label v-for="kode in DISKON_KATEGORI" :key="kode" class="siswa-discount-option"><Checkbox v-model="form.diskon_kategori" :value="kode" :input-id="`diskon-${kode}`" />{{ kode }}</label></div>
        </div>
        <div class="siswa-fields">
          <div class="siswa-field"><label for="siswa-diskon">Jumlah diskon <span>(Rp)</span></label><InputNumber input-id="siswa-diskon" :model-value="amount('diskon_nominal')" @update:model-value="setAmount('diskon_nominal', $event)" locale="id-ID" :min="0" :max-fraction-digits="2" :invalid="diskonInvalid" :input-props="{ 'aria-invalid': diskonInvalid, 'aria-describedby': diskonInvalid ? 'siswa-diskon-error' : 'siswa-diskon-help' }" fluid /><small v-if="diskonInvalid" id="siswa-diskon-error" class="siswa-field-error">Diskon tidak boleh melebihi total biaya masuk.</small><small v-else id="siswa-diskon-help">Memotong Uang Masuk lebih dulu, lalu Pengembangan, Kegiatan, dan Seragam.</small></div>
          <dl class="siswa-fee-summary" aria-live="polite"><div><dt>Total biaya masuk</dt><dd>{{ formatRp(bruto) }}</dd></div><div><dt>Diskon</dt><dd>− {{ formatRp(Math.min(diskon, bruto)) }}</dd></div><div class="siswa-fee-total"><dt>Ditagihkan</dt><dd>{{ formatRp(Math.max(bruto - diskon, 0)) }}</dd></div></dl>
        </div>
        <small v-if="student?.biaya_masuk" class="siswa-section-help">Komponen yang sudah ada penerimaannya tidak bisa diubah nominalnya.</small>
      </fieldset>
      <fieldset :disabled="saving" class="siswa-form-section">
        <legend>Alamat dan orang tua <span>Opsional</span></legend>
        <div class="siswa-fields">
          <div class="siswa-field siswa-field-full"><label for="siswa-address">Alamat</label><Textarea id="siswa-address" v-model="form.alamat as string" rows="2" fluid /></div>
          <div class="siswa-field"><label for="siswa-father">Nama ayah</label><InputText id="siswa-father" v-model="form.nama_ayah as string" maxlength="100" fluid /></div>
          <div class="siswa-field"><label for="siswa-father-phone">Nomor telepon ayah</label><InputText id="siswa-father-phone" v-model="form.kontak_ayah as string" type="tel" maxlength="20" fluid /></div>
          <div class="siswa-field"><label for="siswa-mother">Nama ibu</label><InputText id="siswa-mother" v-model="form.nama_ibu as string" maxlength="100" fluid /></div>
          <div class="siswa-field"><label for="siswa-mother-phone">Nomor telepon ibu</label><InputText id="siswa-mother-phone" v-model="form.kontak_ibu as string" type="tel" maxlength="20" fluid /></div>
        </div>
      </fieldset>
    </form>
    <template #footer><span v-if="saving" class="siswa-saving" role="status">Sedang menyimpan data…</span><Button label="Batal" severity="secondary" :disabled="saving" @click="visible = false" /><Button :label="student ? 'Simpan perubahan' : 'Tambah siswa'" type="submit" form="siswa-form" :loading="saving" :aria-busy="saving"><template #icon><Icon :name="student ? 'check' : 'plus'" /></template><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>

<style scoped>
.siswa-form-intro { margin: 0 0 var(--bee-space-5); color: var(--app-text-muted); max-width: 60ch; }
.siswa-form-section { border: 0; border-top: 1px solid var(--app-border); padding: var(--bee-space-5) 0 0; margin: 0 0 var(--bee-space-5); min-width: 0; }
.siswa-form-section:last-child { margin-bottom: 0; }
.siswa-form-section legend { font-size: var(--bee-type-body); font-weight: 500; padding: 0 var(--bee-space-3) 0 0; }.siswa-form-section legend span { font-size: var(--bee-type-caption); font-weight: 400; color: var(--app-text-muted); margin-left: var(--bee-space-2); }
.siswa-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--bee-space-5) var(--bee-space-4); }.siswa-field { display: flex; flex-direction: column; gap: var(--bee-space-2); min-width: 0; }.siswa-field-full { grid-column: 1 / -1; }
.siswa-field label { font-weight: 500; }.siswa-field label span { color: var(--app-text-muted); font-weight: 400; }.siswa-field small { color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.4; }.siswa-field small.siswa-field-error { color: var(--bee-color-critical); }
.siswa-section-help { margin: 0 0 var(--bee-space-4); color: var(--app-text-muted); font-size: var(--bee-type-caption); max-width: 60ch; display: block; }
.siswa-fee-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-2) var(--bee-space-3); margin: 0 0 var(--bee-space-4); }.siswa-fee-toolbar .p-button { padding-inline: 0; }.siswa-fee-toolbar small { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.siswa-discount { margin: var(--bee-space-5) 0 var(--bee-space-4); }.siswa-discount-label { display: block; font-weight: 500; margin-bottom: var(--bee-space-2); }
.siswa-discount-options { display: flex; flex-wrap: wrap; gap: var(--bee-space-2); }.siswa-discount-option { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 44px; padding: 0 var(--bee-space-4); border: 1px solid var(--app-border); border-radius: var(--bee-radius-control); cursor: pointer; }.siswa-discount-option:has(:checked) { border-color: var(--bee-color-brand); background: var(--bee-color-brand-tint); }
.siswa-fee-summary { margin: 0; padding: var(--bee-space-3) var(--bee-space-4); background: var(--bee-color-surface-subtle); border-radius: var(--bee-radius-control); display: grid; gap: var(--bee-space-1); align-self: start; }.siswa-fee-summary div { display: flex; justify-content: space-between; gap: var(--bee-space-3); }.siswa-fee-summary dt { color: var(--app-text-muted); font-size: var(--bee-type-caption); }.siswa-fee-summary dd { margin: 0; font-variant-numeric: tabular-nums; }.siswa-fee-total { border-top: 1px solid var(--app-border); padding-top: var(--bee-space-1); }.siswa-fee-total dt, .siswa-fee-total dd { font-weight: 600; color: var(--app-text); font-size: var(--bee-type-ui); }
.siswa-save-error { margin-bottom: var(--bee-space-5); }.siswa-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media(max-width: 520px) { .siswa-fields { grid-template-columns: minmax(0, 1fr); gap: var(--bee-space-4); }.siswa-saving { width: 100%; } }
</style>
