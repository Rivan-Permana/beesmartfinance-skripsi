import { mount } from "@vue/test-utils"
import PrimeVue from "primevue/config"
import { describe, expect, it } from "vitest"
import type { PembayaranTagihan, Tagihan } from "@/types/api"
import TagihanHistoryDialog from "./TagihanHistoryDialog.vue"
import { bisaBatalSaldoAwal } from "./presentation"

const bayar = (extra: Partial<PembayaranTagihan>): PembayaranTagihan => ({
  id: 1, tanggal: "2026-07-01", no_bukti: "SALDO-AWAL-20261231", nominal: "400000", akun_kas: null, jurnal: null, jurnal_status: null,
  saldo_awal: true, created_by: 1, dibatalkan: false, alasan_batal: "", dibatalkan_pada: null, alokasi: [{ detail: 9, nominal: "400000" }], ...extra,
})
const tagihan = (pembayaran: PembayaranTagihan[]) => ({
  id: 5, siswa: 7, siswa_nama: "Raka", jenis: "BIAYA_MASUK", periode_bulan: 7, periode_tahun: 2026, status: "SEBAGIAN", perlu_rekonsiliasi: false,
  detail: [{ id: 9, komponen: "UANG_MASUK", keterangan: "Uang Masuk", nominal: "1000000", total_terbayar: "400000" }], pembayaran,
}) as unknown as Tagihan
const DialogStub = { template: "<div><slot /><slot name='footer' /></div>" }
const pasang = (target: Tagihan) => mount(TagihanHistoryDialog, { props: { target }, global: { plugins: [[PrimeVue, { unstyled: true }]], stubs: { Dialog: DialogStub } } })

describe("batal saldo awal", () => {
  it("hanya untuk saldo awal yang belum dibatalkan", () => {
    expect(bisaBatalSaldoAwal(bayar({}))).toBe(true)
    expect(bisaBatalSaldoAwal(bayar({ dibatalkan: true }))).toBe(false)
    expect(bisaBatalSaldoAwal(bayar({ saldo_awal: false, jurnal_status: "POSTED" }))).toBe(false)
  })

  it("meminta alasan sebelum mengirim pembatalan", async () => {
    const view = pasang(tagihan([bayar({}), bayar({ id: 2, no_bukti: "KW-02", saldo_awal: false, akun_kas: "112", jurnal: "j", jurnal_status: "POSTED" })]))
    expect(view.findAll('[aria-label^="Batalkan saldo awal"]')).toHaveLength(1)
    await view.get('[aria-label="Batalkan saldo awal SALDO-AWAL-20261231"]').trigger("click")
    const kirim = view.findAll("button").find((b) => b.text() === "Batalkan penerimaan")!
    expect(kirim.attributes("disabled")).toBeDefined()
    await view.get("textarea").setValue("Salah impor baris")
    await view.get("form").trigger("submit")
    expect(view.emitted("cancelOpening")?.[0]?.[1]).toBe("Salah impor baris")
    expect((view.emitted("cancelOpening")?.[0]?.[0] as PembayaranTagihan).id).toBe(1)
    view.unmount()
  })

  it("tidak menawarkan pembatalan untuk saldo awal yang sudah dibatalkan", () => {
    const view = pasang(tagihan([bayar({ dibatalkan: true, alasan_batal: "Salah impor" })]))
    expect(view.find('[aria-label^="Batalkan saldo awal"]').exists()).toBe(false)
    expect(view.text()).toContain("Alasan pembatalan: Salah impor")
    view.unmount()
  })
})
