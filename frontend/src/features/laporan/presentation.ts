import { formatRp } from "@/core/format"
import type { BukuBesarRow, Coa, LabaRugiResult, PosisiKeuanganResult, RealisasiAnggaranRow, SaldoRow } from "@/types/api"

export const REPORTS = [
  { id: "neraca", title: "Neraca saldo", description: "Saldo awal bertanggal dan mutasi jurnal tercatat hingga akhir tahun." },
  { id: "lr", title: "Laba rugi", description: "Pendapatan dan beban pada tahun yang diterapkan, termasuk saldo awal bertanggal yang relevan." },
  { id: "pk", title: "Posisi keuangan", description: "Rincian aset, liabilitas, dan ekuitas hingga akhir tahun." },
  { id: "ra", title: "Realisasi anggaran", description: "Pagu gabungan per akun dan tahun anggaran dibandingkan dengan realisasi jurnal tercatat pada tahun kalender yang sama." },
  { id: "bb", title: "Buku besar", description: "Mutasi satu akun per bulan, termasuk saldo awal periode." },
] as const
export type ReportKind = typeof REPORTS[number]["id"]
export interface ReportFilters { tahun: number; bulan: number; account: Pick<Coa,"kode_akun"|"nama_akun"|"posisi_normal"> | null }
export type ReportSnapshot = { scope: ReportFilters } & (
  { kind:"neraca";data:SaldoRow[] } | { kind:"lr";data:LabaRugiResult } | { kind:"pk";data:PosisiKeuanganResult }
  | { kind:"ra";data:RealisasiAnggaranRow[] } | { kind:"bb";data:BukuBesarRow[] }
)
export const reportMonths = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
export function reportPeriod(kind:ReportKind,scope:ReportFilters){
  if(kind==='neraca'||kind==='pk')return `Hingga 31 Desember ${scope.tahun}`
  if(kind==='lr')return `Januari–Desember ${scope.tahun}`
  if(kind==='ra')return `Tahun anggaran ${scope.tahun}`
  return `${reportMonths[scope.bulan-1]} ${scope.tahun}`
}
export function reportFiltersChanged(kind:ReportKind,draft:ReportFilters,applied:ReportFilters){
  return draft.tahun!==applied.tahun||(kind==='bb'&&(draft.bulan!==applied.bulan||draft.account?.kode_akun!==applied.account?.kode_akun))
}
// Reports can be negative. Work in cents and reject missing/invalid amounts instead of showing zero.
export function reportCents(value:unknown):number|null{
  if((typeof value!=='string'&&typeof value!=='number')||(typeof value==='string'&&!value.trim()))return null
  const number=Number(value),scaled=number*100,rounded=Math.round(scaled)
  return Number.isFinite(number)&&Number.isSafeInteger(rounded)&&Math.abs(scaled-rounded)<=Number.EPSILON*Math.max(1,Math.abs(scaled))*4?rounded:null
}
export function reportMoney(value:unknown){const amount=reportCents(value);return amount===null?'Belum diketahui':formatRp(amount/100)}
export function sumAmounts(values:unknown[]):number|null{
  let total=0
  for(const value of values){const amount=reportCents(value);if(amount===null)return null;total+=amount;if(!Number.isSafeInteger(total))return null}
  return total/100
}
export function groupBalance(rows:SaldoRow[],normal:'D'|'K'){
  return sumAmounts(rows.map(row=>{const value=reportCents(row.saldo_akhir);return value===null?null:(row.posisi_normal===normal?value:-value)/100}))
}
export function ledgerBalances(rows:BukuBesarRow[],normal:'D'|'K'|undefined){
  let balance:number|null=normal?0:null
  return rows.map(row=>{
    const debit=reportCents(row.debit),credit=reportCents(row.kredit)
    if(balance!==null){
      if(debit===null||credit===null)balance=null
      else{balance+=(debit-credit)*(normal==='K'?-1:1);if(!Number.isSafeInteger(balance))balance=null}
    }
    return {...row,saldo:balance===null?null:balance/100}
  })
}
export function budgetPercent(pagu:unknown,realisasi:unknown){
  const budget=reportCents(pagu),actual=reportCents(realisasi)
  if(budget===null||budget<=0||actual===null)return null
  const percentage=actual/budget*100
  return {value:Math.max(0,Math.min(100,percentage)),label:`${new Intl.NumberFormat('id-ID',{maximumFractionDigits:1}).format(percentage)}%`}
}
