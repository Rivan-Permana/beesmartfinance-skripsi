<script setup lang="ts">
import { computed } from "vue"
import type { SaldoRow } from "@/types/api"
import { reportCents, reportMoney, sumAmounts } from "./presentation"
const props=defineProps<{rows:SaldoRow[];caption:string;detailed?:boolean;totalLabel?:string;total?:string|number|null;compactOnPrint?:boolean}>()
const debit=computed(()=>sumAmounts(props.rows.map(row=>row.total_debit)))
const credit=computed(()=>sumAmounts(props.rows.map(row=>row.total_kredit)))
const allZero=computed(()=>props.rows.length>0&&props.rows.every(row=>reportCents(row.saldo_akhir)===0))
</script>
<template>
  <div class="report-scroll" tabindex="0" role="region" :aria-label="caption"><table class="report-table" :class="{'report-table-detailed':detailed}"><caption>{{ caption }}</caption><thead><tr><th scope="col">Akun</th><th v-if="detailed" scope="col">Posisi normal</th><th v-if="detailed" scope="col" class="numeric">Debit kumulatif</th><th v-if="detailed" scope="col" class="numeric">Kredit kumulatif</th><th scope="col" class="numeric">{{ detailed?'Saldo akhir':'Saldo (Rp)' }}</th></tr></thead><tbody><tr v-for="row in rows" :key="row.kode_akun" :class="{'report-print-zero':compactOnPrint&&reportCents(row.saldo_akhir)===0}"><th scope="row"><span class="report-account-name">{{ row.nama_akun }}</span><small class="report-account-code">{{ row.kode_akun }}</small></th><td v-if="detailed">{{ row.posisi_normal==='D'?'Debit':'Kredit' }}</td><td v-if="detailed" class="numeric">{{ reportMoney(row.total_debit) }}</td><td v-if="detailed" class="numeric">{{ reportMoney(row.total_kredit) }}</td><td class="numeric" :class="{'report-negative':Number(row.saldo_akhir)<0}">{{ reportMoney(row.saldo_akhir) }}</td></tr><tr v-if="!rows.length"><td :colspan="detailed?5:2" class="report-empty-cell">Tidak ada akun pada bagian ini.</td></tr><tr v-if="compactOnPrint&&allZero" class="report-print-empty"><td :colspan="detailed?5:2" class="report-empty-cell">Tidak ada akun bersaldo pada periode ini.</td></tr></tbody><tfoot v-if="detailed&&rows.length"><tr><th scope="row" colspan="2">Total debit dan kredit</th><td class="numeric">{{ reportMoney(debit) }}</td><td class="numeric">{{ reportMoney(credit) }}</td><td class="numeric">—</td></tr></tfoot><tfoot v-else-if="totalLabel"><tr><th scope="row">{{ totalLabel }}</th><td class="numeric">{{ reportMoney(total) }}</td></tr></tfoot></table></div>
</template>
