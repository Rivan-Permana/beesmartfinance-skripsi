import { api } from "@/core/api"
import type {
  BukuBesarRow,
  LabaRugiResult,
  PosisiKeuanganResult,
  RealisasiAnggaranRow,
  SaldoRow,
} from "@/types/api"

export interface LaporanPeriod {
  tahun?: number
  bulan?: number
  tanggal?: string
  periode?: number
}

export const laporanApi = {
  neracaSaldo: (period?: LaporanPeriod) =>
    api.get<SaldoRow[]>("/laporan/neraca-saldo/", { params: period }).then((r) => r.data),
  labaRugi: (period?: LaporanPeriod) =>
    api.get<LabaRugiResult>("/laporan/laba-rugi/", { params: period }).then((r) => r.data),
  posisiKeuangan: (period?: LaporanPeriod) =>
    api.get<PosisiKeuanganResult>("/laporan/posisi-keuangan/", { params: period }).then((r) => r.data),
  realisasiAnggaran: (tahun?: number) =>
    api
      .get<RealisasiAnggaranRow[]>("/laporan/realisasi-anggaran/", {
        params: tahun ? { tahun } : {},
      })
      .then((r) => r.data),
  bukuBesar: (kode_akun: string, period?: LaporanPeriod) =>
    api
      .get<BukuBesarRow[]>(`/laporan/buku-besar/${encodeURIComponent(kode_akun)}/`, {
        params: period,
      })
      .then((r) => r.data),
}
