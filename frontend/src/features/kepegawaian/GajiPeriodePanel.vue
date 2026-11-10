<script setup lang="ts">
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { computed, ref, watch } from 'vue'
import Icon from '@/shared/components/PhosphorIcon.vue'
import { notifySuccess } from '@/core/errors'
import type { Gaji, GajiPeriodeHasil } from '@/types/api'
import { gajiApi } from './api'
import { errorText, money, payrollPeriods } from './payroll'

const props = defineProps<{ rows: Gaji[]; mode: 'finance' | 'principal'; busy?: boolean }>()
const emit = defineEmits<{ done: [] }>()
const toast = useToast()

const periods = computed(() => payrollPeriods(props.rows))
const selected = ref<string | null>(null)
const period = computed(() => periods.value.find(p => p.key === selected.value) ?? null)
const count = computed(() => period.value ? (props.mode === 'finance' ? period.value.belum : period.value.menunggu) : 0)
// Pilih otomatis periode terbaru yang masih punya pekerjaan untuk peran ini.
watch(periods, list => {
  if (selected.value && list.some(p => p.key === selected.value)) return
  selected.value = (list.find(p => (props.mode === 'finance' ? p.belum : p.menunggu) > 0) ?? list[0])?.key ?? null
}, { immediate: true })

const open = ref(false), loading = ref(false), saving = ref(false), error = ref('')
const preview = ref<GajiPeriodeHasil | null>(null), result = ref<GajiPeriodeHasil | null>(null)
const failures = computed(() => result.value?.hasil.filter(h => h.status === 'gagal') ?? [])
const title = computed(() => `${props.mode === 'finance' ? 'Posting dan ajukan gaji' : 'Setujui jurnal gaji'} ${period.value?.label ?? ''}`)
const run = (simpan: boolean) => props.mode === 'finance'
  ? gajiApi.postingPeriode(period.value!.bulan, period.value!.tahun, simpan)
  : gajiApi.setujuiPeriode(period.value!.bulan, period.value!.tahun, simpan)

async function start() {
  if (!period.value || !count.value || props.busy) return
  open.value = true; loading.value = true; error.value = ''; preview.value = null; result.value = null
  try { preview.value = await run(false) } catch (e) { error.value = errorText(e, 'Daftar slip belum berhasil diperiksa') } finally { loading.value = false }
}
async function confirm() {
  if (!preview.value?.jumlah || saving.value) return
  saving.value = true; error.value = ''
  try {
    result.value = await run(true)
    if (result.value.berhasil) notifySuccess(toast, props.mode === 'finance' ? 'Jurnal gaji dibuat dan diajukan' : 'Jurnal gaji disetujui', { detail: `${result.value.berhasil} slip, total ${money(result.value.total_netto)}.` })
    emit('done')
    if (!result.value.gagal) open.value = false
  } catch (e) { error.value = errorText(e, 'Proses belum terkonfirmasi. Muat ulang daftar sebelum mencoba lagi') } finally { saving.value = false }
}
function close() { if (!saving.value) open.value = false }
</script>

<template>
  <section class="employee-panel payroll-period" aria-labelledby="payroll-period-title">
    <header class="employee-heading">
      <div>
        <h2 id="payroll-period-title">Jurnal gaji per periode</h2>
        <p v-if="mode === 'finance'">Buat jurnal untuk semua slip satu periode sekaligus, lalu ajukan ke Kepala Sekolah.</p>
        <p v-else>Periksa daftar jurnal gaji satu periode, lalu setujui sekaligus.</p>
      </div>
    </header>
    <div class="payroll-period-body">
      <div class="employee-field">
        <label for="payroll-period">Periode</label>
        <Select input-id="payroll-period" v-model="selected" :options="periods" option-label="label" option-value="key" placeholder="Belum ada slip" :disabled="!periods.length || busy"><template #dropdownicon><Icon name="caret-down" /></template></Select>
      </div>
      <p v-if="period" class="payroll-period-count" role="status">{{ period.belum }} slip belum dijurnal · {{ period.menunggu }} menunggu persetujuan</p>
      <Button :label="mode === 'finance' ? `Posting dan ajukan ${count} slip` : `Periksa dan setujui ${count} jurnal`" :disabled="!count || busy" @click="start"><template #icon><Icon :name="mode === 'finance' ? 'file-arrow-up' : 'check-circle'" /></template></Button>
    </div>
  </section>

  <Dialog :visible="open" @update:visible="v => { if (!v) close() }" :header="title" modal :draggable="false" :style="{ width: '560px' }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup' }">
    <template #closeicon><Icon name="x" /></template>
    <p v-if="loading" role="status">Memeriksa slip di server…</p>
    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
    <template v-if="preview && !result">
      <p class="payroll-period-summary"><strong>{{ preview.jumlah }} slip</strong> · total netto <strong>{{ money(preview.total_netto) }}</strong></p>
      <ul class="payroll-period-list" aria-label="Slip yang akan diproses"><li v-for="row in preview.hasil" :key="row.gaji"><span>{{ row.nama }}</span><span class="tabular-nums">{{ money(row.netto) }}</span></li></ul>
      <p class="payroll-period-note">{{ mode === 'finance' ? 'Setiap slip mendapat jurnal sendiri dan langsung diajukan ke Kepala Sekolah. Saldo kasbon baru berkurang setelah jurnal disetujui.' : 'Jurnal dicatat ke buku besar dan potongan kasbon dibukukan. Jurnal yang Anda buat sendiri tidak bisa Anda setujui dan akan dilewati.' }}</p>
    </template>
    <template v-if="result">
      <p class="payroll-period-summary"><strong>{{ result.berhasil }} berhasil</strong>, {{ result.gagal }} gagal.</p>
      <Message v-if="failures.length" severity="warn" :closable="false">
        <ul class="payroll-period-failures"><li v-for="row in failures" :key="row.gaji"><strong>{{ row.nama }}</strong>: {{ row.pesan }}</li></ul>
      </Message>
    </template>
    <template #footer>
      <Button :label="result ? 'Tutup' : 'Batal'" severity="secondary" :disabled="saving" @click="close" />
      <Button v-if="!result" :label="mode === 'finance' ? 'Buat dan ajukan jurnal' : 'Setujui semua'" :loading="saving" :disabled="!preview?.jumlah || loading" @click="confirm" />
    </template>
  </Dialog>
</template>

<style scoped>
.payroll-period { margin-bottom: var(--bee-space-5); }
.payroll-period-body { display: flex; flex-wrap: wrap; align-items: end; gap: var(--bee-space-4); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.payroll-period-body .employee-field { min-width: 200px; }
.payroll-period-count { margin: 0; color: var(--app-text-muted); font-size: var(--bee-type-caption); flex: 1 1 200px; }
.payroll-period-summary { margin: 0 0 var(--bee-space-3); }
.payroll-period-list { list-style: none; margin: 0; padding: 0; max-height: 280px; overflow-y: auto; border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.payroll-period-list li { display: flex; justify-content: space-between; gap: var(--bee-space-3); padding: var(--bee-space-2) var(--bee-space-3); border-bottom: 1px solid var(--app-border); }
.payroll-period-list li:last-child { border-bottom: 0; }
.payroll-period-note { color: var(--app-text-muted); font-size: var(--bee-type-caption); line-height: 1.5; margin: var(--bee-space-3) 0 0; }
.payroll-period-failures { margin: 0; padding-left: var(--bee-space-4); }
@media (max-width: 520px) { .payroll-period-body .employee-field, .payroll-period-body .p-button { flex: 1 1 100%; } }
</style>
