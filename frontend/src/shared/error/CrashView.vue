<script setup lang="ts">
import Button from "primevue/button"
import { ref } from "vue"

defineProps<{ error: Error | null }>()
defineEmits<{ (e: "reset"): void }>()

const showDetail = ref(false)
</script>

<template>
  <div class="crash">
    <div class="card">
      <div class="emoji">🐝</div>
      <h1>Maaf, ada yang tidak beres</h1>
      <p>
        Aplikasi mengalami kendala tidak terduga. Silakan muat ulang halaman.
        Bila terus berulang, hubungi admin sekolah.
      </p>

      <div class="actions">
        <Button label="Muat Ulang" icon="pi pi-refresh" @click="$emit('reset')" />
        <Button
          label="Lihat Detail Teknis"
          severity="secondary"
          text
          @click="showDetail = !showDetail"
        />
      </div>

      <pre v-if="showDetail && error" class="detail">{{ error.message }}
{{ error.stack }}</pre>
    </div>
  </div>
</template>

<style scoped>
.crash {
  min-height: 70vh;
  display: grid;
  place-items: center;
  padding: 2rem;
}
.card {
  max-width: 520px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
}
.emoji {
  font-size: 3rem;
  background: var(--bee-orange);
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin: 0 auto 0.75rem;
}
h1 { margin: 0 0 0.5rem; }
p { color: var(--app-text-muted); margin: 0 0 1.25rem; }
.actions { display: flex; gap: 0.5rem; justify-content: center; }
.detail {
  text-align: left;
  font-size: 0.75rem;
  background: #1f2430;
  color: #f3f4f6;
  padding: 0.75rem;
  border-radius: 8px;
  margin-top: 1rem;
  max-height: 240px;
  overflow: auto;
  white-space: pre-wrap;
}
</style>
