<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router"
import Icon from "./PhosphorIcon.vue"
defineProps<{
  label: string
  value: string
  icon: string
  tone?: "navy" | "magenta" | "orange" | "green" | "blue" | "red" | "gold"
  hint?: string
  /** Kartu menjadi tautan ke rincian bila diisi. */
  to?: RouteLocationRaw
  /** Isi 0–100 untuk menampilkan bilah kemajuan. */
  progress?: number | null
}>()
</script>

<template>
  <component :is="to ? RouterLink : 'div'" :to="to" class="kpi" :class="[tone ?? 'navy', { 'kpi--link': !!to }]">
    <span class="kpi-icon"><Icon :name="icon" /></span>
    <div class="kpi-body">
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value tabular-nums">{{ value }}</div>
      <div v-if="progress != null" class="kpi-progress" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100" :aria-label="label"><span :style="{ width: `${Math.max(0, Math.min(100, progress))}%` }" /></div>
      <div v-if="hint" class="kpi-hint">{{ hint }}</div>
      <slot />
    </div>
    <Icon v-if="to" name="arrow-right" class="kpi-go" />
  </component>
</template>

<style scoped>
.kpi { --kpi-ink: var(--bee-color-chart-ink); --kpi-tint: var(--bee-color-neutral-tint); position: relative; display: flex; align-items: flex-start; gap: var(--bee-space-4); padding: var(--bee-space-5); min-width: 0; background: var(--app-surface); border: 1px solid var(--app-border); border-top: 4px solid var(--kpi-ink); border-radius: var(--bee-radius-panel); color: inherit; text-decoration: none; transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease; }
.kpi.green { --kpi-ink: var(--bee-color-positive); --kpi-tint: var(--bee-color-positive-tint); }
.kpi.magenta { --kpi-ink: var(--bee-color-brand); --kpi-tint: var(--bee-color-brand-tint); }
.kpi.red { --kpi-ink: var(--bee-color-critical); --kpi-tint: var(--bee-color-critical-tint); }
.kpi.orange { --kpi-ink: var(--bee-color-warning); --kpi-tint: var(--bee-color-warning-tint); }
.kpi.blue { --kpi-ink: var(--bee-color-info); --kpi-tint: var(--bee-color-info-tint); }
.kpi.gold { --kpi-ink: var(--bee-color-chart-gold); --kpi-tint: var(--bee-color-warning-tint); }
.kpi-icon { display: grid; place-items: center; flex: none; width: 40px; height: 40px; border-radius: 12px; background: var(--kpi-tint); color: var(--kpi-ink); }
.kpi-body { min-width: 0; flex: 1; }
.kpi-label { color: var(--app-text-muted); font-size: var(--bee-type-ui); }
.kpi-value { font-size: var(--bee-type-number-secondary); font-weight: 600; line-height: 1.3; color: var(--kpi-ink); margin-top: var(--bee-space-1); overflow-wrap: anywhere; }
.kpi-hint { margin-top: var(--bee-space-2); font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.kpi-progress { margin-top: var(--bee-space-3); height: 8px; border-radius: 999px; background: var(--kpi-tint); overflow: hidden; }
.kpi-progress span { display: block; height: 100%; border-radius: inherit; background: var(--kpi-ink); transition: width .4s ease; }
.kpi-go { position: absolute; top: var(--bee-space-4); right: var(--bee-space-4); width: 16px; height: 16px; color: var(--app-text-muted); opacity: 0; transition: opacity .16s ease, transform .16s ease; }
.kpi--link:hover { border-color: var(--kpi-ink); box-shadow: 0 6px 18px -10px var(--kpi-ink); transform: translateY(-2px); }
.kpi--link:hover .kpi-go { opacity: 1; transform: translateX(2px); }
.kpi--link:focus-visible { outline: 2px solid var(--bee-color-focus); outline-offset: 2px; }
@media (hover: none) { .kpi-go { opacity: .7; } }
@media (prefers-reduced-motion: reduce) { .kpi, .kpi-go, .kpi-progress span { transition: none; } .kpi--link:hover { transform: none; } }
</style>
