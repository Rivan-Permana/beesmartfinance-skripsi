<script setup lang="ts">
import Icon from "./PhosphorIcon.vue"

const props = defineProps<{ clearCallback: (event: MouseEvent) => void }>()

function clear(event: MouseEvent) {
  const input = (event.currentTarget as HTMLElement).closest('[data-pc-name="select"]')?.querySelector<HTMLElement>('[role="combobox"]')
  props.clearCallback(event)
  input?.focus()
}
</script>

<template>
  <button type="button" class="bee-select-clear" data-pc-section="clearicon" aria-label="Hapus pilihan" title="Hapus pilihan" @click.stop="clear">
    <Icon name="x" />
  </button>
</template>

<style scoped>
.bee-select-clear {
  display: inline-grid;
  place-items: center;
  align-self: stretch;
  flex: 0 0 var(--bee-size-control);
  min-block-size: var(--bee-size-control);
  padding: 0;
  border: 0;
  border-radius: var(--bee-radius-control);
  background: transparent;
  color: var(--app-text-muted);
  cursor: pointer;
}
.bee-select-clear:hover { background: var(--bee-color-surface-subtle); color: var(--app-text); }
</style>
