import { defineStore } from "pinia"

import { api, tokenStore } from "@/core/api"
import type { CurrentUser, Role } from "@/types/api"

interface State {
  user: CurrentUser | null
  ready: boolean
}

export const useAuthStore = defineStore("auth", {
  state: (): State => ({ user: null, ready: false }),

  getters: {
    isAuthenticated: (s) => !!s.user,
    roles: (s): Role[] => s.user?.groups ?? [],
    hasRole: (s) => (roles: Role[]) =>
      !!s.user &&
      (s.user.is_superuser || roles.some((r) => s.user!.groups.includes(r))),
  },

  actions: {
    async login(username: string, password: string) {
      const { data } = await api.post("/auth/token/", { username, password })
      tokenStore.set({ access: data.access, refresh: data.refresh })
      await this.fetchMe()
    },

    async fetchMe() {
      const { data } = await api.get<CurrentUser>("/auth/me/")
      this.user = data
    },

    async init() {
      if (tokenStore.access) {
        try {
          await this.fetchMe()
        } catch {
          tokenStore.clear()
        }
      }
      this.ready = true
    },

    logout() {
      tokenStore.clear()
      this.user = null
    },
  },
})
