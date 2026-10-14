import { AxiosError } from "axios"

export interface FriendlyError {
  summary: string
  detail?: string
}

function extractDetail(data: unknown): string | undefined {
  if (!data) return undefined
  if (typeof data === "string") return humanizeTechnicalDetail(data)
  if (Array.isArray(data)) {
    return humanizeTechnicalDetail(data.map((x) => String(x)).join(" · "))
  }
  if (typeof data === "object") {
    const obj = data as Record<string, unknown>
    if (obj.detail) return humanizeTechnicalDetail(String(obj.detail))
    const parts: string[] = []
    for (const [key, val] of Object.entries(obj)) {
      const text = Array.isArray(val) ? val.join(", ") : String(val)
      if (key === "non_field_errors" || /^\d+$/.test(key)) {
        parts.push(humanizeTechnicalDetail(text))
      } else {
        parts.push(`${key}: ${humanizeTechnicalDetail(text)}`)
      }
    }
    return parts.join(" · ") || undefined
  }
  return undefined
}

/** Terjemahkan sisa jargon teknis (PostgreSQL, constraint) ke bahasa ramah. */
export function humanizeTechnicalDetail(raw: string): string {
  const text = raw.trim()
  if (!text) return text
  const lower = text.toLowerCase()
  if (
    lower.includes("mspostingrule")
    || lower.includes("posting rule")
    || lower.includes("belum diset")
  ) {
    return "Akun pendapatan untuk komponen tagihan belum dikonfigurasi. Hubungi Staff Keuangan."
  }
  if (
    lower.includes("belum terdaftar")
    || (lower.includes("is not present") && lower.includes("ms_coa"))
    || (lower.includes("tr_jurnal_detail") && lower.includes("kode_akun") && lower.includes("insert"))
  ) {
    return "Akun COA untuk jurnal belum terdaftar atau belum dikonfigurasi. Hubungi Staff Keuangan untuk mapping akun auto-jurnal."
  }
  if (lower.includes("seed_system_posting_rules")) {
    return "Mapping akun auto-jurnal belum lengkap. Hubungi Staff Keuangan."
  }
  if (lower.includes("tr_jurnal_detail") && lower.includes("kode_akun")) {
    return "Akun ini masih tercatat di jurnal. Nonaktifkan akun, atau periksa jurnal terkait terlebih dahulu."
  }
  if (lower.includes("ms_coa_sub_golongan") || (lower.includes("ms_sub_golongan") && lower.includes("ms_coa"))) {
    return "Sub-golongan masih punya akun di dalamnya. Pindahkan atau hapus akun tersebut dulu."
  }
  if (lower.includes("foreign key") || (lower.includes("violates") && lower.includes("constraint"))) {
    return "Data ini masih dipakai di bagian lain. Periksa kembali sebelum menghapus atau mengubah."
  }
  if (lower.includes("invalid page")) {
    return "Halaman tidak ditemukan. Kembali ke halaman pertama."
  }
  if (lower.includes("duplicate key") || lower.includes("already exists")) {
    return "Kode atau data sudah ada. Gunakan kode lain."
  }
  if (text.length > 180 || lower.includes("pg_") || lower.includes("_fkey")) {
    return "Operasi tidak dapat dilanjutkan. Data mungkin masih dipakai di modul lain."
  }
  return text
}

/**
 * Terjemahkan error (terutama dari Axios/DRF) ke pesan ramah berbahasa
 * Indonesia yang pas untuk pegawai sekolah — bukan jargon teknis.
 */
export function friendlyError(
  e: unknown,
  fallback = "Maaf, terjadi kendala.",
): FriendlyError {
  const err = e as AxiosError<unknown>
  if (err?.isAxiosError) {
    if (!err.response) {
      return {
        summary: "Koneksi terputus",
        detail:
          "Aplikasi tidak dapat terhubung ke server. Coba periksa koneksi internet, atau hubungi admin sekolah.",
      }
    }
    const status = err.response.status
    const detail = extractDetail(err.response.data)
    switch (status) {
      case 400:
        return {
          summary: "Data belum sesuai",
          detail: detail || "Mohon periksa kembali isian pada formulir.",
        }
      case 401:
        return {
          summary: "Sesi Anda berakhir",
          detail: "Demi keamanan, silakan masuk kembali.",
        }
      case 403:
        return {
          summary: "Tidak diizinkan",
          detail:
            "Akun Anda tidak memiliki hak untuk tindakan ini. Hubungi Kepala Sekolah / admin bila perlu akses.",
        }
      case 404:
        return {
          summary: "Data tidak ditemukan",
          detail: detail || "Data yang Anda cari mungkin sudah dihapus atau dipindahkan.",
        }
      case 409:
        return { summary: "Data bertabrakan", detail }
      case 429:
        return {
          summary: "Terlalu sering mencoba",
          detail: "Mohon tunggu sebentar, lalu coba lagi.",
        }
      default:
        if (status >= 500) {
          return {
            summary: "Server sedang bermasalah",
            detail: "Coba beberapa saat lagi. Jika berlanjut, hubungi admin sekolah.",
          }
        }
        return { summary: fallback, detail }
    }
  }
  if (e instanceof Error) return { summary: fallback, detail: e.message }
  return { summary: fallback }
}

/** Ambil baris detail toast sukses — hanya string, bukan objek/array API. */
function extractSuccessDetail(data: unknown): string | undefined {
  if (!data || typeof data !== "object") return undefined
  const detail = (data as { detail?: unknown }).detail
  return typeof detail === "string" && detail.trim() ? detail : undefined
}

/** Pesan sukses ramah untuk aksi jurnal (response body = objek jurnal). */
export function jurnalActionSuccessMessage(
  action: "submit" | "approve" | "void" | "catat",
  data: unknown,
): { summary: string; detail?: string } {
  const j = data as { no_bukti?: string; keterangan?: string; status?: string }
  const bukti = j.no_bukti ? `No. bukti ${j.no_bukti}` : "Jurnal"
  switch (action) {
    case "catat":
      return { summary: "Jurnal dicatat", detail: `${bukti} sudah masuk buku besar.` }
    case "submit":
      if (j.status === "POSTED") {
        return { summary: "Jurnal dicatat", detail: `${bukti} sudah masuk buku besar.` }
      }
      return {
        summary: "Jurnal diajukan",
        detail: `${bukti} menunggu persetujuan Kepala Sekolah.`,
      }
    case "approve":
      return {
        summary: "Jurnal disetujui",
        detail: `${bukti} sudah masuk buku besar (POSTED).`,
      }
    case "void":
      return {
        summary: "Jurnal dibatalkan",
        detail: extractSuccessDetail(data) ?? `${bukti} dibalik via jurnal pembalik.`,
      }
  }
}

interface ToastLike {
  add: (m: {
    severity: string
    summary: string
    detail?: string
    life?: number
  }) => void
}

/** Tampilkan error sebagai toast ramah. */
export function notifyError(toast: ToastLike, e: unknown, fallback?: string) {
  const f = friendlyError(e, fallback)
  toast.add({ severity: "error", summary: f.summary, detail: f.detail, life: 5000 })
}

/**
 * Tampilkan toast sukses ramah. `data` boleh berisi `{ detail }` dari backend
 * (lihat exception handler & action endpoint) untuk dijadikan baris kedua.
 */
export function notifySuccess(
  toast: ToastLike,
  summary: string,
  data?: { detail?: string } | unknown,
) {
  const detail = extractSuccessDetail(data)
  toast.add({ severity: "success", summary, detail, life: 3500 })
}
