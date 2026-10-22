<script setup lang="ts">
import { computed } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import Message from "primevue/message"
import Tag from "primevue/tag"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { formatRp } from "@/core/format"
import type { Coa, Jurnal } from "@/types/api"
import { journalActionLabels, journalActions, journalDate, journalSource, journalState, journalTotals, type JournalAccess, type JournalAction } from "./presentation"
const props=defineProps<{accounts:Coa[];access:JournalAccess;accountsLoading?:boolean;accountsError?:boolean}>()
const target=defineModel<Jurnal|null>("target",{default:null})
const emit=defineEmits<{action:[action:JournalAction,row:Jurnal];reloadAccounts:[]}>()
const totals=computed(()=>target.value?journalTotals(target.value.detail):null)
const actions=computed(()=>target.value?journalActions(target.value,props.access).sort((a,b)=>["catat","approve","reject","submit","edit","cancel","void","remove"].indexOf(a)-["catat","approve","reject","submit","edit","cancel","void","remove"].indexOf(b)):[])
function accountName(code:string){return props.accounts.find(account=>account.kode_akun===code)?.nama_akun??"Nama akun belum dimuat"}
</script>
<template>
  <Dialog :visible="!!target" @update:visible="value=>{if(!value)target=null}" header="Rincian jurnal" modal :draggable="false" :style="{width:'820px'}" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup rincian jurnal'}"><template #closeicon><Icon name="x" /></template>
    <template v-if="target"><div class="journal-detail-heading"><div><h3>{{ target.no_bukti }}</h3><p>{{ journalDate(target.tanggal) }} · {{ journalSource(target.tipe_sumber) }}</p></div><Tag :value="journalState(target).label" :severity="journalState(target).severity" /></div><p class="journal-detail-description">{{ target.keterangan||'Tanpa keterangan transaksi.' }}</p>
      <Message v-if="target.perlu_rekonsiliasi" severity="warn" :closable="false">Rincian penerimaan perlu dicocokkan melalui transaksi sumber. Jurnal belum dapat dicatat atau disetujui.</Message>
      <Message v-else-if="target.status==='PENDING'&&access.principal&&target.created_by===access.userId" severity="info" :closable="false">Jurnal ini dibuat oleh Anda. Persetujuan harus dilakukan oleh pengguna lain yang berwenang.</Message>
      <div v-if="accountsError" class="journal-detail-notice"><p>Nama akun belum berhasil dimuat. Kode dan nominal jurnal tetap ditampilkan.</p><Button label="Muat ulang nama akun" severity="secondary" text :loading="accountsLoading" @click="emit('reloadAccounts')" /></div>
      <h4 class="journal-detail-section">Rincian debit dan kredit</h4><div class="journal-detail-scroll" tabindex="0" role="region" aria-label="Rincian akun jurnal"><table class="journal-detail-table"><thead><tr><th scope="col">Akun</th><th scope="col" class="numeric">Debit (Rp)</th><th scope="col" class="numeric">Kredit (Rp)</th></tr></thead><tbody><tr v-for="(line,index) in target.detail" :key="index"><th scope="row"><span>{{ line.kode_akun }}</span><small>{{ accountName(line.kode_akun) }}</small></th><td class="numeric">{{ Number.isFinite(Number(line.debit))&&line.debit!==''?formatRp(line.debit):'Belum diketahui' }}</td><td class="numeric">{{ Number.isFinite(Number(line.kredit))&&line.kredit!==''?formatRp(line.kredit):'Belum diketahui' }}</td></tr></tbody><tfoot><tr><th scope="row">Total</th><td class="numeric">{{ totals?formatRp(totals.debit):'Belum diketahui' }}</td><td class="numeric">{{ totals?formatRp(totals.kredit):'Belum diketahui' }}</td></tr></tfoot></table></div>
      <p class="journal-detail-note">{{ totals?.balanced?'Total debit dan kredit seimbang.':'Periksa rincian: total debit dan kredit belum dapat dinyatakan seimbang.' }} {{ target.status==='DRAFT'?'Draf belum masuk buku besar.':'' }}</p>
      <div v-if="actions.length" class="journal-detail-actions" role="group" aria-label="Tindakan jurnal"><Button v-for="action in actions" :key="action" :label="journalActionLabels[action]" :severity="['remove','cancel','void'].includes(action)?'danger':['catat','approve','submit'].includes(action)?undefined:'secondary'" :outlined="['remove','cancel','void'].includes(action)" :disabled="action==='edit'&&(accountsLoading||accountsError)" @click="emit('action',action,target)" /></div>
      <p v-else class="journal-detail-note">Tidak ada tindakan lanjutan yang tersedia untuk status dan kewenangan Anda saat ini.</p>
    </template>
    <template #footer><Button label="Tutup rincian" severity="secondary" @click="target=null" /></template>
  </Dialog>
</template>
<style scoped>
.journal-detail-heading{display:flex;align-items:start;justify-content:space-between;gap:var(--bee-space-4);flex-wrap:wrap}.journal-detail-heading h3{font-size:var(--bee-type-section);overflow-wrap:anywhere}.journal-detail-heading p,.journal-detail-note,.journal-detail-notice{color:var(--app-text-muted);font-size:var(--bee-type-caption);margin-top:var(--bee-space-2)}.journal-detail-description{margin:var(--bee-space-5) 0;overflow-wrap:anywhere}.journal-detail-section{font-size:var(--bee-type-ui);margin:var(--bee-space-5) 0 var(--bee-space-3)}.journal-detail-scroll{overflow:auto;max-width:100%}.journal-detail-table{width:100%;border-collapse:collapse;font-size:var(--bee-type-ui)}.journal-detail-table th,.journal-detail-table td{padding:var(--bee-space-3);text-align:start;border-bottom:1px solid var(--app-border)}.journal-detail-table th{font-weight:500}.journal-detail-table thead th{color:var(--app-text-muted);font-size:var(--bee-type-caption)}.journal-detail-table small{display:block;color:var(--app-text-muted);font-weight:400;max-width:36ch;overflow-wrap:anywhere}.journal-detail-table .numeric{text-align:end;white-space:nowrap;font-variant-numeric:tabular-nums}.journal-detail-table tfoot{background:var(--bee-color-surface-subtle)}.journal-detail-actions{display:flex;flex-wrap:wrap;gap:var(--bee-space-3);margin-top:var(--bee-space-5)}
@media(max-width:520px){.journal-detail-actions{display:grid;grid-template-columns:minmax(0,1fr)}.journal-detail-table th,.journal-detail-table td{padding:var(--bee-space-3) var(--bee-space-2)}}
</style>
