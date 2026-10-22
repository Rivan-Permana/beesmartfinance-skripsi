<script setup lang="ts">
import { computed } from "vue"
import Icon from "./PhosphorIcon.vue"

// Familiar pager: ‹ 1 … 4 5 6 … 16 ›. First and last pages are always one click away.
// API mirrors the PrimeVue Paginator props the lists already pass (v-model:first, rows, total-records, @page).
const props = withDefaults(defineProps<{ rows: number; totalRecords: number; alwaysShow?: boolean }>(), { alwaysShow: false })
const first = defineModel<number>("first", { default: 0 })
const emit = defineEmits<{ page: [event: { page: number; first: number; rows: number; pageCount: number }] }>()

const pageCount = computed(() => Math.max(1, Math.ceil(props.totalRecords / props.rows)))
const current = computed(() => Math.min(pageCount.value - 1, Math.floor(first.value / props.rows)))
const items = computed(() => {
  const last = pageCount.value - 1, pages = new Set([0, last, current.value - 1, current.value, current.value + 1])
  const sorted = [...pages].filter(p => p >= 0 && p <= last).sort((a, b) => a - b)
  const out: Array<{ page: number; neighbor: boolean } | "gap"> = []
  sorted.forEach((page, i) => {
    if (i && page - sorted[i - 1]! > 1) out.push("gap")
    out.push({ page, neighbor: Math.abs(page - current.value) === 1 && page !== 0 && page !== last })
  })
  return out
})
function go(page: number) {
  if (page < 0 || page >= pageCount.value || page === current.value) return
  first.value = page * props.rows
  emit("page", { page, first: first.value, rows: props.rows, pageCount: pageCount.value })
}
</script>

<template>
  <nav v-if="alwaysShow || pageCount > 1" class="bee-pager" aria-label="Halaman daftar">
    <button type="button" class="bee-pager-step" :disabled="current === 0" aria-label="Halaman sebelumnya" @click="go(current - 1)">
      <Icon name="caret-left" />
    </button>
    <template v-for="(item, i) in items" :key="item === 'gap' ? `gap-${i}` : item.page">
      <span v-if="item === 'gap'" class="bee-pager-gap" aria-hidden="true">…</span>
      <button v-else type="button" :class="{ 'bee-pager-neighbor': item.neighbor }" :aria-current="item.page === current ? 'page' : undefined" :aria-label="`Halaman ${item.page + 1}`" @click="go(item.page)">
        {{ item.page + 1 }}
      </button>
    </template>
    <button type="button" class="bee-pager-step" :disabled="current === pageCount - 1" aria-label="Halaman berikutnya" @click="go(current + 1)">
      <Icon name="caret-right" />
    </button>
  </nav>
</template>

<style scoped>
.bee-pager { container-type: inline-size; display: flex; flex-wrap: nowrap; align-items: center; justify-content: center; gap: var(--bee-space-1); padding: var(--bee-space-3) var(--bee-space-4); }
button { display: inline-flex; align-items: center; justify-content: center; min-width: var(--bee-size-control); height: var(--bee-size-control); padding-inline: var(--bee-space-2); border: 0; border-radius: var(--bee-radius-control); background: transparent; color: var(--app-text); font: inherit; font-size: var(--bee-type-ui); font-variant-numeric: tabular-nums; cursor: pointer; }
button:hover:not(:disabled) { background: var(--bee-color-surface-subtle); }
button[aria-current="page"] { background: var(--bee-color-brand-tint); color: var(--bee-color-brand); font-weight: 600; cursor: default; }
button:disabled { color: var(--bee-color-disabled-text, var(--app-text-muted)); cursor: default; opacity: .5; }
.bee-pager-gap { min-width: 1.5rem; text-align: center; color: var(--app-text-muted); }
.bee-icon { width: 18px; height: 18px; }
/* Narrow panels keep first, current, and last pages so the row never wraps. */
@container (max-width: 380px) { .bee-pager-neighbor { display: none; } }
</style>
