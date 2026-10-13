import { api } from "@/core/api"

async function saveCsvBlob(data: string, filename: string) {
  const blob = new Blob([data], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/** Unduh CSV dari endpoint export legacy (authenticated). */
export const legacyExportApi = {
  async katering(bulan: number, tahun: number, filename: string) {
    const { data } = await api.get<string>("/export/legacy/katering/", {
      params: { bulan, tahun },
      responseType: "text",
      headers: { Accept: "text/csv" },
    })
    saveCsvBlob(data, filename)
  },
  async jemput(bulan: number, tahun: number, filename: string) {
    const { data } = await api.get<string>("/export/legacy/jemput/", {
      params: { bulan, tahun },
      responseType: "text",
      headers: { Accept: "text/csv" },
    })
    saveCsvBlob(data, filename)
  },
}
