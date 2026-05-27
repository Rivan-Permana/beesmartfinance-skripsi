<script setup lang="ts">
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Password from "primevue/password"
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")

async function submit() {
  error.value = ""
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const next = (route.query.next as string) || "/"
    router.push(next)
  } catch (e: any) {
    error.value =
      e?.response?.status === 401
        ? "Username atau password salah."
        : "Gagal masuk. Coba lagi."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <div class="logo">🐝</div>
      <h1>Sekolah Lebah Madu</h1>
      <p class="sub">Sistem Informasi Akuntansi</p>

      <Message v-if="error" severity="error" :closable="false" class="mb">
        {{ error }}
      </Message>

      <label>Username</label>
      <InputText v-model="username" autocomplete="username" fluid />

      <label>Password</label>
      <Password
        v-model="password"
        :feedback="false"
        toggle-mask
        input-class="w-full"
        fluid
      />

      <Button
        type="submit"
        label="Masuk"
        :loading="loading"
        class="mt"
        fluid
      />
    </form>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--bee-navy), var(--bee-magenta));
  padding: 1rem;
}
.login-card {
  width: 100%;
  max-width: 380px;
  background: #fff;
  border-radius: 18px;
  padding: 2rem 1.75rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
}
.logo {
  font-size: 2.5rem;
  background: var(--bee-orange);
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin: 0 auto 0.5rem;
}
h1 {
  text-align: center;
  font-size: 1.3rem;
}
.sub {
  text-align: center;
  color: var(--app-text-muted);
  margin: 0 0 1.25rem;
}
label {
  font-weight: 600;
  font-size: 0.85rem;
  margin: 0.6rem 0 0.25rem;
}
.mb {
  margin-bottom: 0.5rem;
}
.mt {
  margin-top: 1.25rem;
}
</style>
