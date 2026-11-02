import { describe, expect, it } from "vitest"
import type { InvoiceGabungan } from "@/types/api"
import { invoiceWaText, nomorWa } from "./invoiceGabungan"

const invoice: InvoiceGabungan = {
  sekolah: "RA Uji", tanggal: "2026-11-02", siswa_id: 1, siswa: "Anak Uji", nis: null, kelompok: "A1 (TK)", jenjang: "TK",
  sections: [
    { kategori: "TAHUNAN", label: "Biaya Tahunan", lines: [{ tagihan_id: 1, periode: "Juli 2026", komponen: "KEGIATAN", label: "Uang Kegiatan", nominal: "100000.00" }] },
    { kategori: "BULANAN", label: "Biaya Bulanan", lines: [{ tagihan_id: 2, periode: "Oktober 2026", komponen: "SPP", label: "SPP", nominal: "50000.00" }] },
  ],
  total: "150000.00", perlu_dicocokkan: [],
  rekening: { bank: "Bank Uji", nomor: "000111", atas_nama: "Sekolah Uji" },
  kontak: { nama: "Bu Kontak", wa: "0812000000" }, catatan: "Dapat dicicil.", kontak_ortu: [],
}

describe("invoice gabungan", () => {
  it("menyusun teks WA dengan rincian, total, rekening, dan kontak", () => {
    const text = invoiceWaText(invoice)
    expect(text).toContain("- Uang Kegiatan: Rp 100.000")
    expect(text).toContain("- SPP — Oktober 2026: Rp 50.000")
    expect(text).toContain("*Total: Rp 150.000*")
    expect(text).toContain("Bank Uji 000111 a.n. Sekolah Uji")
    expect(text).toContain("Bu Kontak 0812000000")
  })
  it("tanpa rekening tidak menulis baris transfer", () => {
    expect(invoiceWaText({ ...invoice, rekening: null, kontak: null })).not.toContain("transfer")
  })
  it("mengubah nomor lokal menjadi format wa.me", () => {
    expect(nomorWa("0812-3456-7890")).toBe("6281234567890")
    expect(nomorWa("+62 812 3456 7890")).toBe("6281234567890")
    expect(nomorWa("12345")).toBeNull()
    expect(nomorWa(null)).toBeNull()
  })
})
