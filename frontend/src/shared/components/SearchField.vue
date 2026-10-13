<script setup lang="ts">
import IconField from "primevue/iconfield"
import InputIcon from "primevue/inputicon"
import InputText from "primevue/inputtext"

const props = withDefaults(
  defineProps<{
    /** Teks singkat di dalam field (jangan panjang — cukup "Cari…") */
    placeholder?: string
    /** Penjelasan penuh untuk tooltip / screen reader */
    hint?: string
    /** Baris penuh di toolbar (mis. di samping banyak filter) */
    block?: boolean
  }>(),
  {
    placeholder: "Cari…",
  },
)

const model = defineModel<string>({ default: "" })
</script>

<template>
  <IconField
    class="bee-search-field"
    :class="{ 'bee-search-field--block': block }"
    :title="hint"
  >
    <InputIcon class="pi pi-search" />
    <InputText
      v-model="model"
      :placeholder="placeholder"
      :aria-label="hint ?? placeholder"
      fluid
      class="bee-search-input"
    />
  </IconField>
</template>

<style scoped>
.bee-search-field {
  flex: 1 1 14rem;
  min-width: 14rem;
  max-width: 100%;
}

.bee-search-field--block {
  flex: 1 1 100%;
  width: 100%;
  min-width: 0;
  margin-bottom: 0.75rem;
}

.bee-search-field :deep(.p-iconfield) {
  width: 100%;
}

.bee-search-field :deep(.p-inputtext) {
  width: 100%;
  min-width: 0;
}
</style>
