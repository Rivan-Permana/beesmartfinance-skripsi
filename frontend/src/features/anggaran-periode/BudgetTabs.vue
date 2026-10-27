<script setup lang="ts">
import { RouterLink } from "vue-router"
import Icon from "@/shared/components/PhosphorIcon.vue"
defineProps<{ current: "kegiatan" | "akun" }>()
</script>

<template>
  <!-- Menu Anggaran Kegiatan menggabungkan pagu per kegiatan dan anggaran per akun. -->
  <nav class="budget-tabs" aria-label="Anggaran Kegiatan">
    <RouterLink to="/kegiatan" :aria-current="current === 'kegiatan' ? 'page' : undefined"><Icon name="flag" />Per kegiatan</RouterLink>
    <RouterLink to="/anggaran" :aria-current="current === 'akun' ? 'page' : undefined"><Icon name="chart-pie" />Per akun</RouterLink>
  </nav>
</template>

<style scoped>
.budget-tabs { display: flex; gap: var(--bee-space-1); margin-bottom: var(--bee-space-5); border-bottom: 1px solid var(--app-border); overflow-x: auto; }
.budget-tabs a { display: inline-flex; align-items: center; gap: var(--bee-space-2); min-height: 44px; padding: 0 var(--bee-space-4); border-bottom: 2px solid transparent; color: var(--app-text-muted); font-size: var(--bee-type-ui); text-decoration: none; white-space: nowrap; }
.budget-tabs a .bee-icon { width: 16px; height: 16px; }
.budget-tabs a[aria-current=page] { border-bottom-color: var(--bee-color-brand); color: var(--bee-color-brand); font-weight: 500; }
.budget-tabs a:hover:not([aria-current=page]) { color: var(--app-text); }
.budget-tabs a:focus-visible { outline: 2px solid var(--bee-color-focus); outline-offset: -2px; }
</style>
