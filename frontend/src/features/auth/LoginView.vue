<script setup lang="ts">
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import Message from "primevue/message"
import Password from "primevue/password"
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { roleHome } from "@/core/navigation"
import { useAuthStore } from "@/stores/auth"
import type { Role } from "@/types/api"

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
    const next = route.query.next as string | undefined
    if (next && next !== "/") {
      const resolved = router.resolve(next)
      const req = resolved.meta.roles as Role[] | undefined
      if (!req || auth.hasRole(req)) {
        await router.push(next)
        return
      }
    }
    await router.push(roleHome(auth.roles))
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) error.value = "Username atau password salah."
    else if (status === 429) {
      // Two limits answer 429: login attempts per address (token request) and the daily request quota per account (later requests).
      const wait = Number(e.response.headers?.["retry-after"])
      const when = Number.isFinite(wait) && wait > 0 ? (wait > 3600 ? `sekitar ${Math.ceil(wait / 3600)} jam lagi` : `dalam ${Math.ceil(wait)} detik`) : "sebentar lagi"
      error.value = String(e.config?.url ?? "").includes("auth/token")
        ? `Terlalu banyak percobaan masuk dari perangkat ini. Coba lagi ${when}.`
        : `Akun ini sudah mencapai batas permintaan harian. Coba lagi ${when} atau hubungi admin.`
    }
    else error.value = "Gagal masuk. Coba lagi."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <img src="/logo-lebah.svg" alt="" class="logo" width="64" height="64" />
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
  margin: 0 auto 0.5rem;
  display: block;
  border-radius: 50%;
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
