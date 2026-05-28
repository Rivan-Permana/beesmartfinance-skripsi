import { AxiosError } from "axios"

export interface FriendlyError {
  summary: string
  detail?: string
}

function extractDetail(data: unknown): string | undefined {
  if (!data) return undefined
  if (typeof data === "string") return data
  if (typeof data === "object") {
    const obj = data as Record<string, unknown>
    if (obj.detail) return String(obj.detail)
    const parts: string[] = []
    for (const [key, val] of Object.entries(obj)) {
      const text = Array.isArray(val) ? val.join(", ") : String(val)
      parts.push(key === "non_field_errors" ? text : `${key}: ${text}`)
    }
    return parts.join(" · ") || undefined
  }
  return undefined
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
  const detail =
    data && typeof data === "object" && "detail" in (data as object)
      ? (data as { detail?: string }).detail
      : undefined
  toast.add({ severity: "success", summary, detail, life: 3500 })
}
