<script setup lang="ts">
import Paginator from "primevue/paginator"
import Icon from "./PhosphorIcon.vue"
</script>

<template>
  <!-- Shared pager. Callers pass v-model:first, rows, total-records (and @page) as attributes.
       The jump-to-page select and "dari N halaman" mean a long list never needs one click per page. -->
  <Paginator
    class="bee-paginator"
    :page-link-size="3"
    template="PrevPageLink PageLinks NextPageLink JumpToPageDropdown CurrentPageReport"
    current-page-report-template="dari {totalPages} halaman"
  >
    <template #previcon><Icon name="caret-left" /></template>
    <template #nexticon><Icon name="caret-right" /></template>
    <template #jumptopagedropdownicon><Icon name="caret-down" /></template>
  </Paginator>
</template>

<style scoped>
.bee-paginator :deep(.p-paginator-content) { flex-wrap: wrap; justify-content: center; row-gap: var(--bee-space-2); }
.bee-paginator :deep(.p-paginator-jtp-dropdown) { min-width: 5.5rem; margin-inline-start: var(--bee-space-3); }
.bee-paginator :deep(.p-paginator-current) { color: var(--app-text-muted); font-size: var(--bee-type-caption); }
</style>
