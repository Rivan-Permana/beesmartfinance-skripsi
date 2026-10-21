<script setup lang="ts">
import { computed } from "vue"
import ProgressBar from "primevue/progressbar"
import AccountReportTable from "./AccountReportTable.vue"
import { budgetPercent, groupBalance, ledgerBalances, reportMoney, sumAmounts, type ReportSnapshot } from "./presentation"
import { journalDate } from "@/features/jurnal/presentation"
const props=defineProps<{snapshot:ReportSnapshot}>()
const assets=computed(()=>props.snapshot.kind==='pk'?groupBalance(props.snapshot.data.aset,'D'):null)
const liabilities=computed(()=>props.snapshot.kind==='pk'?groupBalance(props.snapshot.data.liabilitas,'K'):null)
const equity=computed(()=>props.snapshot.kind==='pk'?groupBalance(props.snapshot.data.ekuitas,'K'):null)
const difference=computed(()=>assets.value===null||liabilities.value===null||equity.value===null?null:sumAmounts([assets.value,-liabilities.value,-equity.value]))
const ledger=computed(()=>props.snapshot.kind==='bb'?ledgerBalances(props.snapshot.data,props.snapshot.scope.account?.posisi_normal):[])
const lastBalance=computed(()=>ledger.value.length?ledger.value[ledger.value.length-1]!.saldo:0)
</script>
<template>
  <template v-if="snapshot.kind==='neraca'">
    <AccountReportTable :rows="snapshot.data" caption="Neraca saldo dalam rupiah" detailed />
    <p class="report-explanation">Debit dan kredit kumulatif termasuk saldo awal bertanggal. Saldo akhir setiap akun mengikuti posisi normalnya; kolom saldo tidak dijumlahkan lintas posisi.</p>
  </template>
  <template v-else-if="snapshot.kind==='lr'">
    <div class="report-statement-grid"><section class="report-statement"><h3>Pendapatan</h3><AccountReportTable :rows="snapshot.data.pendapatan" caption="Rincian pendapatan" total-label="Total pendapatan" :total="snapshot.data.total_pendapatan" compact-on-print /></section><section class="report-statement"><h3>Beban</h3><AccountReportTable :rows="snapshot.data.beban" caption="Rincian beban" total-label="Total beban" :total="snapshot.data.total_beban" compact-on-print /></section></div>
    <dl class="report-result"><div><dt>{{ Number(snapshot.data.laba_rugi)<0?'Rugi periode':'Laba periode' }}</dt><dd :class="{'report-negative':Number(snapshot.data.laba_rugi)<0}">{{ reportMoney(snapshot.data.laba_rugi) }}</dd></div></dl>
    <p class="report-explanation">Total mengikuti cakupan tahun yang diterapkan. Laba/rugi berbeda dari mutasi kas. Saat dicetak, akun bersaldo Rp0 disembunyikan dari rincian; total tetap mencakup seluruh akun.</p>
  </template>
  <template v-else-if="snapshot.kind==='pk'">
    <div class="report-statement-grid"><section class="report-statement"><h3>Aset</h3><AccountReportTable :rows="snapshot.data.aset" caption="Rincian aset" total-label="Total aset" :total="assets" /></section><div class="report-statement-stack"><section class="report-statement"><h3>Liabilitas</h3><AccountReportTable :rows="snapshot.data.liabilitas" caption="Rincian liabilitas" total-label="Total liabilitas" :total="liabilities" /></section><section class="report-statement"><h3>Ekuitas</h3><AccountReportTable :rows="snapshot.data.ekuitas" caption="Rincian ekuitas" total-label="Total ekuitas" :total="equity" /></section></div></div>
    <dl class="report-result"><div><dt>Total aset</dt><dd>{{ reportMoney(assets) }}</dd></div><div><dt>Liabilitas + ekuitas</dt><dd>{{ reportMoney(liabilities===null||equity===null?null:sumAmounts([liabilities,equity])) }}</dd></div><div><dt>Selisih aset − liabilitas − ekuitas</dt><dd :class="{'report-negative':difference!==null&&difference!==0}">{{ reportMoney(difference) }}</dd></div></dl>
    <p class="report-explanation">Total memperhitungkan posisi normal akun, termasuk akun kontra. Laba rugi tahun berjalan ditampilkan terpisah pada laporan Laba rugi; tidak ditambahkan otomatis sebagai akun ekuitas. Periksa rincian bila terdapat selisih.</p>
  </template>
  <template v-else-if="snapshot.kind==='ra'">
    <div class="report-scroll" tabindex="0" role="region" aria-label="Realisasi anggaran per akun"><table class="report-table report-budget-table"><caption>Realisasi anggaran dalam rupiah</caption><thead><tr><th scope="col">Akun anggaran</th><th scope="col" class="numeric">Pagu</th><th scope="col" class="numeric">Realisasi</th><th scope="col" class="numeric">Sisa pagu</th><th scope="col">Realisasi dari pagu</th></tr></thead><tbody><tr v-for="row in snapshot.data" :key="`${row.tahun_anggaran}-${row.kode_akun}`"><th scope="row"><span class="report-account-name">{{ row.nama_akun }}</span><small class="report-account-code">{{ row.kode_akun }}</small></th><td class="numeric">{{ reportMoney(row.pagu) }}</td><td class="numeric">{{ reportMoney(row.realisasi) }}</td><td class="numeric" :class="{'report-negative':Number(row.sisa_pagu)<0}">{{ reportMoney(row.sisa_pagu) }}</td><td><div v-if="budgetPercent(row.pagu,row.realisasi)" class="report-budget-usage"><ProgressBar :value="budgetPercent(row.pagu,row.realisasi)!.value" :show-value="false" :aria-label="`Realisasi akun ${row.kode_akun} dari pagu ${reportMoney(row.pagu)}`" :aria-valuetext="budgetPercent(row.pagu,row.realisasi)!.label" /><span>{{ budgetPercent(row.pagu,row.realisasi)!.label }}</span></div><span v-else class="report-explanation">Persentase tidak tersedia</span></td></tr><tr v-if="!snapshot.data.length"><td colspan="5" class="report-empty-cell">Belum ada anggaran pada tahun ini.</td></tr></tbody></table></div>
    <p class="report-explanation">Pagu menjumlahkan semua entri anggaran akun pada tahun yang dipilih, termasuk entri bulanan dan tahunan; carry over tidak ditambahkan otomatis. Persentase memakai pagu gabungan sebagai pembagi. Pagu nol tidak dianggap 0%; realisasi yang melampaui pagu tetap menampilkan persentase aktual.</p>
  </template>
  <template v-else-if="snapshot.kind==='bb'">
    <dl class="report-ledger-summary"><div><dt>Posisi normal akun</dt><dd>{{ snapshot.scope.account?.posisi_normal==='K'?'Kredit':'Debit' }}</dd></div><div><dt>Baris dalam laporan</dt><dd>{{ snapshot.data.length }}</dd></div><div><dt>Saldo akhir cakupan</dt><dd :class="{'report-negative':lastBalance!==null&&lastBalance<0}">{{ reportMoney(lastBalance) }}</dd></div></dl>
    <div class="report-scroll" tabindex="0" role="region" aria-label="Mutasi buku besar dan saldo berjalan"><table class="report-table report-ledger-table"><caption>Buku besar dalam rupiah, termasuk saldo awal periode</caption><thead><tr><th scope="col">Tanggal dan bukti</th><th scope="col">Keterangan</th><th scope="col" class="numeric">Debit</th><th scope="col" class="numeric">Kredit</th><th scope="col" class="numeric">Saldo berjalan</th></tr></thead><tbody><tr v-for="(row,index) in ledger" :key="index"><th scope="row"><span>{{ journalDate(row.tanggal) }}</span><small class="report-account-code">{{ row.no_bukti }}</small></th><td>{{ row.keterangan||'Tanpa keterangan' }}</td><td class="numeric">{{ reportMoney(row.debit) }}</td><td class="numeric">{{ reportMoney(row.kredit) }}</td><td class="numeric" :class="{'report-negative':row.saldo!==null&&row.saldo<0}">{{ reportMoney(row.saldo) }}</td></tr><tr v-if="!ledger.length"><td colspan="5" class="report-empty-cell">Tidak ada baris saldo awal atau mutasi untuk akun pada bulan ini.</td></tr></tbody></table></div>
    <p class="report-explanation">Saldo berjalan mengikuti posisi normal akun dan urutan pencatatan dalam laporan. Baris SALDO-AWAL adalah saldo pembuka, bukan transaksi baru. Nominal yang belum diketahui membuat saldo berikutnya tetap belum diketahui.</p>
  </template>
</template>
