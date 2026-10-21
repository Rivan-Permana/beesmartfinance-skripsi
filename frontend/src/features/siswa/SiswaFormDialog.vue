<script setup lang="ts">
import SelectClearButton from "@/shared/components/SelectClearButton.vue"
import { computed, nextTick, reactive, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Select from "primevue/select"
import Textarea from "primevue/textarea"
import Icon from "@/shared/components/PhosphorIcon.vue"
import type { Kelompok, Siswa, SiswaInput } from "@/types/api"
import { kelompokLabel, statusOptions } from "./presentation"

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
  Object.assign(form, {
    nis: props.student?.nis ?? "", nama: props.student?.nama ?? "", status: props.student?.status ?? "aktif",
    spp_nominal: props.student?.spp_nominal ?? "0.00", kelompok: props.student?.kelompok ?? null,
    nama_ayah: props.student?.nama_ayah ?? "", kontak_ayah: props.student?.kontak_ayah ?? "",
    nama_ibu: props.student?.nama_ibu ?? "", kontak_ibu: props.student?.kontak_ibu ?? "", alamat: props.student?.alamat ?? "",
  })
}, { immediate: true })
watch(() => props.error, async (message) => { if (message) { await nextTick(); errorElement.value?.focus() } })
async function submit() {
  if (props.saving) return
  attempted.value = true
  if (nameInvalid.value || sppInvalid.value) {
    await nextTick()
    formElement.value?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
    return
  }
  emit("save", { ...form, nama: form.nama!.trim(), nis: form.nis?.trim() || null })
}
</script>

<template>
  <Dialog v-model:visible="visible" :header="student ? 'Ubah data siswa' : 'Tambah siswa'" modal :draggable="false" :closable="!saving" :close-on-escape="!saving" class="siswa-form-dialog" :style="{ width: '640px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup form siswa' }">
    <template #closeicon><Icon name="x" /></template>
    <p class="siswa-form-intro">{{ student ? 'Perbarui profil dan tarif SPP siswa. Perubahan tidak mengubah tagihan yang sudah dibuat.' : 'Isi data utama siswa. Kontak orang tua dapat dilengkapi kemudian.' }}</p>
    <div v-if="error" ref="errorElement" tabindex="-1" class="siswa-save-error"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }} Input tetap tersimpan di form ini.</Message></div>
    <form id="siswa-form" ref="formElement" novalidate :aria-busy="saving" @submit.prevent="submit">
      <fieldset :disabled="saving" class="siswa-form-section">
        <legend>Data siswa</legend>
        <div class="siswa-fields">
          <div class="siswa-field siswa-field-full"><label for="siswa-name">Nama lengkap <span>(wajib)</span></label><InputText id="siswa-name" v-model="form.nama" autofocus required maxlength="100" :invalid="attempted && nameInvalid" :aria-invalid="attempted && nameInvalid" :aria-describedby="attempted && nameInvalid ? 'siswa-name-error' : undefined" fluid /><small v-if="attempted && nameInvalid" id="siswa-name-error" class="siswa-field-error">Isi nama lengkap siswa.</small></div>
          <div class="siswa-field"><label for="siswa-nis">Nomor induk siswa <span>(NIS)</span></label><InputText id="siswa-nis" v-model="form.nis as string" maxlength="20" aria-describedby="siswa-nis-help" fluid /><small id="siswa-nis-help">Boleh dikosongkan jika belum tersedia.</small></div>
          <div class="siswa-field"><label for="siswa-status">Status siswa</label><Select :key="(saving) ? 'locked' : 'editable'" input-id="siswa-status" v-model="form.status" :disabled="saving" :options="statusOptions" option-label="label" option-value="value" fluid><template #dropdownicon><Icon name="caret-down" /></template></Select></div>
          <div class="siswa-field"><label for="siswa-kelompok">Kelompok belajar</label><Select :key="(groupError || saving) ? 'locked' : 'editable'" input-id="siswa-kelompok" v-model="form.kelompok" :options="groupOptions" option-label="label" option-value="value" placeholder="Belum dikelompokkan" show-clear filter :disabled="groupError || saving" empty-filter-message="Kelompok tidak ditemukan" aria-describedby="siswa-group-help" fluid><template #filtericon><Icon name="magnifying-glass" /></template><template #dropdownicon><Icon name="caret-down" /></template><template #clearicon="slotProps"><SelectClearButton v-bind="slotProps" /></template></Select><small id="siswa-group-help">{{ groupError ? 'Pilihan kelompok belum tersedia. Kelompok siswa saat ini tetap dipertahankan.' : 'Pilih sesuai kelompok belajar siswa.' }}</small></div>
          <div class="siswa-field"><label for="siswa-spp">SPP per bulan <span>(Rp)</span></label><InputNumber input-id="siswa-spp" v-model="spp" locale="id-ID" :min="0" :max-fraction-digits="2" :invalid="attempted && sppInvalid" :input-props="{ 'aria-invalid': attempted && sppInvalid, 'aria-describedby': attempted && sppInvalid ? 'siswa-spp-error' : 'siswa-spp-help' }" fluid /><small v-if="attempted && sppInvalid" id="siswa-spp-error" class="siswa-field-error">Isi nominal nol atau lebih besar.</small><small v-else id="siswa-spp-help">Tarif siswa, bukan pembayaran yang diterima.</small></div>
        </div>
      </fieldset>
      <fieldset :disabled="saving" class="siswa-form-section">
        <legend>Kontak orang tua <span>Opsional</span></legend>
        <div class="siswa-fields">
          <div class="siswa-field"><label for="siswa-father">Nama ayah</label><InputText id="siswa-father" v-model="form.nama_ayah as string" maxlength="100" fluid /></div>
          <div class="siswa-field"><label for="siswa-father-phone">Nomor telepon ayah</label><InputText id="siswa-father-phone" v-model="form.kontak_ayah as string" type="tel" maxlength="20" fluid /></div>
          <div class="siswa-field"><label for="siswa-mother">Nama ibu</label><InputText id="siswa-mother" v-model="form.nama_ibu as string" maxlength="100" fluid /></div>
          <div class="siswa-field"><label for="siswa-mother-phone">Nomor telepon ibu</label><InputText id="siswa-mother-phone" v-model="form.kontak_ibu as string" type="tel" maxlength="20" fluid /></div>
          <div class="siswa-field siswa-field-full"><label for="siswa-address">Alamat</label><Textarea id="siswa-address" v-model="form.alamat as string" rows="2" fluid /></div>
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
.siswa-save-error { margin-bottom: var(--bee-space-5); }.siswa-saving { color: var(--app-text-muted); font-size: var(--bee-type-caption); margin-right: auto; }
@media(max-width: 520px) { .siswa-fields { grid-template-columns: minmax(0, 1fr); gap: var(--bee-space-4); }.siswa-saving { width: 100%; } }
</style>
