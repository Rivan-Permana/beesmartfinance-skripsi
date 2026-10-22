<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Textarea from "primevue/textarea"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { Jurnal } from "@/types/api"
import { journalActionLabels, journalDate, journalTotals, type JournalAction } from "./presentation"
const props=defineProps<{target:Jurnal|null;action:Exclude<JournalAction,'edit'>|null;pending?:boolean;error?:string}>()
const emit=defineEmits<{close:[];confirm:[reason:string];refresh:[]}>()
const reason=ref("")
const needsReason=computed(()=>props.action==='cancel'||props.action==='cancelDraft'||props.action==='reject')
const attempted=ref(false)
const errorElement=ref<HTMLElement|null>(null)
const descriptions={cancelDraft:"Jurnal draf menjadi VOID. Slip gaji atau kasbon sumbernya dibuka kembali untuk diperbaiki lalu diposting ulang dengan nomor bukti baru. Alasan wajib.",reject:"Jurnal dikembalikan ke Draf untuk diperbaiki Staff Keuangan. Alasan wajib dan dicatat pada keterangan jurnal.",remove:"Draf manual ini beserta rincian akunnya akan dihapus. Tindakan ini tidak membuat jurnal pembalik.",submit:"Jurnal diajukan kepada Kepala Sekolah. Pengajuan belum memasukkan angka ke buku besar.",approve:"Persetujuan memasukkan jurnal ke buku besar. Periksa bukti dan rincian akun sebelum melanjutkan.",catat:"Jurnal akan masuk ke buku besar. Setelah tercatat, rincian tidak dapat diubah melalui form draf.",cancel:"Penerimaan yang belum tercatat akan dibatalkan melalui transaksi sumbernya. Alasan wajib disimpan bersama pembatalan.",void:"Sistem membuat dan mencatat jurnal pembalik dengan debit/kredit ditukar. Jurnal asli tetap tersimpan untuk riwayat; bukan dihapus."}
const totals=computed(()=>props.target?journalTotals(props.target.detail):null)
const danger=computed(()=>props.action&&['remove','cancel','cancelDraft','void'].includes(props.action))
watch(()=>[props.target?.id,props.action],()=>{reason.value="";attempted.value=false})
watch(()=>props.error,async value=>{if(value){await nextTick();errorElement.value?.focus()}})
function submit(){if(props.pending)return;attempted.value=true;if(needsReason.value&&!reason.value.trim())return;emit('confirm',reason.value.trim())}
</script>
<template>
  <Dialog :visible="!!target&&!!action" @update:visible="value=>{if(!value&&!pending)emit('close')}" :header="action?journalActionLabels[action]:''" modal :draggable="false" :closable="!pending" :close-on-escape="!pending" :style="{width:'480px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup konfirmasi jurnal'}"><template #closeicon><Icon name="x" /></template>
    <template v-if="target&&action"><p class="journal-confirm-proof">{{ target.no_bukti }}</p><p class="journal-confirm-scope">{{ journalDate(target.tanggal) }} · {{ totals?.balanced&&!target.perlu_rekonsiliasi?formatRp(totals.debit):'Nominal belum diketahui' }}</p><p class="journal-confirm-copy">{{ descriptions[action] }}</p><div v-if="error" ref="errorElement" tabindex="-1" class="journal-confirm-error"><Message severity="error" :closable="false">{{ error }} Jika respons terputus, muat ulang daftar untuk memeriksa hasil sebelum mencoba lagi.</Message><Button label="Periksa ulang daftar" severity="secondary" :disabled="pending" @click="emit('refresh')" /></div><form id="journal-action-form" @submit.prevent="submit"><div v-if="needsReason" class="journal-reason"><label for="journal-cancel-reason">{{ action==='reject'?'Alasan penolakan (wajib)':'Alasan pembatalan (wajib)' }}</label><Textarea id="journal-cancel-reason" v-model="reason" autofocus rows="3" maxlength="500" :disabled="pending" :invalid="attempted&&!reason.trim()" :aria-invalid="attempted&&!reason.trim()" :aria-describedby="attempted&&!reason.trim()?'journal-reason-error':undefined" fluid /><small v-if="attempted&&!reason.trim()" id="journal-reason-error">{{ action==='reject'?'Isi alasan penolakan.':action==='cancelDraft'?'Isi alasan pembatalan.':'Isi alasan pembatalan penerimaan.' }}</small></div></form></template>
    <template #footer><Button label="Kembali" severity="secondary" :disabled="pending" @click="emit('close')" /><Button :label="action?journalActionLabels[action]:''" :severity="danger?'danger':undefined" type="submit" form="journal-action-form" :loading="pending"><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
<style scoped>
.journal-confirm-proof{font-weight:600;overflow-wrap:anywhere}.journal-confirm-scope{margin-top:var(--bee-space-1);font-variant-numeric:tabular-nums}.journal-confirm-copy{margin:var(--bee-space-3) 0 var(--bee-space-5);color:var(--app-text-muted)}.journal-reason{display:grid;gap:var(--bee-space-2)}.journal-reason label{font-weight:500}.journal-reason small{color:var(--bee-color-critical)}.journal-confirm-error{display:grid;justify-items:start;gap:var(--bee-space-3);margin-bottom:var(--bee-space-5)}
</style>
