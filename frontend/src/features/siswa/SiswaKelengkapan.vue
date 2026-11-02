<script setup lang="ts">
import BeePaginator from "@/shared/components/BeePaginator.vue"
import { computed, ref, watch } from "vue"
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { KelengkapanBaris, KelengkapanHasil, KelengkapanKode } from "@/types/api"
import { KELENGKAPAN_LABEL } from "./presentation"

const props = defineProps<{
  result: KelengkapanHasil | null
  loading?: boolean
  error?: string
  /** Keuangan dan Kepsek hanya melihat; Staf TU melengkapi. */
  readonly?: boolean
}>()
const emit = defineEmits<{ edit: [id: number]; retry: [] }>()
const kode = ref<KelengkapanKode | null>(null)
const first = ref(0)
const rows = computed(() => props.result?.baris ?? [])
const filtered = computed(() => kode.value ? rows.value.filter((row) => row.masalah.some((m) => m.kode === kode.value)) : rows.value)
const pageRows = computed(() => filtered.value.slice(first.value, first.value + 10))
const chips = computed(() => (Object.keys(KELENGKAPAN_LABEL) as KelengkapanKode[])
  .map((value) => ({ value, label: KELENGKAPAN_LABEL[value], count: props.result?.ringkasan[value] ?? 0 }))
  .filter((chip) => chip.count > 0))
watch([kode, rows], () => { first.value = 0 })
function spp(row: KelengkapanBaris) {
  if (Number(row.spp_nominal) <= 0) return "Belum diisi"
  return formatRp(row.spp_nominal) + (row.spp_acuan ? ` · median jenjang ${formatRp(row.spp_acuan)}` : "")
}
</script>

<template>
  <section class="kelengkapan" aria-label="Data siswa perlu dilengkapi" :aria-busy="loading">
    <div class="kelengkapan-heading">
      <h2>Perlu dilengkapi <span v-if="result">{{ result.baris.length }}</span></h2>
      <p>Siswa aktif dengan SPP kosong atau di luar kisaran jenjangnya, nomor HP orang tua kosong atau janggal, atau belum punya kelompok. Daftar ini berkurang sendiri setelah data diperbaiki.</p>
    </div>
    <div v-if="chips.length" class="kelengkapan-chips" role="group" aria-label="Saring jenis masalah">
      <Button :label="`Semua (${rows.length})`" size="small" :severity="kode === null ? undefined : 'secondary'" :outlined="kode !== null" :aria-pressed="kode === null" @click="kode = null" />
      <Button v-for="chip in chips" :key="chip.value" :label="`${chip.label} (${chip.count})`" size="small" :severity="kode === chip.value ? undefined : 'secondary'" :outlined="kode !== chip.value" :aria-pressed="kode === chip.value" @click="kode = chip.value" />
    </div>
    <div v-if="error" class="kelengkapan-notice"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang" severity="secondary" @click="emit('retry')" /></div>
    <div v-else-if="loading" class="kelengkapan-loading" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><span>Memeriksa data siswa</span></div>
    <div v-else-if="!rows.length" class="kelengkapan-empty"><Icon name="check-circle" /><h3>Data siswa aktif sudah lengkap</h3><p>Tidak ada SPP kosong, nomor HP janggal, atau siswa tanpa kelompok.</p></div>
    <template v-else>
      <DataTable class="kelengkapan-desktop" :value="pageRows" data-key="id" :table-style="{ minWidth: '760px' }" :pt="{ tableContainer: { tabindex: 0, role: 'region', 'aria-label': 'Tabel siswa perlu dilengkapi' } }">
        <Column header="Siswa"><template #body="{ data }"><strong class="kelengkapan-name">{{ data.nama }}</strong><small class="kelengkapan-secondary">{{ data.kelompok ?? "Belum dikelompokkan" }}{{ data.nis ? ` · NIS ${data.nis}` : "" }}</small></template></Column>
        <Column header="Yang perlu dicek"><template #body="{ data }"><ul class="kelengkapan-masalah"><li v-for="(m, i) in data.masalah" :key="i"><Tag :value="m.pesan" severity="warn" /></li></ul></template></Column>
        <Column header="SPP per bulan"><template #body="{ data }"><span class="tabular-nums">{{ spp(data) }}</span></template></Column>
        <Column v-if="!readonly" header="Tindakan" header-class="kelengkapan-actions" body-class="kelengkapan-actions"><template #body="{ data }"><Button label="Lengkapi" severity="secondary" :aria-label="`Lengkapi data ${data.nama}`" @click="emit('edit', data.id)"><template #icon><Icon name="pencil-simple" /></template></Button></template></Column>
      </DataTable>
      <ul class="kelengkapan-mobile" aria-label="Siswa perlu dilengkapi">
        <li v-for="row in pageRows" :key="row.id">
          <strong class="kelengkapan-name">{{ row.nama }}</strong><small class="kelengkapan-secondary">{{ row.kelompok ?? "Belum dikelompokkan" }}</small>
          <ul class="kelengkapan-masalah"><li v-for="(m, i) in row.masalah" :key="i"><Tag :value="m.pesan" severity="warn" /></li></ul>
          <p class="kelengkapan-secondary tabular-nums">SPP: {{ spp(row) }}</p>
          <Button v-if="!readonly" label="Lengkapi data" severity="secondary" fluid :aria-label="`Lengkapi data ${row.nama}`" @click="emit('edit', row.id)"><template #icon><Icon name="pencil-simple" /></template></Button>
        </li>
      </ul>
      <BeePaginator v-if="filtered.length > 10" v-model:first="first" :rows="10" :total-records="filtered.length" />
    </template>
    <div class="kelengkapan-footnote"><Icon name="info" /><span>SPP dianggap di luar kisaran bila kurang dari separuh atau lebih dari 1,5 kali median SPP jenjangnya. SPP khusus yang memang disepakati boleh dibiarkan.</span></div>
  </section>
</template>

<style scoped>
.kelengkapan { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); overflow: clip; }
.kelengkapan-heading { padding: var(--bee-space-5) var(--bee-space-5) var(--bee-space-4); }
.kelengkapan-heading h2 { font-size: var(--bee-type-section); font-weight: 600; line-height: 1.3; display: flex; align-items: center; gap: var(--bee-space-3); }
.kelengkapan-heading h2 span { font-size: var(--bee-type-ui); font-weight: 500; color: var(--bee-color-muted); background: var(--bee-color-neutral-tint); padding: 2px 8px; border-radius: var(--bee-radius-status); }
.kelengkapan-heading p { margin: var(--bee-space-1) 0 0; color: var(--app-text-muted); max-width: 72ch; }
.kelengkapan-chips { display: flex; flex-wrap: wrap; gap: var(--bee-space-2); padding: 0 var(--bee-space-5) var(--bee-space-4); }
.kelengkapan-notice { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-3); padding: 0 var(--bee-space-5) var(--bee-space-4); }.kelengkapan-notice .p-message { flex: 1 1 300px; }
.kelengkapan-loading { display: flex; gap: var(--bee-space-3); align-items: center; justify-content: center; min-height: 200px; color: var(--app-text-muted); border-top: 1px solid var(--app-border); }
.kelengkapan-empty { display: grid; justify-items: center; text-align: center; padding: var(--bee-space-7) var(--bee-space-5); border-top: 1px solid var(--app-border); }.kelengkapan-empty > .bee-icon { width: 32px; height: 32px; color: var(--bee-color-success, var(--bee-color-muted)); margin-bottom: var(--bee-space-4); }.kelengkapan-empty h3 { font-size: var(--bee-type-section); font-weight: 500; }.kelengkapan-empty p { color: var(--app-text-muted); margin: var(--bee-space-2) 0 0; }
.kelengkapan-name { font-weight: 500; overflow-wrap: anywhere; }
.kelengkapan-secondary { display: block; font-size: var(--bee-type-caption); color: var(--app-text-muted); margin-top: var(--bee-space-1); }
.kelengkapan-masalah { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--bee-space-1); }
:deep(.kelengkapan-actions) { width: 144px; text-align: end; white-space: nowrap; }:deep(th.kelengkapan-actions .p-datatable-column-header-content) { justify-content: flex-end; }
:deep(.p-datatable-tbody > tr > td) { height: var(--bee-size-row-multiline); padding-block: var(--bee-space-3); }
.kelengkapan-footnote { display: flex; align-items: flex-start; gap: var(--bee-space-2); padding: var(--bee-space-4) var(--bee-space-5); border-top: 1px solid var(--app-border); color: var(--app-text-muted); font-size: var(--bee-type-caption); }.kelengkapan-footnote .bee-icon { width: 16px; height: 16px; margin-top: 2px; flex-shrink: 0; }
.kelengkapan-mobile { display: none; }
@media (max-width: 767px) {
  .kelengkapan-heading, .kelengkapan-chips, .kelengkapan-notice { padding-inline: var(--bee-space-4); }
  .kelengkapan-desktop { display: none; }
  .kelengkapan-mobile { display: block; list-style: none; margin: 0; padding: 0; }.kelengkapan-mobile > li { display: grid; gap: var(--bee-space-2); padding: var(--bee-space-4); border-top: 1px solid var(--app-border); }
  .kelengkapan-mobile .kelengkapan-secondary { margin: 0; }.kelengkapan-mobile .p-button { min-height: 44px; }
  .kelengkapan-footnote { padding: var(--bee-space-4); }
}
</style>
