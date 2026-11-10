import { describe, expect, it } from "vitest"
import { paymentState } from "@/features/tagihan/presentation"
import type { ImporBiayaMasukBaris } from "@/types/api"
import { BIAYA_MASUK_PREFILL, biayaMasukBruto, imporBiayaMasukDetail, tanggalSaldoAwalDefault } from "./presentation"

const row = (extra: Partial<ImporBiayaMasukBaris>): ImporBiayaMasukBaris => ({
  baris: 4, nama: "Anak", kelas: "TK A", aksi: "isi", siswa: 1, kategori: "", diskon: 0,
  komponen: { uang_masuk: 1000, uang_portofolio: null, uang_kegiatan: null, uang_pengembangan: null, uang_komite: 500, uang_seragam: null },
  ditagih: 1500, terbayar: 1000, alasan: null, ...extra,
})

describe("cut-over biaya masuk", () => {
  it("default tanggal saldo awal adalah akhir bulan lalu", () => {
    expect(tanggalSaldoAwalDefault(new Date(2027, 0, 1)).toDateString()).toBe(new Date(2026, 11, 31).toDateString())
  })
  it("komite dan portofolio tidak diisi dari daftar harga tetapi ikut total", () => {
    expect(BIAYA_MASUK_PREFILL.map((f) => f.field)).not.toContain("uang_komite")
    expect(biayaMasukBruto({ uang_masuk: "1000", uang_komite: "500", uang_portofolio: "250" })).toBe(1750)
  })
  it("rincian baris pratinjau menyebut tagihan, terbayar, sisa, dan diskon", () => {
    const text = imporBiayaMasukDetail(row({ kategori: "SIB", diskon: 200 }))
    expect(text).toContain("sisa")
    expect(text).toContain("diskon SIB")
    expect(imporBiayaMasukDetail(row({ aksi: "galat", alasan: "Siswa tidak ditemukan" }))).toBe("Siswa tidak ditemukan")
    expect(imporBiayaMasukDetail(row({ aksi: "cek", alasan: "Total cicilan melebihi" }))).toMatch(/^Total cicilan melebihi Ditagihkan/)
  })
  it("riwayat pembayaran membedakan saldo awal", () => {
    expect(paymentState({ dibatalkan: false, jurnal_status: null, saldo_awal: true }).label).toBe("Saldo awal dari spreadsheet")
    expect(paymentState({ dibatalkan: true, jurnal_status: null, saldo_awal: true }).label).toBe("Dibatalkan")
    expect(paymentState({ dibatalkan: false, jurnal_status: "POSTED", saldo_awal: false }).label).toBe("Sudah dicatat")
  })
})
