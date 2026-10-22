<script setup lang="ts">
import { computed } from "vue"
import { resolveIcon } from "@/core/icons"
import sprite from "../icons/phosphor.svg?url"
const props = defineProps<{ name: string }>()
const icon = computed(() => resolveIcon(props.name))
</script>

<template>
  <svg class="icon bee-icon" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true" focusable="false">
    <use :href="`${sprite}#${icon}`" />
  </svg>
</template>
