<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import { useToast } from "primevue/usetoast"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import { formatRp } from "@/core/format"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { siswaApi } from "@/features/siswa/api"
import type { InvoiceGabungan as InvoiceData } from "@/types/api"
import InvoiceGabungan from "./InvoiceGabungan.vue"
import { invoiceWaText, nomorWa } from "./invoiceGabungan"

/** Invoice semua tunggakan satu siswa. Dibuka dari Data Siswa dan Tunggakan Tagihan. */
const props = defineProps<{ siswaId: number | null }>()
const emit = defineEmits<{ close: [] }>()
const toast = useToast()
const invoice = ref<InvoiceData | null>(null)
const loading = ref(false)
const error = ref("")
const visible = computed({ get: () => props.siswaId != null, set: (open) => { if (!open) emit("close") } })
const waTargets = computed(() => (invoice.value?.kontak_ortu ?? [])
  .map((kontak) => ({ ...kontak, wa: nomorWa(kontak.nomor) }))
  .filter((kontak): kontak is { label: string; nomor: string; wa: string } => kontak.wa !== null))
const hasBill = computed(() => Boolean(invoice.value?.sections.length))

async function load(id: number) {
  loading.value = true
  error.value = ""
  invoice.value = null
  try {
    invoice.value = await siswaApi.invoiceGabungan(id)
  } catch (e) {
    const err = friendlyError(e, "Invoice siswa belum berhasil dimuat.")
    error.value = [err.summary, err.detail].filter(Boolean).join(". ")
  } finally {
    loading.value = false
  }
}
watch(() => props.siswaId, (id) => { if (id != null) void load(id) }, { immediate: true })

async function copyText() {
  if (!invoice.value) return
  try {
    await navigator.clipboard.writeText(invoiceWaText(invoice.value))
    notifySuccess(toast, "Teks invoice disalin. Tempel di WhatsApp.")
  } catch (e) {
    notifyError(toast, e, "Teks belum berhasil disalin.")
  }
}
function openWa(nomor: string) {
  if (!invoice.value) return
  window.open(`https://wa.me/${nomor}?text=${encodeURIComponent(invoiceWaText(invoice.value))}`, "_blank", "noopener")
}
function selesaiCetak() {
  document.body.classList.remove("bee-print-struk")
  window.removeEventListener("afterprint", selesaiCetak)
}
function cetak() {
  document.body.classList.add("bee-print-struk")
  window.addEventListener("afterprint", selesaiCetak, { once: true })
  try {
    window.print()
  } catch (e) {
    selesaiCetak()
    notifyError(toast, e, "Gagal membuka dialog cetak.")
  }
}
onBeforeUnmount(selesaiCetak)
</script>

<template>
  <Dialog v-model:visible="visible" header="Invoice tunggakan siswa" modal :draggable="false" :style="{ width: '600px' }" class="struk-dialog invoice-gabungan-dialog" :pt="{ mask: { class: 'struk-print-mask' } }" :close-button-props="{ severity: 'secondary', text: true, 'aria-label': 'Tutup invoice' }">
    <template #closeicon><Icon name="x" /></template>
    <div v-if="loading" class="invoice-gabungan-state" role="status"><Icon name="arrows-clockwise" class="bee-spin" /><span>Mengumpulkan tagihan siswa</span></div>
    <div v-else-if="error" class="invoice-gabungan-state"><Message severity="error" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ error }}</Message><Button label="Coba muat ulang" severity="secondary" @click="siswaId != null && load(siswaId)" /></div>
    <template v-else-if="invoice">
      <div class="invoice-gabungan-notes">
        <Message v-if="invoice.perlu_dicocokkan.length" severity="warn" :closable="false"><template #icon><Icon name="warning-circle" /></template>{{ invoice.perlu_dicocokkan.length }} tagihan ({{ invoice.perlu_dicocokkan.map((t) => t.periode).join(", ") }}, total {{ formatRp(invoice.perlu_dicocokkan.reduce((sum, t) => sum + Number(t.total), 0)) }}) belum ikut dihitung karena pembayaran lamanya perlu dicocokkan.</Message>
        <Message v-if="!invoice.rekening" severity="info" :closable="false"><template #icon><Icon name="info" /></template>Rekening jenjang {{ invoice.jenjang ?? "siswa ini" }} belum diatur. Isi di menu Kelompok, bagian Jenjang.</Message>
      </div>
      <InvoiceGabungan id="struk-print-area" :invoice="invoice" />
    </template>
    <template #footer>
      <div class="invoice-gabungan-actions">
        <Button label="Tutup" severity="secondary" text @click="emit('close')" />
        <Button label="Salin teks WA" severity="secondary" :disabled="!hasBill" @click="copyText"><template #icon><Icon name="file-text" /></template></Button>
        <Button v-for="target in waTargets" :key="target.label" :label="`WA ${target.label}`" severity="secondary" :disabled="!hasBill" :aria-label="`Buka WhatsApp ke ${target.label} (${target.nomor})`" @click="openWa(target.wa)"><template #icon><Icon name="arrow-up-right" /></template></Button>
        <Button label="Cetak" :disabled="!invoice" @click="cetak"><template #icon><Icon name="printer" /></template></Button>
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.invoice-gabungan-state { display: grid; justify-items: center; gap: var(--bee-space-3); padding: var(--bee-space-6) 0; color: var(--app-text-muted); }
.invoice-gabungan-notes { display: grid; gap: var(--bee-space-2); margin-bottom: var(--bee-space-4); }
.invoice-gabungan-notes:empty { display: none; }
.invoice-gabungan-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--bee-space-2); }
@media print { .invoice-gabungan-notes { display: none; } }
@media (max-width: 600px) { .invoice-gabungan-actions { display: grid; grid-template-columns: 1fr 1fr; } }
</style>
