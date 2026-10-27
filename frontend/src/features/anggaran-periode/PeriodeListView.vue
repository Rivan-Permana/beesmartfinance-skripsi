<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import DatePicker from "primevue/datepicker"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Tag from "primevue/tag"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, reactive, ref } from "vue"

import { periodeApi } from "./api"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { calendarTextMatches, formatLocalDate } from "@/core/format"
import PageLayout from "@/shared/components/PageLayout.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { useAuthStore } from "@/stores/auth"
import type { PeriodeAkuntansi } from "@/types/api"

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const rows = ref<PeriodeAkuntansi[]>([])
const loading = ref(false)
const error = ref("")
const closing = ref(false)
const canCreate = computed(() => auth.hasRole(["Finance"]))
const canClose = computed(() => auth.hasRole(["SchoolPrincipal"]))

async function load() {
  if (loading.value) return
  loading.value = true
  error.value = ""
  try { rows.value = await periodeApi.listAll() }
  catch (cause) {
    rows.value = []
    const message = friendlyError(cause, "Periode akuntansi belum berhasil dimuat")
    error.value = [message.summary, message.detail].filter(Boolean).join(". ")
  }
  finally { loading.value = false }
}

const dialog = ref(false)
const saving = ref(false)
const formError = ref("")
const badStart = ref(false)
const badEnd = ref(false)
const form = reactive<{ kode: string; tgl_mulai: Date | null; tgl_selesai: Date | null }>({
  kode: "",
  tgl_mulai: new Date(new Date().getFullYear(), 6, 1),    // 1 Juli
  tgl_selesai: new Date(new Date().getFullYear() + 1, 5, 30), // 30 Juni
})

function openCreate() {
  formError.value = ""; badStart.value = false; badEnd.value = false
  const y = new Date().getFullYear()
  form.kode = `${y}/${y + 1}`
  form.tgl_mulai = new Date(y, 6, 1)
  form.tgl_selesai = new Date(y + 1, 5, 30)
  dialog.value = true
}

async function save() {
  if (saving.value || !canCreate.value) return
  formError.value = ""
  if (!form.kode.trim()) formError.value = "Isi kode periode."
  else if (!form.tgl_mulai || !form.tgl_selesai || badStart.value || badEnd.value || !Number.isFinite(form.tgl_mulai.getTime()) || !Number.isFinite(form.tgl_selesai.getTime())) formError.value = "Pilih tanggal mulai dan selesai yang valid."
  else if (form.tgl_mulai > form.tgl_selesai) formError.value = "Tanggal selesai harus sesudah atau sama dengan tanggal mulai."
  if (formError.value) return
  saving.value = true
  try {
    await periodeApi.create({
      kode: form.kode.trim(),
      tgl_mulai: formatLocalDate(form.tgl_mulai!),
      tgl_selesai: formatLocalDate(form.tgl_selesai!),
    })
    notifySuccess(toast, "Periode akuntansi dibuat")
    dialog.value = false
    await load()
  } catch (e) {
    notifyError(toast, e, "Belum dapat memastikan periode dibuat. Periksa daftar sebelum mencoba lagi.")
  } finally {
    saving.value = false
  }
}

function tutup(p: PeriodeAkuntansi) {
  confirm.require({
    message: `Tutup buku ${p.kode} (${dateLabel(p.tgl_mulai)}–${dateLabel(p.tgl_selesai)})? Sistem membuat dan memposting jurnal penutup pendapatan serta beban ke ekuitas. Tindakan ini tidak dapat dibatalkan.`,
    header: "Tutup buku periode?",
    rejectLabel: "Batal",
    acceptLabel: "Tutup buku",
    acceptClass: "p-button-danger",
    accept: async () => {
      if (closing.value) return
      closing.value = true
      try {
        const latest = (await periodeApi.listAll()).find((row) => row.id === p.id)
        if (!latest || latest.status !== "OPEN") { toast.add({ severity: "warn", summary: "Status berubah", detail: "Periode tidak lagi terbuka. Muat ulang daftar sebelum melanjutkan.", life: 6000 }); await load(); return }
        const res = await periodeApi.tutup(p.id)
        notifySuccess(toast, "Periode ditutup", res)
        await load()
      } catch (e) {
        notifyError(toast, e, "Belum dapat memastikan penutupan berhasil. Periksa status periode dan jurnal sebelum mencoba lagi.")
      } finally { closing.value = false }
    },
  })
}

function dateLabel(value: string) { return value.split("-").reverse().join("/") }
const openCount = computed(() => rows.value.filter((row) => row.status === "OPEN").length)

onMounted(load)
</script>

<template>
  <PageLayout title="Periode akuntansi" subtitle="Rentang pembukuan dan status tutup buku sekolah." :surface="false">
    <template #actions>
      <Button v-if="canCreate" label="Tambah periode" :disabled="loading || !!error" @click="openCreate"><template #icon><Icon name="plus" /></template></Button>
    </template>

    <div class="period-scope"><Icon name="info" /><p>Periode memakai rentang tanggal pembukuan; contoh tahun pelajaran berjalan dari Juli sampai Juni. Menutup buku membuat <strong>jurnal penutup terposting</strong> dan mengubah status menjadi Tertutup.</p></div>
    <section class="period-panel" aria-label="Daftar periode akuntansi" :aria-busy="loading">
      <header class="period-heading"><div><h2>Daftar periode</h2><p v-if="!loading && !error">{{ openCount }} terbuka · {{ rows.length - openCount }} tertutup</p><p v-else>Periksa rentang dan status sebelum tindakan.</p></div><Button label="Muat ulang" severity="secondary" :disabled="loading || closing" :loading="loading" @click="load"><template #icon><Icon name="arrows-clockwise" /></template></Button></header>
      <div v-if="error" class="period-notice"><Message severity="error" :closable="false">{{ error }}</Message><Button label="Coba muat ulang periode" severity="secondary" @click="load" /></div>
      <div v-if="!loading && !error && !rows.length" class="period-empty"><Icon name="calendar-blank" /><h3>Belum ada periode tercatat</h3><p>{{ canCreate ? "Tambah periode untuk menyiapkan rentang pembukuan." : "Minta Staf Keuangan menyiapkan periode." }}</p></div>
      <p v-if="!error && rows.length" class="period-scroll-hint"><Icon name="caret-right" /> Geser tabel untuk melihat status{{ canClose ? ' dan aksi' : '' }}.</p>
      <div v-if="!error && (loading || rows.length)" class="period-table-scroll" role="region" tabindex="0" aria-label="Tabel periode dapat digulir horizontal">

    <DataTable :value="rows" :loading="loading" data-key="id" striped-rows>
      <Column field="kode" header="Periode" />
      <Column header="Mulai"><template #body="{ data }">{{ dateLabel(data.tgl_mulai) }}</template></Column>
      <Column header="Selesai"><template #body="{ data }">{{ dateLabel(data.tgl_selesai) }}</template></Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.status === 'OPEN' ? 'Terbuka' : 'Tertutup'"
            :severity="data.status === 'OPEN' ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column v-if="canClose" header="Tindakan" headerClass="bee-col-actions--md" bodyClass="bee-col-actions--md">
        <template #body="{ data }">
          <div class="bee-actions">
            <Button
              v-if="canClose && data.status === 'OPEN'"
              label="Tutup buku"
              size="small"
              severity="danger"
              :disabled="loading || closing"
              text
              @click="tutup(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>
      </div>
    </section>

    <Dialog v-model:visible="dialog" header="Tambah periode" modal class="period-dialog" :closable="!saving" :dismissable-mask="!saving" :close-on-escape="!saving">
      <div class="form-grid">
        <p class="period-form-intro span2">Tanggal menentukan rentang jurnal yang akan ditutup. Periksa keduanya sebelum menyimpan.</p>
        <div class="field span2">
          <label for="period-code">Kode periode (wajib)</label>
          <InputText id="period-code" v-model="form.kode" placeholder="Contoh: 2025/2026" :disabled="saving" fluid />
        </div>
        <div class="field">
          <label for="period-start">Tanggal mulai (wajib)</label>
          <DatePicker input-id="period-start" v-model="form.tgl_mulai" date-format="dd/mm/yy" :disabled="saving" :invalid="badStart" @input="badStart = !calendarTextMatches(($event.target as HTMLInputElement).value, form.tgl_mulai)" @update:model-value="badStart = false" fluid />
        </div>
        <div class="field">
          <label for="period-end">Tanggal selesai (wajib)</label>
          <DatePicker input-id="period-end" v-model="form.tgl_selesai" date-format="dd/mm/yy" :disabled="saving" :invalid="badEnd" @input="badEnd = !calendarTextMatches(($event.target as HTMLInputElement).value, form.tgl_selesai)" @update:model-value="badEnd = false" fluid />
        </div>
        <Message v-if="formError" severity="error" :closable="false" class="span2" role="alert">{{ formError }}</Message>
      </div>
      <template #footer>
        <Button label="Batal" severity="secondary" text :disabled="saving" @click="dialog = false" />
        <Button label="Simpan periode" :disabled="saving" :loading="saving" @click="save" />
      </template>
    </Dialog>
  </PageLayout>
</template>

<style scoped>
.period-scope { display: flex; align-items: start; gap: var(--bee-space-3); margin-bottom: var(--bee-space-5); padding: var(--bee-space-4) var(--bee-space-5); background: var(--app-surface); border-inline-start: 3px solid var(--bee-color-info); border-radius: var(--bee-radius-control); }
.period-scope .bee-icon { width: 20px; height: 20px; flex: none; color: var(--bee-color-info); }
.period-scope p { margin: 0; max-width: 85ch; line-height: 1.55; }
.period-panel { overflow: hidden; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.period-heading { display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: var(--bee-space-4); padding: var(--bee-space-5); }
.period-heading h2 { margin: 0; font-size: var(--bee-type-section); }
.period-heading p { margin: var(--bee-space-2) 0 0; color: var(--app-text-muted); }
.period-notice { display: flex; align-items: center; flex-wrap: wrap; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-5); }
.period-notice .p-message { flex: 1 1 300px; }
.period-empty { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-7) var(--bee-space-5); text-align: center; }
.period-empty .bee-icon { width: 32px; height: 32px; color: var(--app-text-muted); }
.period-empty h3 { margin: 0; font-size: var(--bee-type-section); }
.period-empty p { margin: 0; color: var(--app-text-muted); }
.period-table-scroll { overflow-x: auto; }
.period-scroll-hint { display: none; align-items: center; gap: var(--bee-space-2); margin: 0; padding: var(--bee-space-3) var(--bee-space-5); color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.period-scroll-hint .bee-icon { width: 16px; height: 16px; }
.period-table-scroll :deep(.p-datatable) { min-width: 660px; }
.period-dialog { width: min(520px, calc(100vw - 32px)); }
.period-form-intro { margin: 0; color: var(--app-text-muted); line-height: 1.5; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field.span2 { grid-column: 1 / -1; }
.field label { font-weight: 600; font-size: 0.85rem; }
@media (max-width: 900px) { .period-scroll-hint { display: flex; } }
@media (max-width: 540px) { .period-heading > .p-button { width: 100%; } .form-grid { grid-template-columns: minmax(0, 1fr); } .field.span2,.span2 { grid-column: 1; } }
</style>
