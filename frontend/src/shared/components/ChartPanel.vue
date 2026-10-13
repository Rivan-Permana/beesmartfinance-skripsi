<script setup lang="ts">
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
        <span v-if="icon" class="chart-panel__icon"><i :class="icon" /></span>
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
      <div v-if="loading" class="chart-panel__skeleton" aria-hidden="true">
        <div class="sk-line sk-line--1" />
        <div class="sk-line sk-line--2" />
        <div class="sk-line sk-line--3" />
      </div>
      <div v-else-if="empty" class="chart-panel__empty">
        <i class="pi pi-chart-bar" />
        <span>{{ emptyText ?? "Belum ada data untuk ditampilkan." }}</span>
      </div>
      <slot v-else />
    </div>
  </section>
</template>

<style scoped>
.chart-panel {
  --panel-accent: var(--bee-navy);
  background: var(--app-surface);
  border: 1px solid rgba(46, 42, 110, 0.08);
  border-radius: var(--bee-radius-lg);
  padding: 1.15rem 1.25rem;
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-shadow:
    0 1px 2px rgba(46, 42, 110, 0.04),
    0 8px 24px rgba(46, 42, 110, 0.05);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.chart-panel:hover {
  box-shadow:
    0 2px 4px rgba(46, 42, 110, 0.06),
    0 12px 32px rgba(46, 42, 110, 0.08);
}
.chart-panel.magenta { --panel-accent: var(--bee-magenta); }
.chart-panel.orange { --panel-accent: var(--bee-orange); }
.chart-panel.green { --panel-accent: var(--bee-success); }
.chart-panel.blue { --panel-accent: var(--bee-sky); }

.chart-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(46, 42, 110, 0.06);
}
.chart-panel__title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: 0;
}
.chart-panel__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: color-mix(in srgb, var(--panel-accent) 12%, transparent);
  color: var(--panel-accent);
  flex-shrink: 0;
  font-size: 0.95rem;
}
.chart-panel__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--bee-navy);
}
.chart-panel__sub {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: var(--app-text-muted);
}
.chart-panel__action :deep(.link) {
  color: var(--bee-magenta);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
  white-space: nowrap;
}
.chart-panel__body {
  flex: 1;
  min-height: 0;
  position: relative;
}
.chart-panel.sm .chart-panel__body :deep(.chart-wrap) { height: 200px; }
.chart-panel.md .chart-panel__body :deep(.chart-wrap) { height: 280px; }
.chart-panel.lg .chart-panel__body :deep(.chart-wrap) { height: 320px; }

.chart-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 180px;
  color: var(--app-text-muted);
  font-size: 0.85rem;
  text-align: center;
  padding: 1rem;
}
.chart-panel__empty i {
  font-size: 1.75rem;
  opacity: 0.35;
}

.chart-panel__skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.5rem 0;
  min-height: 180px;
  justify-content: center;
}
.sk-line {
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    rgba(46, 42, 110, 0.06) 0%,
    rgba(46, 42, 110, 0.12) 50%,
    rgba(46, 42, 110, 0.06) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s ease infinite;
}
.sk-line--1 { width: 92%; }
.sk-line--2 { width: 68%; animation-delay: 0.15s; }
.sk-line--3 { width: 84%; animation-delay: 0.3s; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
