import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import { navForRoles, roleHome } from "@/core/navigation"
import { pemakaianBulan, statusRealisasi } from "@/features/anggaran-periode/presentation"
import AccountReportTable from "@/features/laporan/AccountReportTable.vue"
import type { PaketLSU, SaldoRow } from "@/types/api"
import { paketState, siswaPunyaPaketBerjalan, sisaSesi, urutkanPaket } from "./presentation"

const paket = (extra: Partial<PaketLSU>): PaketLSU => ({
  id: 1, siswa: 7, siswa_nama: "Raka", jumlah_sesi: 8, harga: "1200000.00", tanggal_mulai: "2027-01-04", keterangan: "",
  sesi_terpakai: 0, tagihan: 3, tagihan_status: "BELUM", tagihan_sisa: "1200000.00", pertemuan: [], ...extra,
})

describe("LSU", () => {
  it("menghitung sisa sesi dan mendahulukan paket berjalan", () => {
    expect(sisaSesi(paket({ sesi_terpakai: 3 }))).toBe(5)
    expect(paketState(paket({ sesi_terpakai: 8 })).label).toBe("Sesi habis")
    const rows = urutkanPaket([paket({ id: 1, sesi_terpakai: 8, tanggal_mulai: "2027-02-01" }), paket({ id: 2, tanggal_mulai: "2027-01-01" })])
    expect(rows.map((r) => r.id)).toEqual([2, 1])
    expect(siswaPunyaPaketBerjalan(rows, 7)).toBe(true)
    expect(siswaPunyaPaketBerjalan([paket({ sesi_terpakai: 8 })], 7)).toBe(false)
  })
})

describe("penyusun anggaran", () => {
  it("hanya melihat menu anggaran bulanan", () => {
    expect(roleHome(["BudgetPlanner"])).toBe("/anggaran")
    expect(navForRoles(["BudgetPlanner"]).map((item) => item.to)).toEqual(["/anggaran"])
    expect(navForRoles(["Administration"]).some((item) => item.to === "/lsu")).toBe(true)
  })
  it("menilai realisasi terhadap anggaran bulan itu", () => {
    const akun = { kode_akun: "5101", nama_akun: "Outing", plafon: "1000", total_anggaran: "300", total_realisasi: "350", sisa_plafon: "650",
      bulan: [{ tahun: 2026, bulan: 7, anggaran: "300", realisasi: "250" }, { tahun: 2026, bulan: 8, anggaran: null, realisasi: "100" }] }
    expect(pemakaianBulan(akun, 0)).toEqual({ anggaranBulan: 300, realisasiBulan: 250 })
    expect(statusRealisasi(300, 350)).toBe("lebih")
    expect(statusRealisasi(null, 100)).toBe("tanpa")
  })
})

describe("laba rugi per kelompok", () => {
  it("menampilkan judul kelompok dan subtotal", () => {
    const row = (kode: string, kelompok: string, saldo: string): SaldoRow => ({ kode_akun: kode, nama_akun: `Akun ${kode}`, posisi_normal: "D", total_debit: saldo, total_kredit: "0", saldo_akhir: saldo, kelompok_kode: kelompok, kelompok_nama: `Kelompok ${kelompok}` })
    const wrapper = mount(AccountReportTable, { props: { caption: "Beban", rows: [row("5101", "51", "100"), row("5401", "54", "25")], groups: [{ kode: "51", nama: "Kelompok 51", total: "100" }, { kode: "54", nama: "Kelompok 54", total: "25" }], totalLabel: "Total", total: "125" } })
    expect(wrapper.findAll(".report-group-row").map((r) => r.text())).toEqual(["Kelompok 51", "Kelompok 54"])
    expect(wrapper.findAll(".report-subtotal-row")).toHaveLength(2)
    expect(wrapper.find(".report-subtotal-row").text()).toContain("Subtotal kelompok 51")
  })
})
