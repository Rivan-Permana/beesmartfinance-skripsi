<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  subtitle?: string
  surface?: boolean
}>(), { surface: true })
</script>

<template>
  <div class="bee-page">
    <div class="bee-page__header">
      <div class="bee-page__titles">
        <h1>{{ title }}</h1>
        <p v-if="subtitle" class="bee-page__subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="bee-page__actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="$slots.filters" class="bee-page__filters">
      <slot name="filters" />
    </div>
    <div class="bee-page__card" :class="{ 'bee-page__card--plain': surface === false }">
      <slot />
    </div>
  </div>
</template>
