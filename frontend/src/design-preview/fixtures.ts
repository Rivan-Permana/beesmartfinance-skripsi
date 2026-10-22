import type { Role } from "@/types/api"
import { navForRoles } from "@/core/navigation"

export const roles: { value: Role; label: string; short: string }[] = [
  { value: "Finance", label: "Staf Keuangan", short: "SK" },
  { value: "SchoolPrincipal", label: "Kepala Sekolah", short: "KS" },
  { value: "Administration", label: "Staf Tata Usaha", short: "TU" },
  { value: "TeacherInCharge", label: "Guru PIC Kegiatan", short: "GP" },
]

export const navigationGroupOrder: Record<Role, string[]> = {
  Finance: ["Ringkasan", "Transaksi", "Perencanaan dan laporan", "Pegawai dan aset", "Pengaturan keuangan"],
  SchoolPrincipal: ["Ringkasan", "Transaksi", "Kegiatan", "Perencanaan dan laporan", "Pengaturan keuangan"],
  Administration: ["Siswa", "Tagihan dan pendaftaran", "Kehadiran dan layanan", "Pegawai"],
  TeacherInCharge: ["Kegiatan", "Kehadiran dan layanan"],
}

// Presentation metadata only; allowed destinations still come from navForRoles.
export const screenInfo: Record<string, { label: string; icon: string; group: string }> = {
  "/dashboard": { label: "Ringkasan", icon: "squares-four", group: "Ringkasan" },
  "/jurnal": { label: "Jurnal", icon: "book-open", group: "Transaksi" },
  "/jurnal?jenis=masuk": { label: "Pemasukan", icon: "arrow-down-left", group: "Transaksi" },
  "/jurnal?jenis=keluar": { label: "Pengeluaran", icon: "arrow-up-right", group: "Transaksi" },
  "/tunggakan-tagihan": { label: "Tunggakan tagihan", icon: "warning-circle", group: "Transaksi" },
  "/coa": { label: "Daftar akun", icon: "book-open", group: "Pengaturan keuangan" },
  "/anggaran": { label: "Anggaran", icon: "chart-pie", group: "Perencanaan dan laporan" },
  "/periode": { label: "Periode akuntansi", icon: "calendar-blank", group: "Pengaturan keuangan" },
  "/laporan": { label: "Laporan keuangan", icon: "file-text", group: "Perencanaan dan laporan" },
  "/audit-log": { label: "Log audit", icon: "clock", group: "Pengaturan keuangan" },
  "/siswa": { label: "Data siswa", icon: "student", group: "Siswa" },
  "/kelompok": { label: "Jenjang dan kelompok", icon: "users", group: "Siswa" },
  "/absensi-siswa": { label: "Absensi siswa", icon: "clipboard-text", group: "Kehadiran dan layanan" },
  "/rekap-siswa": { label: "Rekap absensi siswa", icon: "chart-bar", group: "Kehadiran dan layanan" },
  "/katering": { label: "Katering", icon: "fork-knife", group: "Kehadiran dan layanan" },
  "/jemputan": { label: "Jemputan", icon: "van", group: "Kehadiran dan layanan" },
  "/tagihan": { label: "Tagihan siswa", icon: "file-text", group: "Tagihan dan pendaftaran" },
  "/pendaftaran": { label: "Pendaftaran siswa", icon: "user-plus", group: "Tagihan dan pendaftaran" },
  "/pegawai": { label: "Data pegawai", icon: "identification-card", group: "Pegawai" },
  "/absensi-pegawai": { label: "Absensi pegawai", icon: "clipboard-text", group: "Pegawai" },
  "/gaji": { label: "Penggajian", icon: "money", group: "Pegawai dan aset" },
  "/pinjaman": { label: "Kasbon pegawai", icon: "credit-card", group: "Pegawai dan aset" },
  "/aset": { label: "Aset tetap", icon: "cube", group: "Pegawai dan aset" },
  "/kegiatan": { label: "Kegiatan sekolah", icon: "flag", group: "Kegiatan" },
}

export const months = ["Mei", "Jun", "Jul", "Agu", "Sep", "Okt"]
export const monthly = {
  income: [29_000_000, 35_000_000, 31_000_000, 42_000_000, 38_000_000, 43_800_000],
  expense: [20_000_000, 24_000_000, 22_000_000, 29_000_000, 25_000_000, 28_650_000],
  cashIn: [31_000_000, 34_200_000, 29_000_000, 42_800_000, 38_400_000, 44_100_000],
  cashOut: [24_500_000, 27_000_000, 24_000_000, 31_800_000, 28_000_000, 29_100_000],
}
export const incomeParts = [
  { label: "SPP", value: 35_000_000 },
  { label: "Katering", value: 5_400_000 },
  { label: "Jemputan", value: 1_900_000 },
  { label: "Pendaftaran", value: 1_500_000 },
]
export const expenseParts = [
  { label: "Gaji dan tunjangan", value: 20_000_000 },
  { label: "Operasional sekolah", value: 6_250_000 },
  { label: "Kegiatan", value: 2_400_000 },
]
export const annualBudget = {
  labels: ["Gaji dan tunjangan", "Operasional sekolah", "Kegiatan"],
  pagu: [150_000_000, 90_000_000, 60_000_000],
  realisasi: [100_000_000, 55_000_000, 37_000_000],
}
export const students = [
  { id: "DEMO-001", name: "Siswa Contoh A", group: "TK A / A1", status: "Aktif", spp: 750_000 },
  { id: "DEMO-002", name: "Siswa Contoh B", group: "TK B / B2", status: "Aktif", spp: 750_000 },
  { id: "DEMO-003", name: "Siswa Contoh C", group: "TK A / A2", status: "Aktif", spp: 650_000 },
  { id: "DEMO-004", name: "Siswa Contoh D", group: "Playgroup / PG1", status: "Cuti", spp: 600_000 },
]
export const bills = [
  { name: "Siswa Contoh A", group: "TK A / A1", total: 950_000, paid: 0, remaining: 950_000, status: "Belum bayar", tone: "warning" },
  { name: "Siswa Contoh B", group: "TK B / B2", total: 950_000, paid: 600_000, remaining: 350_000, status: "Sebagian dibayar", tone: "brand" },
  { name: "Siswa Contoh C", group: "TK A / A2", total: 850_000, paid: null, remaining: null, status: "Perlu dicocokkan", tone: "warning" },
]
export const journals = [
  { code: "CONTOH-001", title: "Penerimaan tagihan siswa", date: "15 Okt 2026", amount: 750_000, status: "Draf", kind: "Penerimaan", tone: "success" },
  { code: "CONTOH-002", title: "Belanja perlengkapan kelas", date: "14 Okt 2026", amount: 425_000, status: "Draf", kind: "Pengeluaran", tone: "brand" },
  { code: "CONTOH-003", title: "Penerimaan lain-lain", date: "14 Okt 2026", amount: 100_000, status: "Draf", kind: "Penerimaan", tone: "success" },
]
export const approvals = [
  { code: "CONTOH-004", title: "Realisasi kegiatan kelas", amount: 600_000, status: "Menunggu persetujuan", kind: "Pengeluaran" },
  { code: "CONTOH-005", title: "Penggajian Oktober", amount: 20_000_000, status: "Menunggu persetujuan", kind: "Pengeluaran" },
]
export const activities = [
  { title: "Pekan membaca", pic: "Guru Contoh A", date: "19–23 Okt 2026", pagu: 2_000_000, realisasi: 1_200_000, status: "Berjalan" },
  { title: "Kunjungan edukasi", pic: "Guru Contoh B", date: "26 Okt 2026", pagu: 3_500_000, realisasi: 2_100_000, status: "Berjalan" },
  { title: "Hari kesehatan", pic: "Guru Contoh A", date: "30 Okt 2026", pagu: 1_500_000, realisasi: 300_000, status: "Rencana" },
]

// Self-check: demo breakdowns and navigation must agree with their source data.
console.assert(incomeParts.reduce((s, p) => s + p.value, 0) === monthly.income[5]
  && expenseParts.reduce((s, p) => s + p.value, 0) === monthly.expense[5]
  && roles.every(({ value }) => navForRoles([value]).every((n) => screenInfo[n.query?.jenis ? `${n.to}?jenis=${n.query.jenis}` : n.to])),
"Preview fixture totals or navigation metadata do not match")
