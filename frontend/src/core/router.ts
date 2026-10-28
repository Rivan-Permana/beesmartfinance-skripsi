import { createRouter, createWebHistory } from "vue-router"

import { roleHome, ROUTE_TITLES } from "@/core/navigation"
import { useAuthStore } from "@/stores/auth"
import type { Role } from "@/types/api"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/features/auth/LoginView.vue"),
      meta: { public: true },
    },
    {
      path: "/",
      component: () => import("@/shared/layout/AppShell.vue"),
      children: [
        { path: "", redirect: () => roleHome(useAuthStore().roles) },
        {
          path: "dashboard",
          name: "dashboard",
          component: () => import("@/features/dashboard/DashboardView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "jurnal",
          name: "jurnal",
          component: () => import("@/features/jurnal/JurnalListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal", "Administration"] as Role[] },
        },
        {
          path: "tunggakan-tagihan",
          name: "tunggakan-tagihan",
          component: () => import("@/features/tagihan/TunggakanTagihanView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "siswa",
          name: "siswa",
          component: () => import("@/features/siswa/SiswaListView.vue"),
          meta: { roles: ["Administration", "Finance"] as Role[] },
        },
        {
          path: "kelompok",
          name: "kelompok",
          component: () => import("@/features/kelompok/KelompokListView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "absensi-siswa",
          name: "absensi-siswa",
          component: () => import("@/features/absensi/AbsensiSiswaView.vue"),
          meta: { roles: ["Administration", "TeacherInCharge"] as Role[] },
        },
        {
          path: "absensi",
          redirect: { name: "absensi-siswa" },
        },
        {
          path: "rekap-siswa",
          name: "rekap-siswa",
          component: () => import("@/features/absensi/RekapSiswaView.vue"),
          meta: { roles: ["Administration", "TeacherInCharge"] as Role[] },
        },
        {
          path: "katering",
          name: "katering",
          component: () => import("@/features/katering/KateringView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "jemputan",
          name: "jemputan",
          component: () => import("@/features/jemputan/JemputanView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "tagihan",
          name: "tagihan",
          component: () => import("@/features/tagihan/TagihanListView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "pendaftaran",
          name: "pendaftaran",
          component: () => import("@/features/pendaftaran/PendaftaranListView.vue"),
          meta: { roles: ["Administration", "Finance"] as Role[] },
        },
        {
          path: "pegawai",
          name: "pegawai",
          component: () => import("@/features/kepegawaian/PegawaiListView.vue"),
          meta: { roles: ["Administration", "Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "absensi-pegawai",
          name: "absensi-pegawai",
          component: () => import("@/features/kepegawaian/AbsensiPegawaiView.vue"),
          meta: { roles: ["Administration", "Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "gaji",
          name: "gaji",
          component: () => import("@/features/kepegawaian/GajiListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "pinjaman",
          name: "pinjaman",
          component: () => import("@/features/kepegawaian/PinjamanListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "aset",
          name: "aset",
          component: () => import("@/features/aset/AsetListView.vue"),
          meta: { roles: ["Finance"] as Role[] },
        },
        {
          path: "kegiatan",
          name: "kegiatan",
          component: () => import("@/features/kegiatan/KegiatanListView.vue"),
          meta: { roles: ["TeacherInCharge", "SchoolPrincipal", "Finance"] as Role[] },
        },
        {
          path: "anggaran",
          name: "anggaran",
          component: () => import("@/features/anggaran-periode/AnggaranListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "periode",
          name: "periode",
          component: () => import("@/features/anggaran-periode/PeriodeListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "coa",
          name: "coa",
          component: () => import("@/features/coa/CoaListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "laporan",
          name: "laporan",
          component: () => import("@/features/laporan/LaporanView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "audit-log",
          name: "audit-log",
          component: () => import("@/features/audit/AuditLogView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.init()

  if (to.meta.public) return true
  if (!auth.isAuthenticated) {
    return { name: "login", query: { next: to.fullPath } }
  }
  const roles = to.meta.roles as Role[] | undefined
  if (roles && !auth.hasRole(roles)) {
    const name = typeof to.name === "string" ? ROUTE_TITLES[to.name] : undefined
    const label = name ?? to.path
    sessionStorage.setItem(
      "bee-forbidden-flash",
      `Halaman "${label}" hanya untuk role tertentu. Anda dialihkan ke halaman utama.`,
    )
    return roleHome(auth.roles)
  }
  return true
})

export default router
