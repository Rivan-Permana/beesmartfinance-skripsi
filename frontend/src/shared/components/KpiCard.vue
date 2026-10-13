<script setup lang="ts">
defineProps<{
  label: string
  value: string
  icon: string
  tone?: "navy" | "magenta" | "orange" | "green"
}>()
</script>

<template>
  <div class="kpi" :class="tone ?? 'navy'">
    <i :class="icon" />
    <div>
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value tabular-nums">{{ value }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpi {
  --kpi-accent: var(--bee-navy);
  display: flex;
  align-items: center;
  gap: 0.85rem;
  background: var(--app-surface);
  border: 1px solid rgba(46, 42, 110, 0.08);
  border-radius: var(--bee-radius-lg);
  padding: 1rem 1.15rem;
  box-shadow: 0 4px 16px rgba(46, 42, 110, 0.05);
  position: relative;
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.kpi::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--kpi-accent);
  border-radius: 4px 0 0 4px;
}
.kpi:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(46, 42, 110, 0.1);
}
.kpi.magenta { --kpi-accent: var(--bee-magenta); }
.kpi.orange { --kpi-accent: var(--bee-orange); }
.kpi.green { --kpi-accent: var(--bee-success); }
.kpi i {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 1.1rem;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--kpi-accent), color-mix(in srgb, var(--kpi-accent) 75%, #000));
  box-shadow: 0 4px 12px color-mix(in srgb, var(--kpi-accent) 35%, transparent);
}
.kpi-label {
  font-size: 0.76rem;
  color: var(--app-text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.kpi-value {
  font-size: 1.28rem;
  font-weight: 800;
  color: var(--bee-navy);
  margin-top: 0.1rem;
}
</style>
