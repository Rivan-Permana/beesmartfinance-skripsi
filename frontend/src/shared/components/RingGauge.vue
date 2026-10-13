<script setup lang="ts">
import { computed } from "vue"

const props = defineProps<{
  value: number
  label?: string
  size?: number
}>()

const size = computed(() => props.size ?? 160)
const stroke = 12
const radius = computed(() => (size.value - stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() => {
  const clamped = Math.min(Math.max(props.value, 0), 100)
  return circumference.value * (1 - clamped / 100)
})
const tone = computed(() => {
  if (props.value >= 100) return "danger"
  if (props.value >= 80) return "warn"
  return "ok"
})
</script>

<template>
  <div class="ring-gauge" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <circle
        class="ring-gauge__track"
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        :stroke-width="stroke"
        fill="none"
      />
      <circle
        class="ring-gauge__fill"
        :class="tone"
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        :stroke-width="stroke"
        fill="none"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
      />
    </svg>
    <div class="ring-gauge__center">
      <span class="ring-gauge__value" :class="tone">{{ value }}%</span>
      <span v-if="label" class="ring-gauge__label">{{ label }}</span>
    </div>
  </div>
</template>

<style scoped>
.ring-gauge {
  position: relative;
  margin: 0 auto;
}
.ring-gauge__track {
  stroke: rgba(46, 42, 110, 0.08);
}
.ring-gauge__fill {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.ring-gauge__fill.ok { stroke: var(--bee-navy); }
.ring-gauge__fill.warn { stroke: var(--bee-orange); }
.ring-gauge__fill.danger { stroke: var(--bee-magenta); }

.ring-gauge__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
}
.ring-gauge__value {
  font-family: "Baloo 2", sans-serif;
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
  color: var(--bee-navy);
}
.ring-gauge__value.warn { color: var(--bee-orange); }
.ring-gauge__value.danger { color: var(--bee-magenta); }
.ring-gauge__label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--app-text-muted);
}
</style>
