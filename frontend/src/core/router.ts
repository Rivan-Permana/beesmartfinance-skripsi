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
