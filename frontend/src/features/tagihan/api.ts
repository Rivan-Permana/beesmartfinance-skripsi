import { api } from "@/core/api"
import type { Paginated, PembayaranTagihan, StrukTagihan, Tagihan, TagihanPreview } from "@/types/api"

export interface GenerateInput {
  siswa: number
  periode_bulan: number
  periode_tahun: number
  tarif_katering?: number
}

export interface BatchGenerateInput {
  periode_bulan: number
  periode_tahun: number
  tarif_katering?: number
  jenjang?: number | null
  kelompok?: number | null
}

export interface BatchPreviewResult {
  count: number
  previews: TagihanPreview[]
  skipped: { siswa: number; nama: string; reason: string }[]
}

export interface BatchGenerateResult {
  count: number
  created_ids: number[]
  skipped: { siswa: number; nama: string; reason: string }[]
}

export interface TagihanWriteInput {
  siswa: number
  periode_bulan: number
  periode_tahun: number
  detail: {
    komponen: string
    kategori: string
    keterangan: string
    akun_pendapatan: string
    nominal: string | number
  }[]
}

export interface BayarTagihanInput {
  tanggal: string
  no_bukti: string
  nominal: string
  akun_kas: string
  request_id: string
  alokasi: { detail: number; nominal: string }[]
}

export const tagihanApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<Paginated<Tagihan>>("/tagihan/", { params }).then((r) => r.data),
  async listAll(params?: Record<string, unknown>): Promise<Tagihan[]> {
    const out: Tagihan[] = []
    let page = 1
    let hasNext = true
    while (hasNext) {
      const data = await tagihanApi.list({ page_size: 200, ...params, page })
      out.push(...data.results)
      hasNext = !!data.next
      page += 1
    }
    return out
  },
  get: (id: number) =>
    api.get<Tagihan>(`/tagihan/${id}/`).then((r) => r.data),
  create: (payload: TagihanWriteInput) =>
    api.post<Tagihan>("/tagihan/", payload).then((r) => r.data),
  update: (id: number, payload: TagihanWriteInput) =>
    api.put<Tagihan>(`/tagihan/${id}/`, payload).then((r) => r.data),
  preview: (payload: GenerateInput) =>
    api.post<TagihanPreview>("/tagihan/preview/", payload).then((r) => r.data),
  generate: (payload: GenerateInput) =>
    api.post<Tagihan>("/tagihan/generate/", payload).then((r) => r.data),
  previewBatch: (payload: BatchGenerateInput) =>
    api.post<BatchPreviewResult>("/tagihan/preview-batch/", payload).then((r) => r.data),
  generateBatch: (payload: BatchGenerateInput) =>
    api.post<BatchGenerateResult>("/tagihan/generate-batch/", payload).then((r) => r.data),
  remove: (id: number) =>
    api.delete(`/tagihan/${id}/`).then((r) => r.data),
  bayar: (id: number, payload: BayarTagihanInput) =>
    api.post<{ detail: string; tagihan: Tagihan; pembayaran: PembayaranTagihan; jurnal_id: string }>(`/tagihan/${id}/bayar/`, payload).then((r) => r.data),
  struk: (id: number) =>
    api.get<StrukTagihan>(`/tagihan/${id}/struk/`).then((r) => r.data),
}
