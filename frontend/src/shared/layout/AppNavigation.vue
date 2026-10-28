<script setup lang="ts">
import { computed } from "vue"
import { RouterLink, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { groupedNav, navForRoles, navItemActive, type NavItem } from "@/core/navigation"
import Icon from "@/shared/components/PhosphorIcon.vue"

defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ navigate: [] }>()
const auth = useAuthStore()
const route = useRoute()
const groups = computed(() => groupedNav(navForRoles(auth.roles), auth.roles))
function isActive(item: NavItem) {
  return navItemActive(item, route.path, route.query.jenis)
}
function target(item: NavItem) {
  return item.query ? { path: item.to, query: item.query } : item.to
}
</script>

<template>
  <nav class="app-navigation" aria-label="Navigasi utama">
    <section v-for="group in groups" :key="group.group">
      <h2 v-if="!collapsed">{{ group.label }}</h2>
      <!-- Real links: open in a new tab, copy the address, and announce as navigation. -->
      <RouterLink v-for="item in group.items" :key="item.to + (item.query?.jenis ?? '')" :to="target(item)" active-class="" exact-active-class="" :class="{ active: isActive(item), compact: collapsed }" :aria-current="isActive(item) ? 'page' : undefined" :aria-label="collapsed ? item.label : undefined" :title="collapsed ? item.label : undefined" @click="emit('navigate')">
        <Icon :name="item.icon" /><span v-if="!collapsed">{{ item.label }}</span>
      </RouterLink>
    </section>
  </nav>
</template>

<style scoped>
.app-navigation { padding: var(--bee-space-3); overflow-y: auto; flex: 1; }
section { margin-bottom: var(--bee-space-5); }
h2 { margin: var(--bee-space-4) var(--bee-space-3) var(--bee-space-2); color: var(--bee-color-nav-muted); font-size: var(--bee-type-caption); font-weight: 400; }
a { display: flex; align-items: center; gap: var(--bee-space-3); width: 100%; min-height: 44px; padding: var(--bee-space-3); border: 0; border-radius: var(--bee-radius-control); background: transparent; color: var(--bee-color-nav-text); font-size: var(--bee-type-ui); line-height: var(--bee-leading-control); cursor: pointer; text-align: start; text-decoration: none; margin-bottom: var(--bee-space-1); }
a:hover { background: var(--bee-color-nav-border); }
a.active { background: var(--bee-color-surface); color: var(--bee-color-nav); font-weight: 500; }
a:focus-visible { outline-color: var(--bee-color-nav-text); outline-offset: -3px; }
a.active:focus-visible { outline-color: var(--bee-color-nav); }
a.compact { justify-content: center; padding-inline: 0; }
</style>
