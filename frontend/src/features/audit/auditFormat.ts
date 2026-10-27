/** Pemetaan label & format nilai audit log — bahasa Indonesia. */

export type UserLabelMap = Record<string, { username: string; nama: string }>

export const AUDIT_TABLE_LABEL: Record<string, string> = {
  ms_coa: "Daftar akun (COA)",
  tr_jurnal: "Jurnal",
  tr_jurnal_detail: "Baris jurnal",
  tr_anggaran: "Anggaran",
  ms_golongan: "Golongan akun",
  ms_sub_golongan: "Sub-golongan akun",
}

export const AUDIT_TABLE_SHORT: Record<string, string> = {
  ms_coa: "COA",
  tr_jurnal: "Jurnal",
  tr_jurnal_detail: "Baris jurnal",
  tr_anggaran: "Anggaran",
  ms_golongan: "Golongan",
  ms_sub_golongan: "Sub-golongan",
}

export const AUDIT_ACTION_LABEL: Record<string, string> = {
  INSERT: "Tambah data",
  UPDATE: "Ubah data",
  DELETE: "Hapus data",
}

export const AUDIT_FIELD_LABEL: Record<string, string> = {
  status: "Status",
  keterangan: "Keterangan",
  tanggal: "Tanggal",
  no_bukti: "No. bukti",
  tipe_sumber: "Sumber transaksi",
  posted_at: "Waktu posting",
  approved_at: "Waktu disetujui",
  submitted_at: "Waktu pengajuan",
  kode_akun: "Kode akun",
  nama_akun: "Nama akun",
  kode_golongan: "Kode golongan",
  nama_golongan: "Nama golongan",
  kode_sub: "Kode subgolongan",
  nama_sub: "Nama subgolongan",
  sub_golongan_id: "Subgolongan",
  golongan_id: "Golongan",
  posisi_normal: "Posisi normal",
  is_active: "Akun aktif",
  saldo_awal: "Saldo awal",
  tanggal_saldo_awal: "Tanggal saldo awal",
  debit: "Debit",
  kredit: "Kredit",
  pagu: "Pagu anggaran",
  realisasi: "Realisasi",
  tahun: "Tahun",
  bulan: "Bulan",
  nominal: "Nominal",
  nominal_anggaran: "Pagu",
  tahun_anggaran: "Tahun anggaran",
  carry_over: "Carry-over ditandai",
  periode_id: "Periode",
  is_deleted: "Dihapus (soft delete)",
  created_by_id: "Dibuat oleh",
  approved_by_id: "Disetujui oleh",
  submitted_by_id: "Diajukan oleh",
  jurnal: "ID jurnal",
  jurnal_id: "ID jurnal",
  siswa: "ID siswa",
  pegawai: "ID pegawai",
  periode_bulan: "Bulan periode",
  periode_tahun: "Tahun periode",
  total: "Total",
}

const USER_ID_FIELDS = new Set([
  "created_by_id",
  "approved_by_id",
  "submitted_by_id",
])

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Draf",
  PENDING: "Menunggu persetujuan",
  POSTED: "Sudah diposting",
  VOID: "Dibatalkan",
  LUNAS: "Lunas",
  BELUM: "Belum lunas",
  SEBAGIAN: "Bayar sebagian",
  AKTIF: "Aktif",
  RENCANA: "Rencana",
  BERJALAN: "Berjalan",
  SELESAI: "Selesai",
}

const SUMBER_LABEL: Record<string, string> = {
  MANUAL: "Input manual",
  AUTO_PENDAFTARAN: "Otomatis — pendaftaran siswa",
  AUTO_TAGIHAN: "Otomatis — tagihan",
  AUTO_GAJI: "Otomatis — gaji",
  AUTO_PINJAMAN: "Otomatis — kasbon pegawai",
  AUTO_ASET: "Otomatis — aset tetap",
  AUTO_KEGIATAN: "Otomatis — kegiatan",
}

const HIDDEN_AUDIT_FIELDS = new Set([
  "id",
  "created_at",
  "updated_at",
  "created_by",
  "modified_by",
])

const ISO_DATETIME = /^\d{4}-\d{2}-\d{2}T/
const MONEY_FIELDS = new Set(["saldo_awal", "nominal_anggaran", "debit", "kredit", "pagu", "realisasi", "nominal"])

export function auditFieldLabel(key: string) {
  return AUDIT_FIELD_LABEL[key] ?? key.replaceAll("_", " ")
}

export function formatAuditUserId(
  value: unknown,
  users: UserLabelMap,
): string {
  if (value == null || value === "") return "—"
  const id = String(value)
  const u = users[id]
  if (u) return `${u.nama} (@${u.username})`
  return `Pengguna ID ${id} (nama tidak tersedia)`
}

export function formatAuditValue(
  key: string,
  value: unknown,
  users: UserLabelMap,
): string {
  if (value == null || value === "") return "—"
  if (USER_ID_FIELDS.has(key)) return formatAuditUserId(value, users)
  if (key === "status" && typeof value === "string") {
    return STATUS_LABEL[value] ?? value
  }
  if (key === "tipe_sumber" && typeof value === "string") {
    return SUMBER_LABEL[value] ?? value.replaceAll("_", " ").toLowerCase()
  }
  if (key === "posisi_normal") {
    if (value === "D") return "Debit"
    if (value === "K") return "Kredit"
  }
  if (MONEY_FIELDS.has(key) && (typeof value === "string" || typeof value === "number")) {
    const match = /^(-?\d+)(?:\.(\d{1,2}))?$/.exec(String(value))
    if (match) return `Rp ${match[1]!.startsWith("-") ? "−" : ""}${BigInt(match[1]!.replace("-", "")).toLocaleString("id-ID")},${(match[2] ?? "").padEnd(2, "0")}`
  }
  if (typeof value === "boolean") return value ? "Ya" : "Tidak"
  if (typeof value === "string" && ISO_DATETIME.test(value)) {
    return new Date(value).toLocaleString("id-ID", {
      dateStyle: "medium",
      timeStyle: "short",
    })
  }
  if (typeof value === "object") {
    try { return JSON.stringify(value) } catch { return String(value) }
  }
  return String(value)
}

export interface AuditDiffRow {
  key: string
  label: string
  old: string
  new: string
  changed: boolean
}

export function buildAuditDiffRows(
  oldData: unknown,
  newData: unknown,
  users: UserLabelMap,
  onlyChanged = true,
): AuditDiffRow[] {
  const oldObj = (oldData && typeof oldData === "object")
    ? oldData as Record<string, unknown>
    : {}
  const newObj = (newData && typeof newData === "object")
    ? newData as Record<string, unknown>
    : {}
  const keys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)])
  const rows = [...keys]
    .filter((k) => !HIDDEN_AUDIT_FIELDS.has(k))
    .map((key) => {
      const oldVal = oldObj[key]
      const newVal = newObj[key]
      const changed = JSON.stringify(oldVal) !== JSON.stringify(newVal)
      return {
        key,
        label: auditFieldLabel(key),
        old: formatAuditValue(key, oldVal, users),
        new: formatAuditValue(key, newVal, users),
        changed,
      }
    })
    .filter((row) => row.old !== "—" || row.new !== "—")
  return onlyChanged ? rows.filter((r) => r.changed) : rows
}

export function formatRecordId(pk: string | null | undefined) {
  if (!pk) return { short: "—", full: "", hint: "ID tidak tercatat" }
  const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(pk)
  if (isUuid) {
    return {
      short: `#${pk.slice(0, 8)}…`,
      full: pk,
      hint: "Identitas unik record di database (UUID)",
    }
  }
  return {
    short: `#${pk}`,
    full: pk,
    hint: "Nomor urut record",
  }
}
