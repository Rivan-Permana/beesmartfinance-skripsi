<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { groupedNav, navForRoles, type NavItem } from "@/core/navigation"
import Icon from "@/shared/components/PhosphorIcon.vue"

defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ navigate: [] }>()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const groups = computed(() => groupedNav(navForRoles(auth.roles)))
function isActive(item: NavItem) {
  return item.to === route.path && (item.query?.jenis ? item.query.jenis === route.query.jenis : !route.query.jenis || item.to !== "/jurnal")
}
function navigate(item: NavItem) {
  emit("navigate")
  void router.push(item.query ? { path: item.to, query: item.query } : item.to)
}
</script>

<template>
  <nav class="app-navigation" aria-label="Navigasi utama">
    <section v-for="group in groups" :key="group.group">
      <h2 v-if="!collapsed">{{ group.label }}</h2>
      <button v-for="item in group.items" :key="item.to + (item.query?.jenis ?? '')" type="button" :class="{ active: isActive(item), compact: collapsed }" :aria-current="isActive(item) ? 'page' : undefined" :aria-label="item.label" :title="collapsed ? item.label : undefined" @click="navigate(item)">
        <Icon :name="item.icon" /><span v-if="!collapsed">{{ item.label }}</span>
      </button>
    </section>
  </nav>
</template>

<style scoped>
.app-navigation { padding: var(--bee-space-3); overflow-y: auto; flex: 1; }
section { margin-bottom: var(--bee-space-5); }
h2 { margin: var(--bee-space-4) var(--bee-space-3) var(--bee-space-2); color: var(--bee-color-nav-muted); font-size: var(--bee-type-caption); font-weight: 400; }
button { display: flex; align-items: center; gap: var(--bee-space-3); width: 100%; min-height: 44px; padding: var(--bee-space-3); border: 0; border-radius: var(--bee-radius-control); background: transparent; color: var(--bee-color-nav-text); font-size: var(--bee-type-ui); cursor: pointer; text-align: start; margin-bottom: var(--bee-space-1); }
button:hover { background: var(--bee-color-nav-border); }
button.active { background: var(--bee-color-surface); color: var(--bee-color-nav); font-weight: 500; }
button:focus-visible { outline-color: var(--bee-color-nav-text); outline-offset: -3px; }
button.active:focus-visible { outline-color: var(--bee-color-nav); }
button.compact { justify-content: center; padding-inline: 0; }
</style>
