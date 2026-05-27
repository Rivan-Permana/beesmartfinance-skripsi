import { createRouter, createWebHistory } from "vue-router"

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
        { path: "", redirect: "/siswa" },
        {
          path: "siswa",
          name: "siswa",
          component: () => import("@/features/siswa/SiswaListView.vue"),
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
    return { path: "/" }
  }
  return true
})

export default router
