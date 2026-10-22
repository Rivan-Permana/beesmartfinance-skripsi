<script setup lang="ts">
import { computed, ref } from "vue"
import Button from "primevue/button"
import Dialog from "primevue/dialog"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import TagihanDirectory from "@/features/tagihan/TagihanDirectory.vue"
import TagihanPaymentDialog from "@/features/tagihan/TagihanPaymentDialog.vue"
import TagihanHistoryDialog from "@/features/tagihan/TagihanHistoryDialog.vue"
import InvoicePreview from "@/features/tagihan/InvoicePreview.vue"
import { paymentPayload, paymentTotal, paymentValid, type TagihanPaymentForm } from "@/features/tagihan/payment"
import { canPayTagihan, tagihanPeriod } from "@/features/tagihan/presentation"
import Icon from "@/shared/components/PhosphorIcon.vue"
import type { PembayaranTagihan, StrukTagihan, Tagihan } from "@/types/api"
import { billingAccounts, billingNames, billingSamples } from "./billing-fixtures"
const toast = useToast()
const confirm = useConfirm()
const rows = ref(structuredClone(billingSamples))
const target = ref<Tagihan | null>(null)
const visible = ref(false)
const history = ref<Tagihan | null>(null)
const invoiceTarget = ref<Tagihan | null>(null)
const form = ref<TagihanPaymentForm>({tanggal:new Date(),no_bukti:"",akun_kas:"111",request_id:"",alokasi:[]})
function pay(row: Tagihan) {
  if (!canPayTagihan(row)) return
  target.value = row
  form.value = {tanggal:new Date(),no_bukti:"",akun_kas:"111",request_id:crypto.randomUUID(),alokasi:row.detail.filter(line => Number(line.nominal) > Number(line.total_terbayar ?? 0)).map(line => ({detail:line.id!,label:line.keterangan,nominal:0,sisa:Number(line.nominal)-Number(line.total_terbayar ?? 0)}))}
  visible.value = true
}
function save() {
  const current=target.value
  if (!current || !canPayTagihan(current) || !paymentValid(form.value)) return
  const amount=paymentTotal(form.value)
  const payload=paymentPayload(form.value)
  const remaining=Math.round(Number(current.sisa_tagihan)*100)-Math.round(amount*100)
  const entry: PembayaranTagihan = {id:Date.now(),tanggal:payload.tanggal,no_bukti:payload.no_bukti,nominal:payload.nominal,akun_kas:form.value.akun_kas,jurnal:"CONTOH",jurnal_status:"DRAFT",created_by:null,dibatalkan:false,alasan_batal:"",dibatalkan_pada:null,alokasi:form.value.alokasi.filter(line => line.nominal>0).map(line => ({detail:line.detail,nominal:line.nominal.toFixed(2)}))}
  rows.value=rows.value.map(row => row.id!==current.id ? row : {...row,total_terbayar:((Math.round(Number(row.total_terbayar)*100)+Math.round(amount*100))/100).toFixed(2),sisa_tagihan:(remaining/100).toFixed(2),status:remaining===0?"LUNAS":"SEBAGIAN",pembayaran:[...row.pembayaran,entry],detail:row.detail.map(line => ({...line,total_terbayar:((Math.round(Number(line.total_terbayar ?? 0)*100)+Math.round((form.value.alokasi.find(item => item.detail===line.id)?.nominal ?? 0)*100))/100).toFixed(2)}))})
  visible.value=false
  toast.add({severity:"success",summary:"Pembayaran contoh dicatat",detail:"Hanya mengubah data contoh di halaman ini.",life:4000})
}
function remove(row: Tagihan) { confirm.require({header:"Hapus tagihan contoh?",message:"Hanya menghapus contoh ini. Data sekolah tidak berubah.",acceptLabel:"Hapus contoh",rejectLabel:"Kembali",acceptProps:{severity:"danger"},accept:()=>{rows.value=rows.value.filter(item=>item.id!==row.id)}}) }
function explainEditor() { toast.add({severity:"info",summary:"Pembuatan dan perubahan tagihan",detail:"Tersedia di halaman Tagihan aplikasi. Spesimen ini memperagakan daftar, pembayaran, riwayat, dan faktur.",life:5000}) }
function reset() { rows.value=structuredClone(billingSamples) }
const invoice=computed<StrukTagihan|null>(()=>invoiceTarget.value ? {no_tagihan:invoiceTarget.value.id,sekolah:"RA Lebah Madu",siswa:billingNames.get(invoiceTarget.value.siswa)!,nis:`CONTOH-00${invoiceTarget.value.siswa}`,kelompok:null,periode:tagihanPeriod(invoiceTarget.value),periode_bulan:invoiceTarget.value.periode_bulan,periode_tahun:invoiceTarget.value.periode_tahun,status:invoiceTarget.value.status,sections:[],rincian:invoiceTarget.value.detail.map(line=>({komponen:line.komponen,label:line.keterangan,nominal:line.nominal})),total:invoiceTarget.value.total,no_jurnal:null,total_terbayar:invoiceTarget.value.total_terbayar,sisa_tagihan:invoiceTarget.value.sisa_tagihan,perlu_rekonsiliasi:invoiceTarget.value.perlu_rekonsiliasi} : null)
</script>

<template>
  <section id="layar-tagihan" class="system-section"><header class="system-section-heading"><h2>Dari tagihan ke bukti pembayaran.</h2><p>Daftar, form pembayaran, riwayat, dan faktur memakai komponen aplikasi. Coba cicilan atau isi seluruh sisa, lalu periksa riwayatnya. Semua data fiktif dan kembali ke awal saat halaman dimuat ulang.</p></header>
    <TagihanDirectory :rows="rows" :names="billingNames" @pay="pay" @history="history = $event" @invoice="invoiceTarget = $event" @remove="remove" @edit="explainEditor" @create="explainEditor" />
    <Button class="billing-reset" label="Pulihkan tagihan contoh" severity="secondary" text @click="reset" />
    <TagihanPaymentDialog v-model="visible" v-model:form="form" :target="target" :student-name="target ? billingNames.get(target.siswa)! : ''" :accounts="billingAccounts" @save="save" />
    <TagihanHistoryDialog v-model:target="history" />
    <Dialog :visible="!!invoiceTarget" @update:visible="value=>{if(!value) invoiceTarget=null}" header="Faktur contoh" modal :draggable="false" :style="{width:'32rem'}" :close-button-props="{severity:'secondary',text:true}"><template #closeicon><Icon name="x" /></template><InvoicePreview v-if="invoice" :invoice="invoice" /><template #footer><Button label="Tutup contoh faktur" severity="secondary" @click="invoiceTarget = null" /></template></Dialog>
  </section>
</template>
<style scoped>
.billing-reset { margin-top: var(--bee-space-3); }
</style>
