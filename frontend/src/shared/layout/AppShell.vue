<script setup lang="ts">
import Button from "primevue/button"
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"

import { groupedNav, navForRoles, ROLE_LABEL, ROUTE_TITLES, type NavItem } from "@/core/navigation"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()
const confirm = useConfirm()

const drawerOpen = ref(false)
const collapsed = ref(false)

const navItems = computed(() => navForRoles(auth.roles))
const navGroups = computed(() => groupedNav(navItems.value))

const roleDisplay = computed(() =>
  auth.roles.map((r) => ROLE_LABEL[r] ?? r).join(", ") || "—",
)

const pageTitle = computed(() => {
  const name = route.name
  if (typeof name === "string" && ROUTE_TITLES[name]) return ROUTE_TITLES[name]
  if (route.path.includes("jenis=masuk")) return "Pemasukan"
  if (route.path.includes("jenis=keluar")) return "Pengeluaran"
  return "BeeSmart Finance"
})

const breadcrumb = computed(() => {
  const group = navItems.value.find((n) => isActive(n))?.group
  return group ? `${group.charAt(0)}${group.slice(1).toLowerCase()}` : "App"
})

function isActive(item: NavItem) {
  if (item.to !== route.path) return false
  if (item.query?.jenis) return route.query.jenis === item.query.jenis
  return !route.query.jenis || item.to !== "/jurnal"
}

function navTo(item: NavItem) {
  drawerOpen.value = false
  router.push(item.query ? { path: item.to, query: item.query } : item.to)
}

function logout() {
  confirm.require({
    message: "Keluar dari aplikasi Lebah Madu?",
    header: "Konfirmasi Keluar",
    icon: "pi pi-sign-out",
    rejectLabel: "Batal",
    acceptLabel: "Keluar",
    accept: () => {
      auth.logout()
      router.push({ name: "login" })
    },
  })
}

function toggleDrawer() {
  drawerOpen.value = !drawerOpen.value
}

onMounted(() => {
  const flash = sessionStorage.getItem("bee-forbidden-flash")
  if (flash) {
    sessionStorage.removeItem("bee-forbidden-flash")
    toast.add({ severity: "warn", summary: "Akses ditolak", detail: flash, life: 4000 })
  }
})

watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false
  },
)
</script>

<template>
  <div class="shell" :class="{ collapsed, 'drawer-open': drawerOpen }">
    <div v-if="drawerOpen" class="shell-backdrop" @click="drawerOpen = false" />

    <aside class="shell-sidebar">
      <div class="brand">
        <img src="/logo-lebah.svg" alt="Lebah Madu" class="brand-logo" width="40" height="40" />
        <div v-if="!collapsed" class="brand-text">
          <div class="brand-title">Lebah Madu</div>
          <div class="brand-sub">SIA Sekolah</div>
        </div>
      </div>

      <nav class="menu">
        <div v-for="grp in navGroups" :key="grp.group" class="menu-group">
          <div v-if="!collapsed" class="menu-group-label">{{ grp.label }}</div>
          <button
            v-for="item in grp.items"
            :key="item.label + item.to + (item.query?.jenis ?? '')"
            type="button"
            class="menu-item"
            :class="{ active: isActive(item) }"
            @click="navTo(item)"
          >
            <i :class="item.icon" />
            <span v-if="!collapsed">{{ item.label }}</span>
          </button>
        </div>
      </nav>
    </aside>

    <div class="shell-main">
      <header class="shell-topbar">
        <div class="topbar-left">
          <Button
            class="menu-toggle"
            icon="pi pi-bars"
            severity="secondary"
            text
            rounded
            aria-label="Menu"
            @click="toggleDrawer"
          />
          <Button
            class="collapse-toggle"
            :icon="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"
            severity="secondary"
            text
            rounded
            aria-label="Collapse sidebar"
            @click="collapsed = !collapsed"
          />
          <div class="breadcrumb">
            <span class="crumb-muted">{{ breadcrumb }}</span>
            <span class="crumb-sep">/</span>
            <span class="crumb-current">{{ pageTitle }}</span>
          </div>
        </div>
        <div class="user">
          <div class="user-meta">
            <span class="user-name">{{ auth.user?.nama }}</span>
            <span class="user-role">{{ roleDisplay }}</span>
          </div>
          <Button icon="pi pi-sign-out" severity="secondary" text rounded aria-label="Keluar" @click="logout" />
        </div>
      </header>
      <main class="shell-content">
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
.shell-backdrop {
  display: none;
}
.shell-sidebar {
  width: var(--bee-sidebar-width);
  background: var(--bee-navy);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s ease;
  z-index: 40;
}
.shell.collapsed .shell-sidebar {
  width: var(--bee-sidebar-collapsed);
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1.1rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}
.brand-logo {
  flex-shrink: 0;
  border-radius: 50%;
}
.brand-title {
  font-family: "Baloo 2", sans-serif;
  font-weight: 700;
  line-height: 1.1;
}
.brand-sub {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.6);
}
.menu {
  padding: 0.75rem 0.5rem;
  overflow-y: auto;
  flex: 1;
}
.menu-group-label {
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.45);
  padding: 0.75rem 0.75rem 0.35rem;
  font-weight: 700;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: none;
  border-radius: var(--bee-radius-sm);
  background: transparent;
  color: rgba(255, 255, 255, 0.88);
  font-weight: 600;
  font-family: inherit;
  font-size: 0.9rem;
  cursor: pointer;
  text-align: left;
}
.menu-item i {
  width: 1.25rem;
  text-align: center;
  flex-shrink: 0;
}
.shell.collapsed .menu-item {
  justify-content: center;
  padding: 0.65rem;
  gap: 0;
}
.shell.collapsed .menu-item:hover:not(.active) {
  background: rgba(229, 25, 127, 0.18);
}
.shell.collapsed .menu-item.active {
  margin: 0 0.35rem;
  width: calc(100% - 0.7rem);
}
.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
}
.menu-item.active {
  background: var(--bee-magenta);
  color: #fff;
}
.shell-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.shell-topbar {
  height: 60px;
  background: var(--app-surface);
  border-bottom: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  gap: 0.5rem;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  min-width: 0;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
  margin-left: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.crumb-muted {
  color: var(--app-text-muted);
  text-transform: capitalize;
}
.crumb-sep {
  color: var(--app-text-muted);
}
.crumb-current {
  font-weight: 700;
  color: var(--bee-navy);
}
.user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}
.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.1;
}
.user-name {
  font-weight: 700;
  font-size: 0.9rem;
}
.user-role {
  font-size: 0.72rem;
  color: var(--app-text-muted);
}
.shell-content {
  padding: 1.5rem;
  flex: 1;
  overflow: auto;
}
.menu-toggle {
  display: none;
}
.collapse-toggle {
  display: inline-flex;
}

@media (max-width: 767px) {
  .shell-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }
  .shell.drawer-open .shell-sidebar {
    transform: translateX(0);
  }
  .shell-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 30;
  }
  .menu-toggle {
    display: inline-flex;
  }
  .collapse-toggle {
    display: none;
  }
  .shell.collapsed .shell-sidebar {
    width: var(--bee-sidebar-width);
  }
}

@media (min-width: 768px) and (max-width: 1279px) {
  .collapse-toggle {
    display: inline-flex;
  }
}
</style>
