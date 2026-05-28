<script setup lang="ts">
import { onErrorCaptured, ref } from "vue"

import CrashView from "./CrashView.vue"

const error = ref<Error | null>(null)

onErrorCaptured((e) => {
  console.error("[ErrorBoundary]", e)
  error.value = e as Error
  return false  // hentikan propagasi
})

function reset() {
  error.value = null
  window.location.reload()
}
</script>

<template>
  <CrashView v-if="error" :error="error" @reset="reset" />
  <slot v-else />
</template>
