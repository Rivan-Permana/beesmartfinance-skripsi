import { formatLocalDate } from "@/core/format"
import type { Tagihan } from "@/types/api"

export interface TagihanPaymentForm {
  tanggal: Date
  no_bukti: string
  akun_kas: string
  request_id: string
  alokasi: { detail: number; label: string; nominal: number; sisa: number }[]
}
export function paymentTotal(form: TagihanPaymentForm) {
  return form.alokasi.reduce((sum, line) => sum + Math.round(line.nominal * 100), 0) / 100
}
export function paymentValid(form: TagihanPaymentForm) {
  return Boolean(form.no_bukti.trim() && form.akun_kas && form.tanggal
    && Number.isFinite(form.tanggal.getTime()) && paymentTotal(form) > 0
    && form.alokasi.every(line => Number.isFinite(line.nominal) && line.nominal >= 0 && line.nominal <= line.sisa))
}

export function paymentPayload(form: TagihanPaymentForm) {
  return {
    tanggal: formatLocalDate(form.tanggal),
    no_bukti: form.no_bukti.trim(), akun_kas: form.akun_kas, request_id: form.request_id,
    nominal: paymentTotal(form).toFixed(2),
    alokasi: form.alokasi.filter(line => line.nominal > 0).map(line => ({detail:line.detail,nominal:line.nominal.toFixed(2)})),
  }
}

/** Form kosong untuk satu tagihan: hanya komponen yang masih bersisa. */
export function paymentFormFor(tagihan: Tagihan, akunKas = ""): TagihanPaymentForm {
  return {
    tanggal: new Date(), no_bukti: "", akun_kas: akunKas, request_id: crypto.randomUUID(),
    alokasi: tagihan.detail.filter((d) => d.id && Number(d.nominal) > Number(d.total_terbayar ?? 0)).map((d) => ({
      detail: d.id!, label: d.keterangan || d.komponen, nominal: 0,
      sisa: Number(d.nominal) - Number(d.total_terbayar ?? 0),
    })),
  }
}
