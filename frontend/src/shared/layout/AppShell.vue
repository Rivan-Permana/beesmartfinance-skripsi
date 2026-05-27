<script setup lang="ts">
import Button from "primevue/button"
import { computed } from "vue"
import { useRouter } from "vue-router"

import { useAuthStore } from "@/stores/auth"
import type { Role } from "@/types/api"

const auth = useAuthStore()
const router = useRouter()

interface NavItem {
  label: string
  icon: string
  to: string
  roles: Role[]
}

const allNav: NavItem[] = [
  { label: "Siswa", icon: "pi pi-users", to: "/siswa", roles: ["Administration"] },
]

const nav = computed(() => allNav.filter((i) => auth.hasRole(i.roles)))

function logout() {
  auth.logout()
  router.push({ name: "login" })
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-badge">🐝</span>
        <div>
          <div class="brand-title">Lebah Madu</div>
          <div class="brand-sub">SIA Sekolah</div>
        </div>
      </div>
      <nav class="menu">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="menu-item"
          active-class="active"
        >
          <i :class="item.icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="spacer" />
        <div class="user">
          <div class="user-meta">
            <span class="user-name">{{ auth.user?.nama }}</span>
            <span class="user-role">{{ auth.roles.join(", ") || "—" }}</span>
          </div>
          <Button
            icon="pi pi-sign-out"
            severity="secondary"
            text
            rounded
            aria-label="Keluar"
            @click="logout"
          />
        </div>
      </header>
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 250px;
  background: var(--bee-navy);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1.1rem 1.2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}
.brand-badge {
  font-size: 1.6rem;
  background: var(--bee-orange);
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 50%;
}
.brand-title {
  font-family: "Baloo 2", sans-serif;
  font-weight: 700;
  color: #fff;
  line-height: 1.1;
}
.brand-sub {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.6);
}
.menu {
  padding: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.9rem;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
}
.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
}
.menu-item.active {
  background: var(--bee-magenta);
  color: #fff;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.topbar {
  height: 60px;
  background: var(--app-surface);
  border-bottom: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
}
.spacer {
  flex: 1;
}
.user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.1;
}
.user-name {
  font-weight: 700;
}
.user-role {
  font-size: 0.72rem;
  color: var(--app-text-muted);
}
.content {
  padding: 1.5rem;
  flex: 1;
  overflow: auto;
}
</style>
