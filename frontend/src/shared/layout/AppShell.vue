<script setup lang="ts">
import Button from "primevue/button"
import Drawer from "primevue/drawer"
import AppNavigation from "./AppNavigation.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"

import { navForRoles, navItemActive, ROLE_LABEL, ROUTE_TITLES, type NavItem } from "@/core/navigation"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()
const confirm = useConfirm()

const drawerOpen = ref(false)
const menuButton = ref<{ $el: HTMLButtonElement } | null>(null)
function restoreMenuFocus() { if (!desktop?.matches) menuButton.value?.$el.focus() }
const collapsed = ref(false)
let desktop: MediaQueryList | undefined
function closeMobileOnDesktop() { if (desktop?.matches) drawerOpen.value = false }
onMounted(() => { desktop = window.matchMedia("(min-width: 768px)"); desktop.addEventListener("change", closeMobileOnDesktop) })
onUnmounted(() => desktop?.removeEventListener("change", closeMobileOnDesktop))

const navItems = computed(() => navForRoles(auth.roles))

const roleDisplay = computed(() =>
  auth.roles.map((r) => ROLE_LABEL[r] ?? r).join(", ") || "—",
)

const pageTitle = computed(() => {
  if (route.path === "/jurnal" && route.query.jenis === "masuk") return "Pemasukan"
  if (route.path === "/jurnal" && route.query.jenis === "keluar") return "Pengeluaran"
  const name = route.name
  if (typeof name === "string" && ROUTE_TITLES[name]) return ROUTE_TITLES[name]
  return "BeeSmart Finance"
})

const breadcrumb = computed(() => {
  const group = navItems.value.find((n) => isActive(n))?.group
  return group ? `${group.charAt(0)}${group.slice(1).toLowerCase()}` : "App"
})

function isActive(item: NavItem) {
  return navItemActive(item, route.path, route.query.jenis)
}


function logout() {
  confirm.require({
    message: "Keluar dari aplikasi Lebah Madu?",
    header: "Keluar dari aplikasi?",
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


    <aside class="shell-sidebar">
      <div class="brand">
        <img src="/logo-lebah.svg" alt="Lebah Madu" class="brand-logo" width="40" height="40" />
        <div v-if="!collapsed" class="brand-text">
          <div class="brand-title">Lebah Madu</div>
          <div class="brand-sub">SIA Sekolah</div>
        </div>
      </div>

      <AppNavigation :collapsed="collapsed" />
    </aside>
    <Drawer id="app-mobile-navigation" v-model:visible="drawerOpen" @after-hide="restoreMenuFocus" header="Lebah Madu" :close-button-props="{ 'aria-label': 'Tutup menu navigasi' }" :pt="{ root: { class: 'shell-mobile-drawer' } }">
      <template #closeicon><Icon name="x" /></template>
      <!-- The topbar hides the account on phones, so the drawer says who is signed in. -->
      <div class="drawer-user"><span class="user-name">{{ auth.user?.nama }}</span><span class="user-role">{{ roleDisplay }}</span></div>
      <AppNavigation @navigate="drawerOpen = false" />
    </Drawer>

    <div class="shell-main">
      <header class="shell-topbar">
        <div class="topbar-left">
          <Button
            ref="menuButton"
            class="menu-toggle"
            severity="secondary"
            text
            rounded
            aria-label="Menu"
            :aria-expanded="drawerOpen"
            aria-controls="app-mobile-navigation"
            @click="toggleDrawer"
          ><template #icon><Icon name="list" /></template></Button>
          <Button
            class="collapse-toggle"
            severity="secondary"
            text
            rounded
            :aria-label="collapsed ? 'Perluas navigasi' : 'Ringkas navigasi'"
            :aria-expanded="!collapsed"
            @click="collapsed = !collapsed"
          ><template #icon><Icon :name="collapsed ? 'caret-right' : 'caret-left'" /></template></Button>
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
          <Button severity="secondary" text aria-label="Keluar" @click="logout"><template #icon><Icon name="sign-out" /></template></Button>
        </div>
      </header>
      <main class="shell-content">
        <RouterView v-slot="{ Component }">
          <Transition name="bee-route" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell { display: flex; min-height: 100vh; }
.shell-sidebar { width: var(--bee-sidebar-width); background: var(--bee-color-nav); color: var(--bee-color-nav-text); display: flex; flex-direction: column; flex-shrink: 0; }
.shell.collapsed .shell-sidebar { width: var(--bee-sidebar-collapsed); }
.brand { display: flex; align-items: center; gap: var(--bee-space-3); padding: var(--bee-space-5) var(--bee-space-4); border-bottom: 1px solid var(--bee-color-nav-border); }
.brand-logo { flex-shrink: 0; }.brand-title { font-weight: 600; font-size: var(--bee-type-body); }.brand-sub { font-size: var(--bee-type-caption); color: var(--bee-color-nav-muted); }
.shell-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.shell-topbar { min-height: 72px; background: var(--app-surface); border-bottom: 1px solid var(--app-border); display: flex; align-items: center; justify-content: space-between; padding: var(--bee-space-3) var(--bee-space-5); gap: var(--bee-space-4); }
.topbar-left { display: flex; align-items: center; gap: var(--bee-space-2); min-width: 0; }.breadcrumb { display: flex; flex-wrap: wrap; align-items: center; gap: var(--bee-space-2); font-size: var(--bee-type-ui); }.crumb-muted,.crumb-sep { color: var(--app-text-muted); }.crumb-current { font-weight: 500; }
.user { display: flex; align-items: center; gap: var(--bee-space-3); flex-shrink: 0; }.user-meta { display: flex; flex-direction: column; align-items: flex-end; }.user-name { font-weight: 500; }.user-role { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
.shell-content { padding: var(--bee-layout-page-gutter); flex: 1; min-width: 0; }.menu-toggle { display: none; }.collapse-toggle { display: inline-flex; }
@media(max-width:767px) { .shell-sidebar { display: none; }.menu-toggle { display: inline-flex; }.collapse-toggle { display: none; }.shell-content { padding: var(--bee-layout-page-gutter-mobile); }.shell-topbar { padding-inline: var(--bee-space-4); }.user-meta { display: none; }.crumb-muted,.crumb-sep { display: none; } }
</style>
<style>
.p-drawer.shell-mobile-drawer { width: min(320px, 100vw); --p-drawer-background: var(--bee-color-nav); --p-drawer-color: var(--bee-color-nav-text); background: var(--bee-color-nav); color: var(--bee-color-nav-text); }
.shell-mobile-drawer .p-drawer-content { padding: 0 0 env(safe-area-inset-bottom); }.p-drawer.shell-mobile-drawer .p-drawer-close-button { color: var(--bee-color-nav-text); }.p-drawer.shell-mobile-drawer .p-drawer-close-button:hover { background: var(--bee-color-nav-border); }.p-drawer.shell-mobile-drawer .p-drawer-close-button:focus-visible { outline-color: var(--bee-color-nav-text); }
@media(min-width:768px) { .shell-mobile-drawer { display: none; } }
.drawer-user { display: grid; gap: 2px; margin: 0 var(--bee-space-3) var(--bee-space-2); padding: var(--bee-space-3); border-radius: var(--bee-radius-control); background: var(--bee-color-nav-border); font-size: var(--bee-type-ui); }.drawer-user .user-name { font-weight: 500; }.drawer-user .user-role { color: var(--bee-color-nav-muted); font-size: var(--bee-type-caption); }
</style>
