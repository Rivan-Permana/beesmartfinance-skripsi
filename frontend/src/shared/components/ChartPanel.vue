<script setup lang="ts">
import Icon from "./PhosphorIcon.vue"
defineProps<{
  title: string
  subtitle?: string
  icon?: string
  accent?: "navy" | "magenta" | "orange" | "green" | "blue"
  size?: "md" | "sm" | "lg"
  loading?: boolean
  empty?: boolean
  emptyText?: string
}>()
</script>

<template>
  <section class="chart-panel" :class="[accent ?? 'navy', size ?? 'md']">
    <header class="chart-panel__head">
      <div class="chart-panel__title-wrap">
        <span v-if="icon" class="chart-panel__icon"><Icon :name="icon" /></span>
        <div>
          <h3 class="chart-panel__title">{{ title }}</h3>
          <p v-if="subtitle" class="chart-panel__sub">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.action" class="chart-panel__action">
        <slot name="action" />
      </div>
    </header>
    <div class="chart-panel__body">
      <div v-if="loading" class="chart-panel__skeleton" role="status" aria-label="Memuat data">
        <div class="sk-line sk-line--1" />
        <div class="sk-line sk-line--2" />
        <div class="sk-line sk-line--3" />
      </div>
      <div v-else-if="empty" class="chart-panel__empty">
        <Icon name="chart-bar" />
        <span>{{ emptyText ?? "Belum ada data untuk ditampilkan." }}</span>
      </div>
      <slot v-else />
    </div>
  </section>
</template>

<style scoped>
.chart-panel { background: var(--app-surface); border: 1px solid var(--app-border); border-radius: var(--bee-radius-panel); padding: var(--bee-space-5); display: flex; flex-direction: column; min-width: 0; }
.chart-panel__head, .chart-panel__title-wrap { display: flex; align-items: flex-start; gap: var(--bee-space-3); }
.chart-panel__head { justify-content: space-between; margin-bottom: var(--bee-space-5); flex-wrap: wrap; }
.chart-panel__title-wrap { min-width: 0; }
.chart-panel__icon { color: var(--bee-color-muted); padding-top: 2px; }
.chart-panel__title { margin: 0; font-size: var(--bee-type-section); font-weight: 500; line-height: 1.3; color: var(--app-text); }
.chart-panel__sub { margin: var(--bee-space-2) 0 0; font-size: var(--bee-type-caption); color: var(--app-text-muted); }
.chart-panel__action :deep(.link) { color: var(--bee-color-brand); font-size: var(--bee-type-ui); }
.chart-panel__body { flex: 1; min-height: 0; position: relative; }
.chart-panel.sm .chart-panel__body :deep(.chart-wrap) { height: 200px; }
.chart-panel.md .chart-panel__body :deep(.chart-wrap) { height: 280px; }
.chart-panel.lg .chart-panel__body :deep(.chart-wrap) { height: 320px; }
.chart-panel__empty { display: flex; align-items: center; justify-content: center; gap: var(--bee-space-3); min-height: 180px; text-align: center; color: var(--app-text-muted); }
.chart-panel__skeleton { display: grid; gap: var(--bee-space-4); padding-block: var(--bee-space-6); }
.sk-line { height: 24px; border-radius: var(--bee-radius-status); background: var(--bee-color-neutral-tint); }
.sk-line--2 { width: 68%; }.sk-line--3 { width: 84%; }
</style>
