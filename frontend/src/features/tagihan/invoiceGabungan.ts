import { formatRp } from "@/core/format"
import type { InvoiceGabungan, InvoiceGabunganLine, TagihanKategori } from "@/types/api"

/** Biaya tahunan cukup namanya; biaya bulanan dan lain-lain perlu bulan tagihannya. */
export function invoiceLineLabel(line: InvoiceGabunganLine, kategori: TagihanKategori) {
  return kategori === "TAHUNAN" ? line.label : `${line.label} — ${line.periode}`
}

export function formatTanggalPanjang(iso: string) {
  const date = new Date(iso + "T12:00:00")
  return Number.isFinite(date.getTime()) ? date.toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" }) : iso
}

/** Nomor lokal 08xx menjadi 628xx untuk tautan wa.me; null bila bukan nomor ponsel. */
export function nomorWa(nomor: string | null | undefined) {
  const angka = (nomor ?? "").replace(/\D/g, "")
  const intl = angka.startsWith("0") ? "62" + angka.slice(1) : angka
  return /^628\d{7,11}$/.test(intl) ? intl : null
}

/** Teks pesan WA invoice; dikirim manual oleh Staf TU. */
export function invoiceWaText(invoice: InvoiceGabungan) {
  const out = [
    `Assalamu'alaikum Ayah/Bunda ${invoice.siswa}.`,
    `Berikut rincian tagihan ${invoice.sekolah} per ${formatTanggalPanjang(invoice.tanggal)}:`,
  ]
  for (const section of invoice.sections) {
    out.push("", `*${section.label}*`)
    for (const line of section.lines) out.push(`- ${invoiceLineLabel(line, section.kategori)}: ${formatRp(line.nominal)}`)
  }
  out.push("", `*Total: ${formatRp(invoice.total)}*`)
  if (invoice.catatan) out.push(invoice.catatan)
  if (invoice.rekening) {
    const { bank, nomor, atas_nama } = invoice.rekening
    out.push("", `Pembayaran melalui transfer ke ${[bank, nomor].filter(Boolean).join(" ")}${atas_nama ? ` a.n. ${atas_nama}` : ""}.`)
  }
  if (invoice.kontak) out.push(`Konfirmasi pembayaran: ${[invoice.kontak.nama, invoice.kontak.wa].filter(Boolean).join(" ")}.`)
  out.push("", "Terima kasih.")
  return out.join("\n")
}
