<script setup lang="ts">
import Icon from "./PhosphorIcon.vue"
import IconField from "primevue/iconfield"
import InputIcon from "primevue/inputicon"
import InputText from "primevue/inputtext"

const props = withDefaults(
  defineProps<{
    /** Teks singkat di dalam field (jangan panjang — cukup "Cari…") */
    placeholder?: string
    /** Pasangkan dengan atribut for pada label yang terlihat. */
    inputId?: string
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
    <InputIcon><Icon name="magnifying-glass" /></InputIcon>
    <InputText
      v-model="model"
      :id="inputId"
      :placeholder="placeholder"
      :aria-label="inputId ? undefined : hint ?? placeholder"
      :aria-describedby="inputId && hint ? `${inputId}-hint` : undefined"
      fluid
      class="bee-search-input"
    />
    <span v-if="inputId && hint" :id="`${inputId}-hint`" class="bee-search-hint">{{ hint }}</span>
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
.bee-search-hint { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }
</style>
