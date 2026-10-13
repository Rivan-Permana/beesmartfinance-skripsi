<script setup lang="ts">
import Button from "primevue/button"

defineProps<{
  message: string
  actionLabel?: string
}>()

const emit = defineEmits<{ action: [] }>()
</script>

<template>
  <div class="empty">
    <img src="/logo-lebah.svg" alt="" class="empty-icon" width="56" height="56" />
    <p>{{ message }}</p>
    <Button
      v-if="actionLabel"
      :label="actionLabel"
      size="small"
      @click="emit('action')"
    />
  </div>
</template>

<style scoped>
.empty {
  text-align: center;
  padding: 2.5rem 1rem;
  color: var(--app-text-muted);
}
.empty-icon {
  opacity: 0.85;
  margin-bottom: 0.75rem;
}
.empty p {
  margin: 0 0 1rem;
}
</style>
