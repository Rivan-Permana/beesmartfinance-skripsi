<script setup lang="ts">
import Icon from "./PhosphorIcon.vue"
defineProps<{
  label: string
  value: string
  icon: string
  tone?: "navy" | "magenta" | "orange" | "green"
}>()
</script>

<template>
  <div class="kpi" :class="tone ?? 'navy'">
    <Icon :name="icon" />
    <div>
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value tabular-nums">{{ value }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpi { display: flex; align-items: flex-start; gap: var(--bee-space-3); padding: var(--bee-space-5); min-width: 0; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); }
.kpi > .bee-icon { margin-top: 2px; color: var(--bee-color-muted); }
.kpi-label { color: var(--app-text-muted); font-size: var(--bee-type-ui); }
.kpi-value { font-size: var(--bee-type-number-secondary); font-weight: 500; line-height: 1.3; color: var(--app-text); margin-top: var(--bee-space-2); overflow-wrap: anywhere; }
</style>
