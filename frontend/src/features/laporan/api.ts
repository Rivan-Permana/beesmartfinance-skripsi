import { api } from "@/core/api"
import type {
  BukuBesarRow,
  LabaRugiResult,
  PosisiKeuanganResult,
  RealisasiAnggaranRow,
  SaldoRow,
} from "@/types/api"

export const laporanApi = {
  neracaSaldo: () =>
    api.get<SaldoRow[]>("/laporan/neraca-saldo/").then((r) => r.data),
  labaRugi: () =>
    api.get<LabaRugiResult>("/laporan/laba-rugi/").then((r) => r.data),
  posisiKeuangan: () =>
    api.get<PosisiKeuanganResult>("/laporan/posisi-keuangan/").then((r) => r.data),
  realisasiAnggaran: (tahun?: number) =>
    api
      .get<RealisasiAnggaranRow[]>("/laporan/realisasi-anggaran/", {
        params: tahun ? { tahun } : {},
      })
      .then((r) => r.data),
  bukuBesar: (kode_akun: string) =>
    api
      .get<BukuBesarRow[]>(`/laporan/buku-besar/${encodeURIComponent(kode_akun)}/`)
      .then((r) => r.data),
}
