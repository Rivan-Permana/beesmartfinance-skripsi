import type { Role } from "@/types/api"

export type NavGroup = "SISWA" | "KEUANGAN" | "PEGAWAI" | "KEGIATAN"

export interface NavItem {
  label: string
  icon: string
  to: string
  roles: Role[]
  group: NavGroup
  /** Query untuk alias jurnal Pemasukan/Pengeluaran */
  query?: Record<string, string>
}

export const ROLE_LABEL: Record<Role, string> = {
  Finance: "Staf Keuangan",
  SchoolPrincipal: "Kepala Sekolah",
  Administration: "Staf TU",
  TeacherInCharge: "Guru PIC Kegiatan",
}

export const NAV_GROUP_LABELS: Record<NavGroup, string> = {
  SISWA: "Siswa",
  KEUANGAN: "Keuangan",
  PEGAWAI: "Pegawai",
  KEGIATAN: "Kegiatan",
}

export const ALL_NAV: NavItem[] = [
  { label: "Beranda", icon: "pi pi-th-large", to: "/dashboard", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Pemasukan", icon: "pi pi-arrow-down-left", to: "/jurnal", query: { jenis: "masuk" }, roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Pengeluaran", icon: "pi pi-arrow-up-right", to: "/jurnal", query: { jenis: "keluar" }, roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Tunggakan Tagihan", icon: "pi pi-exclamation-circle", to: "/tunggakan-tagihan", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Daftar Akun", icon: "pi pi-sitemap", to: "/coa", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Anggaran", icon: "pi pi-chart-pie", to: "/anggaran", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Aset", icon: "pi pi-box", to: "/aset", roles: ["Finance"], group: "KEUANGAN" },
  { label: "Periode", icon: "pi pi-calendar", to: "/periode", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Laporan", icon: "pi pi-file", to: "/laporan", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Log Audit", icon: "pi pi-history", to: "/audit-log", roles: ["Finance", "SchoolPrincipal"], group: "KEUANGAN" },
  { label: "Data siswa", icon: "pi pi-users", to: "/siswa", roles: ["Administration"], group: "SISWA" },
  { label: "Kelompok", icon: "pi pi-th-large", to: "/kelompok", roles: ["Administration"], group: "SISWA" },
  { label: "Absensi Siswa", icon: "pi pi-calendar-plus", to: "/absensi-siswa", roles: ["Administration"], group: "SISWA" },
  { label: "Rekap Absensi", icon: "pi pi-chart-bar", to: "/rekap-siswa", roles: ["Administration", "TeacherInCharge"], group: "SISWA" },
  { label: "Katering", icon: "pi pi-apple", to: "/katering", roles: ["Administration"], group: "SISWA" },
  { label: "Jemputan", icon: "pi pi-car", to: "/jemputan", roles: ["Administration"], group: "SISWA" },
  { label: "Tagihan", icon: "pi pi-receipt", to: "/tagihan", roles: ["Administration"], group: "SISWA" },
  { label: "Pendaftaran", icon: "pi pi-user-plus", to: "/pendaftaran", roles: ["Administration"], group: "SISWA" },
  { label: "Pegawai", icon: "pi pi-id-card", to: "/pegawai", roles: ["Administration"], group: "PEGAWAI" },
  { label: "Absensi Pegawai", icon: "pi pi-calendar-plus", to: "/absensi-pegawai", roles: ["Administration"], group: "PEGAWAI" },
  { label: "Gaji", icon: "pi pi-money-bill", to: "/gaji", roles: ["Finance"], group: "PEGAWAI" },
  { label: "Kasbon", icon: "pi pi-credit-card", to: "/pinjaman", roles: ["Finance"], group: "PEGAWAI" },
  { label: "Kegiatan", icon: "pi pi-flag", to: "/kegiatan", roles: ["TeacherInCharge", "SchoolPrincipal"], group: "KEGIATAN" },
]

export const ROUTE_TITLES: Record<string, string> = {
  dashboard: "Beranda",
  jurnal: "Jurnal",
  siswa: "Data siswa",
  kelompok: "Pengelolaan Kelompok",
  "absensi-siswa": "Absensi Siswa",
  "rekap-siswa": "Rekap Absensi",
  katering: "Katering",
  jemputan: "Jemputan",
  tagihan: "Tagihan siswa",
  pendaftaran: "Pendaftaran Siswa",
  pegawai: "Data Pegawai",
  gaji: "Penggajian",
  pinjaman: "Kasbon Pegawai",
  aset: "Aset tetap",
  kegiatan: "Kegiatan sekolah",
  anggaran: "Anggaran",
  periode: "Periode Akuntansi",
  laporan: "Laporan Keuangan",
  "audit-log": "Log Audit",
  coa: "Daftar Akun",
  "tunggakan-tagihan": "Tunggakan Tagihan",
  "absensi-pegawai": "Absensi Pegawai",
}

export function roleHome(roles: Role[]): string {
  if (roles.includes("Finance") || roles.includes("SchoolPrincipal")) return "/dashboard"
  if (roles.includes("Administration")) return "/siswa"
  if (roles.includes("TeacherInCharge")) return "/kegiatan"
  return "/login"
}

export function navForRoles(roles: Role[]): NavItem[] {
  return ALL_NAV.filter((item) => item.roles.some((r) => roles.includes(r)))
}

export function groupedNav(items: NavItem[]): { group: NavGroup; label: string; items: NavItem[] }[] {
  const order: NavGroup[] = ["SISWA", "KEUANGAN", "PEGAWAI", "KEGIATAN"]
  const map = new Map<NavGroup, NavItem[]>()
  for (const item of items) {
    if (!map.has(item.group)) map.set(item.group, [])
    map.get(item.group)!.push(item)
  }
  return order
    .filter((g) => map.has(g))
    .map((g) => ({ group: g, label: NAV_GROUP_LABELS[g], items: map.get(g)! }))
}
