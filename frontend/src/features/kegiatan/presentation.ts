import type { Kegiatan, KegiatanStatus } from "@/types/api"
export const KEGIATAN_STATUS = {
  RENCANA:{label:"Rencana",severity:"secondary"},
  BERJALAN:{label:"Berjalan",severity:"info"},
  SELESAI:{label:"Selesai",severity:"success"},
} as const satisfies Record<KegiatanStatus,{label:string;severity:string}>
export const kegiatanStatusOptions=Object.entries(KEGIATAN_STATUS).map(([value,state])=>({value,label:state.label}))
export function budgetUsage(pagu: string | number, ratio: number) {
  if (!Number.isFinite(Number(pagu)) || Number(pagu)<=0 || !Number.isFinite(ratio)) return null
  return {value:Math.max(0,Math.min(100,ratio*100)),label:new Intl.NumberFormat("id-ID",{style:"percent",maximumFractionDigits:1}).format(ratio)}
}
export interface RealisasiForm {tanggal:Date;deskripsi:string;nominal:number}
export function realisasiValid(form: RealisasiForm, target: Kegiatan | null) {
  return Boolean(target && form.tanggal && Number.isFinite(form.tanggal.getTime()) && Number.isFinite(form.nominal) && form.nominal>0 && form.nominal<=Number(target.sisa_pagu))
}
