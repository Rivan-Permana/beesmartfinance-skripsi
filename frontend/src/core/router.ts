import { createRouter, createWebHistory } from "vue-router"

import { useAuthStore } from "@/stores/auth"
import type { Role } from "@/types/api"

/** Halaman awal sesuai role (hindari loop redirect). */
function roleHome(): string {
  const auth = useAuthStore()
  if (auth.hasRole(["Finance", "SchoolPrincipal"])) return "/dashboard"
  if (auth.hasRole(["Administration"])) return "/siswa"
  return "/jurnal"
}

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
        { path: "", redirect: () => roleHome() },
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
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "siswa",
          name: "siswa",
          component: () => import("@/features/siswa/SiswaListView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "tagihan",
          name: "tagihan",
          component: () => import("@/features/tagihan/TagihanListView.vue"),
          meta: { roles: ["Administration"] as Role[] },
        },
        {
          path: "pegawai",
          name: "pegawai",
          component: () => import("@/features/kepegawaian/PegawaiListView.vue"),
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
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
          meta: { roles: ["Finance", "SchoolPrincipal"] as Role[] },
        },
        {
          path: "kegiatan",
          name: "kegiatan",
          component: () => import("@/features/kegiatan/KegiatanListView.vue"),
          meta: { roles: ["TeacherInCharge", "SchoolPrincipal"] as Role[] },
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
          path: "laporan",
          name: "laporan",
          component: () => import("@/features/laporan/LaporanView.vue"),
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
    return roleHome()
  }
  return true
})

export default router
