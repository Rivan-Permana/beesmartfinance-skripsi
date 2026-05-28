<script setup lang="ts">
import ConfirmDialog from "primevue/confirmdialog"
import Toast from "primevue/toast"

import ErrorBoundary from "@/shared/error/ErrorBoundary.vue"
</script>

<template>
  <Toast />
  <ConfirmDialog />
  <ErrorBoundary>
    <RouterView />
  </ErrorBoundary>
</template>
