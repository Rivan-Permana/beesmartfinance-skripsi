# 🎨 Frontend Migration Guide

> Panduan migrasi frontend ke SPA modern.
>
> ⚠️ **REVISI FINAL (berlaku) — lihat bagian "Rencana Final" di bawah.**
> Bagian lama (Vuetify) dipertahankan sebagai referensi historis, namun
> **keputusan final memakai PrimeVue + TypeScript** sesuai ringkasan berikut.

---

## ✅ Rencana Final Frontend (revisi)

### Tech stack final
- **Vite + Vue 3 + TypeScript** (`<script setup lang="ts">`, `strict`)
- **PrimeVue 4** (komponen) + **@primeuix/themes** (Aura + preset brand)
- **Pinia** (state), **Vue Router** (+ guard RBAC), **Axios** (client + interceptor JWT/refresh)
- Tipe API idealnya **di-generate dari OpenAPI** (`/api/schema`) agar sinkron dgn backend

### Tema: "Branded-Professional"
Layout **dashboard admin** (sidebar navy + topbar + konten terang), bukan kloning
landing page. Brand sekolah masuk sebagai **aksen** (bukan dekorasi penuh) demi
keterbacaan untuk staf harian (termasuk pengguna kurang tech-savvy).

Palette (dari web compro `sekolahlebahmadu.com`):
- Orange `#F5A623` · Magenta `#E5197F` (primary) · Navy `#2E2A6E` (sidebar/heading)
- Sky Blue `#4FB0DB` · Cream `#F5EDD6` (aksen) · workspace terang `#F6F7FB`
- Font: **Nunito Sans** (body) + **Baloo 2** (heading/brand), logo lebah 🐝

### Struktur folder (feature-based, selaras backend)
```
frontend/src/
├── core/        theme.ts · api.ts (axios+interceptor) · router.ts
├── stores/      auth.ts (Pinia: token, user, role, hasRole)
├── types/       api.ts (DTO domain; calon hasil generate OpenAPI)
├── shared/      layout/AppShell.vue (sidebar navy + topbar)
└── features/    <domain>/  (views, components, api.ts)
                 auth/ · siswa/ · (jurnal, tagihan, gaji, dst — menyusul)
```

### Auth & RBAC
- Login → JWT (access+refresh) di `localStorage`; `auth/me` ambil role (Groups).
- **Route guard** + menu/aksi tampil per role (Finance/SchoolPrincipal/
  Administration/TeacherInCharge) — cermin RBAC backend. UI gating ≠ security
  boundary; server tetap otoritatif.
- Axios interceptor: inject `Bearer`, auto-refresh saat 401, logout bila gagal.

### Konsistensi BE↔FE
- Konsumsi **`/api/v1/`**; istilah & status domain (DRAFT/PENDING/POSTED, dll)
  persis backend; nominal `Decimal` ditangani aman (hindari float liar).

### Peta modul → endpoint (acuan implementasi bertahap)
| Modul FE | Endpoint utama | Role |
|---|---|---|
| Login / sesi | `auth/token`, `auth/token/refresh`, `auth/me` | semua |
| Siswa (✅ fondasi) | `siswa/` | Administration |
| Jurnal + maker-checker | `jurnal/` (+`submit`/`approve`/`void`) | Finance/Principal |
| Tagihan + bayar/struk | `tagihan/` (+`generate`/`bayar`/`struk`) | Administration |
| Pegawai/Gaji/Pinjaman | `pegawai/`,`gaji/`(+`posting`),`pinjaman/`(+`cairkan`) | Finance/Principal |
| Aset | `aset/`(+`susutkan`) | Finance |
| Kegiatan | `kegiatan/`(+`realisasi`/`laporan`) | Teacher/Principal |
| Anggaran/Periode | `anggaran/`,`periode/`(+`tutup`) | Finance/Principal |
| Laporan & Dashboard | `laporan/*`,`dashboard/*` | Finance/Principal |

### Status implementasi
- ✅ Fondasi: scaffold, tema brand, auth JWT+refresh, guard RBAC + role-aware
  home redirect, AppShell (sidebar navy + topbar).
- ✅ Pesan ramah terpusat: `core/errors.ts` (`notifyError`, `notifySuccess`)
  — pesan Indonesia kontekstual untuk pegawai (401/403/404/429/500/koneksi/
  validasi + sukses dengan `detail` dari backend).
- ✅ Modul terimplementasi:
  - **Siswa** (Administration) — CRUD
  - **Tagihan** (Administration) — list + generate + bayar + struk
  - **Dashboard** (Finance/Principal) — KPI + realisasi anggaran
  - **Jurnal** (Finance/Principal) — list + buat (multi-baris, cek balance)
    + alur maker-checker (submit/approve/void)
  - **Pegawai** (Finance/Principal baca; Finance tulis) — CRUD
  - **Gaji** (Finance/Principal baca; Finance tulis) — list + buat slip + posting
  - **Kasbon/Pinjaman** (Finance/Principal baca; Finance tulis) — list + ajukan + cairkan
  - **Aset** (Finance/Principal) — list + tambah + susutkan
  - **Kegiatan** (Teacher/Principal) — list + buat + realisasi + laporan utilisasi
- ⬜ Berikutnya: Anggaran/Periode (CRUD + tutup), Laporan detail
  (neraca-saldo, laba-rugi, posisi-keuangan, realisasi-anggaran, buku-besar).

---

## 📑 Table of Contents (dokumen lama — referensi)

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Project Setup](#project-setup)
- [Architecture](#architecture)
- [Design System](#design-system)
- [Component Migration](#component-migration)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [UI/UX Improvements](#uiux-improvements)
- [Migration Strategy](#migration-strategy)

---

## Overview

### Goals
- ✅ Modern, reactive UI with Vue.js 3
- ✅ Material Design components with Vuetify
- ✅ Single Page Application (SPA)
- ✅ Better user experience (no page reloads)
- ✅ Component reusability
- ✅ Type safety with TypeScript (optional)
- ✅ PWA capabilities

### Timeline
- **Setup**: 1 week
- **Core Components**: 2 weeks
- **Dashboard Migration**: 1 week
- **Module Migration** (per module): 1 week each
- **Testing & Polish**: 2 weeks
- **Total**: ~10-12 weeks

---

## Technology Stack

### Frontend Framework
```json
{
  "name": "beesmartfinance-frontend",
  "version": "1.0.0",
  "dependencies": {
    "vue": "^3.4.0",
    "vuetify": "^3.4.0",
    "pinia": "^2.1.7",
    "vue-router": "^4.2.5",
    "axios": "^1.6.2",
    "date-fns": "^3.0.0",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.3.0",
    "vee-validate": "^4.12.0",
    "yup": "^1.3.3"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^4.5.0",
    "vitest": "^1.0.0",
    "@vue/test-utils": "^2.4.0",
    "cypress": "^13.6.0",
    "eslint": "^8.55.0",
    "eslint-plugin-vue": "^9.19.0",
    "prettier": "^3.1.0",
    "typescript": "^5.3.0",
    "sass": "^1.69.0"
  }
}
```

### Why Vue.js 3 + Vuetify?

| Feature | Vue.js 3 + Vuetify | React + Ant Design | Angular + Material |
|---------|-------------------|-------------------|-------------------|
| Learning Curve | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐ Steep |
| Performance | Excellent | Excellent | Good |
| Component Library | Vuetify (Material Design) | Ant Design | Angular Material |
| Bundle Size | Small (~100kb) | Medium (~150kb) | Large (~200kb+) |
| TypeScript | Optional | Required (modern) | Required |
| Admin Dashboard | Perfect fit | Good | Good |
| Community | Large | Very Large | Large |
| Django Integration | Excellent | Good | Good |

**Decision**: Vue.js 3 + Vuetify untuk kemudahan development, dokumentasi lengkap, dan cocok untuk admin dashboard.

---

## Project Setup

### Step 1: Create Frontend Project

```bash
# Navigate to project root
cd /home/user/beesmartfinance

# Create frontend directory
npm create vite@latest frontend -- --template vue

# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

### Step 2: Install Vuetify

```bash
# Install Vuetify
npm install vuetify@^3.4.0

# Install Material Design Icons
npm install @mdi/font

# Install Sass (for custom styling)
npm install -D sass
```

### Step 3: Install Additional Dependencies

```bash
# State management
npm install pinia

# Router
npm install vue-router

# HTTP client
npm install axios

# Form validation
npm install vee-validate yup

# Date utilities
npm install date-fns

# Charts
npm install chart.js vue-chartjs

# Number formatting
npm install numeral
```

### Step 4: Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── img/
├── src/
│   ├── assets/
│   │   ├── styles/
│   │   │   ├── main.scss
│   │   │   ├── variables.scss
│   │   │   └── vuetify.scss
│   │   └── img/
│   ├── components/
│   │   ├── common/
│   │   │   ├── AppBar.vue
│   │   │   ├── Sidebar.vue
│   │   │   ├── Footer.vue
│   │   │   ├── LoadingSpinner.vue
│   │   │   └── ConfirmDialog.vue
│   │   ├── charts/
│   │   │   ├── PieChart.vue
│   │   │   ├── BarChart.vue
│   │   │   └── LineChart.vue
│   │   └── forms/
│   │       ├── TextInput.vue
│   │       ├── SelectInput.vue
│   │       └── DatePicker.vue
│   ├── layouts/
│   │   ├── DefaultLayout.vue
│   │   └── AuthLayout.vue
│   ├── views/
│   │   ├── auth/
│   │   │   ├── Login.vue
│   │   │   └── ForgotPassword.vue
│   │   ├── dashboard/
│   │   │   └── Dashboard.vue
│   │   ├── siswa/
│   │   │   ├── SiswaList.vue
│   │   │   ├── SiswaForm.vue
│   │   │   ├── SiswaDetail.vue
│   │   │   └── KehadiranForm.vue
│   │   ├── pegawai/
│   │   ├── keuangan/
│   │   ├── katering/
│   │   └── jemputan/
│   ├── stores/
│   │   ├── auth.js
│   │   ├── siswa.js
│   │   ├── pegawai.js
│   │   └── keuangan.js
│   ├── services/
│   │   ├── api.js
│   │   ├── siswa.service.js
│   │   ├── pegawai.service.js
│   │   └── keuangan.service.js
│   ├── router/
│   │   └── index.js
│   ├── plugins/
│   │   ├── vuetify.js
│   │   └── axios.js
│   ├── utils/
│   │   ├── formatters.js
│   │   ├── validators.js
│   │   └── constants.js
│   ├── App.vue
│   └── main.js
├── .env.development
├── .env.production
├── vite.config.js
├── package.json
└── README.md
```

### Step 5: Configure Vuetify

```javascript
// src/plugins/vuetify.js
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

const customTheme = {
  dark: false,
  colors: {
    primary: '#2196F3',
    secondary: '#424242',
    accent: '#82B1FF',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107',

    // Custom colors for finance app
    income: '#4CAF50',
    expense: '#F44336',
    background: '#F5F5F5',
  },
}

export default createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'customTheme',
    themes: {
      customTheme,
    },
  },
  defaults: {
    VBtn: {
      variant: 'flat',
      rounded: 'md',
    },
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
  },
})
```

### Step 6: Configure Router

```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { layout: 'auth', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/siswa',
    name: 'SiswaList',
    component: () => import('@/views/siswa/SiswaList.vue'),
    meta: { requiresAuth: true, permission: 'siswa.view' }
  },
  {
    path: '/siswa/create',
    name: 'SiswaCreate',
    component: () => import('@/views/siswa/SiswaForm.vue'),
    meta: { requiresAuth: true, permission: 'siswa.create' }
  },
  {
    path: '/siswa/:id',
    name: 'SiswaDetail',
    component: () => import('@/views/siswa/SiswaDetail.vue'),
    meta: { requiresAuth: true, permission: 'siswa.view' }
  },
  {
    path: '/siswa/:id/edit',
    name: 'SiswaEdit',
    component: () => import('@/views/siswa/SiswaForm.vue'),
    meta: { requiresAuth: true, permission: 'siswa.edit' }
  },
  // ... more routes
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.permission && !authStore.hasPermission(to.meta.permission)) {
    next({ name: 'NoPermission' })
  } else {
    next()
  }
})

export default router
```

### Step 7: Configure Pinia (State Management)

```javascript
// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const permissions = ref([])

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const userName = computed(() => user.value?.username || '')
  const userGroups = computed(() => user.value?.groups || [])

  // Actions
  async function login(credentials) {
    try {
      const response = await api.post('/api/auth/login/', credentials)

      token.value = response.data.access
      user.value = response.data.user
      permissions.value = response.data.permissions || []

      localStorage.setItem('token', token.value)

      return true
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  function logout() {
    token.value = null
    user.value = null
    permissions.value = []
    localStorage.removeItem('token')
  }

  function hasPermission(permission) {
    return permissions.value.includes(permission) || user.value?.is_superuser
  }

  async function fetchProfile() {
    try {
      const response = await api.get('/api/auth/profile/')
      user.value = response.data
    } catch (error) {
      console.error('Fetch profile error:', error)
      logout()
    }
  }

  return {
    user,
    token,
    permissions,
    isAuthenticated,
    userName,
    userGroups,
    login,
    logout,
    hasPermission,
    fetchProfile,
  }
})
```

### Step 8: Configure Axios

```javascript
// src/services/api.js
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()

    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push({ name: 'Login' })
    }

    return Promise.reject(error)
  }
)

export default api
```

### Step 9: Environment Variables

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Beesmartfinance

# .env.production
VITE_API_BASE_URL=https://api.beesmartfinance.com
VITE_APP_NAME=Beesmartfinance
```

### Step 10: Main Entry Point

```javascript
// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import './assets/styles/main.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

app.mount('#app')
```

---

## Architecture

### Component Hierarchy

```
App.vue
├── DefaultLayout.vue
│   ├── AppBar.vue
│   ├── Sidebar.vue
│   ├── router-view (Main Content)
│   └── Footer.vue
└── AuthLayout.vue
    └── router-view (Auth Pages)
```

### Layouts

```vue
<!-- src/layouts/DefaultLayout.vue -->
<template>
  <v-app>
    <app-bar @toggle-sidebar="drawer = !drawer" />

    <sidebar v-model="drawer" />

    <v-main>
      <v-container fluid class="pa-4">
        <router-view />
      </v-container>
    </v-main>

    <app-footer />

    <!-- Global components -->
    <loading-overlay v-if="loading" />
    <notification-snackbar />
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import AppBar from '@/components/common/AppBar.vue'
import Sidebar from '@/components/common/Sidebar.vue'
import AppFooter from '@/components/common/Footer.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import NotificationSnackbar from '@/components/common/NotificationSnackbar.vue'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'

const drawer = ref(true)
const appStore = useAppStore()
const { loading } = storeToRefs(appStore)
</script>
```

---

## Design System

> Sistem desain komprehensif untuk memastikan konsistensi visual dan pengalaman pengguna yang optimal pada dashboard keuangan TK Lebah Madu.

### 📐 Design Principles untuk Financial Admin Dashboard

#### 1. **Clarity First** (Kejelasan Utama)
- Data keuangan harus jelas dan mudah dipahami
- Hindari clutter dan informasi yang berlebihan
- Gunakan visualisasi data (charts) untuk insight cepat
- Hierarki informasi yang jelas (primary → secondary → tertiary)

#### 2. **Data-Driven Design**
- Angka dan data menjadi focal point
- Status keuangan harus terlihat dalam sekali pandang (at-a-glance)
- Gunakan color-coding untuk kategori keuangan (income/expense)
- Real-time update untuk data penting

#### 3. **Efficiency & Speed**
- Minimize clicks untuk task yang sering dilakukan
- Bulk actions untuk operasi massal
- Quick filters dan search yang powerful
- Keyboard shortcuts untuk power users

#### 4. **Trust & Reliability**
- Confirmation dialogs untuk aksi kritis (delete, payment)
- Audit trail yang jelas (who, when, what)
- Error prevention lebih baik dari error handling
- Consistent validation dan feedback

#### 5. **Responsive & Accessible**
- Mobile-first untuk monitoring di mana saja
- Touch-friendly untuk tablet usage
- Accessible untuk semua user (WCAG 2.1 AA)
- High contrast untuk readability

---

### 🎨 Design Tokens

Design tokens adalah foundation dari design system. Tokens ini memastikan konsistensi visual di seluruh aplikasi.

#### Color System

```javascript
// src/plugins/vuetify.js - Extended Color Palette
const designTokens = {
  colors: {
    // Primary Palette (Blue - Trust & Stability)
    primary: {
      50: '#E3F2FD',
      100: '#BBDEFB',
      200: '#90CAF9',
      300: '#64B5F6',
      400: '#42A5F5',
      500: '#2196F3',  // Main primary
      600: '#1E88E5',
      700: '#1976D2',
      800: '#1565C0',
      900: '#0D47A1',
    },

    // Financial Colors (Semantic)
    financial: {
      income: '#4CAF50',      // Green - Pemasukan
      expense: '#F44336',     // Red - Pengeluaran
      pending: '#FF9800',     // Orange - Pending
      paid: '#4CAF50',        // Green - Lunas
      overdue: '#F44336',     // Red - Terlambat
      partial: '#FFC107',     // Amber - Sebagian
    },

    // Status Colors
    status: {
      active: '#4CAF50',      // Green
      inactive: '#9E9E9E',    // Grey
      graduated: '#2196F3',   // Blue
      transferred: '#FF9800', // Orange
      suspended: '#F44336',   // Red
    },

    // Neutral Colors
    neutral: {
      50: '#FAFAFA',
      100: '#F5F5F5',
      200: '#EEEEEE',
      300: '#E0E0E0',
      400: '#BDBDBD',
      500: '#9E9E9E',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },

    // Semantic Colors
    semantic: {
      success: '#4CAF50',
      warning: '#FF9800',
      error: '#F44336',
      info: '#2196F3',
    },

    // Background Colors
    background: {
      default: '#F5F5F5',     // Light grey
      paper: '#FFFFFF',       // White
      elevated: '#FFFFFF',    // White with shadow
      dark: '#1E1E1E',        // Dark mode
    },

    // Text Colors
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.60)',
      disabled: 'rgba(0, 0, 0, 0.38)',
      hint: 'rgba(0, 0, 0, 0.38)',
      white: '#FFFFFF',
    },
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: designTokens.colors.primary[500],
          secondary: '#424242',
          accent: '#82B1FF',
          error: designTokens.colors.semantic.error,
          info: designTokens.colors.semantic.info,
          success: designTokens.colors.semantic.success,
          warning: designTokens.colors.semantic.warning,

          // Financial-specific colors
          income: designTokens.colors.financial.income,
          expense: designTokens.colors.financial.expense,
          pending: designTokens.colors.financial.pending,

          background: designTokens.colors.background.default,
          surface: designTokens.colors.background.paper,
        },
      },
      dark: {
        colors: {
          primary: designTokens.colors.primary[400],
          background: designTokens.colors.background.dark,
          // ... dark theme colors
        },
      },
    },
  },
})
```

#### Color Usage Guidelines

```vue
<!-- Financial Transaction Display -->
<template>
  <!-- ✅ GOOD - Semantic color for transaction type -->
  <v-chip
    :color="transaction.jenis === 'Masuk' ? 'income' : 'expense'"
    variant="flat"
  >
    {{ formatCurrency(transaction.jumlah) }}
  </v-chip>

  <!-- ✅ GOOD - Status color for payment status -->
  <v-chip
    :color="getPaymentStatusColor(payment.status)"
    size="small"
    label
  >
    {{ payment.status }}
  </v-chip>

  <!-- ❌ BAD - Hardcoded colors -->
  <v-chip color="#FF0000">Terlambat</v-chip>
</template>

<script setup>
function getPaymentStatusColor(status) {
  const colorMap = {
    'lunas': 'success',
    'belum_lunas': 'warning',
    'terlambat': 'error',
  }
  return colorMap[status] || 'grey'
}
</script>
```

---

#### Typography System

```javascript
// src/assets/styles/typography.scss
$font-family-base: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$font-family-monospace: 'Roboto Mono', 'Courier New', monospace;

// Type Scale (based on 1.25 ratio - Major Third)
$font-sizes: (
  'xs': 0.75rem,      // 12px - Labels, captions
  'sm': 0.875rem,     // 14px - Body small, helper text
  'base': 1rem,       // 16px - Body text
  'lg': 1.125rem,     // 18px - Subheadings
  'xl': 1.25rem,      // 20px - Card titles
  '2xl': 1.5rem,      // 24px - Section headings
  '3xl': 1.875rem,    // 30px - Page headings
  '4xl': 2.25rem,     // 36px - Dashboard title
  '5xl': 3rem,        // 48px - KPI numbers
);

// Font Weights
$font-weights: (
  'light': 300,
  'normal': 400,
  'medium': 500,
  'semibold': 600,
  'bold': 700,
);

// Line Heights
$line-heights: (
  'tight': 1.2,       // Headings
  'normal': 1.5,      // Body text
  'relaxed': 1.75,    // Long-form content
);

// Letter Spacing
$letter-spacings: (
  'tight': '-0.02em',
  'normal': '0',
  'wide': '0.025em',
  'wider': '0.05em',
);
```

**Usage in Components**:

```vue
<template>
  <div class="financial-card">
    <!-- Page Title -->
    <h1 class="text-3xl font-bold text-neutral-900">
      Dashboard Keuangan
    </h1>

    <!-- Section Heading -->
    <h2 class="text-2xl font-semibold text-neutral-800 mt-6">
      Ringkasan Bulan Ini
    </h2>

    <!-- Card Title -->
    <h3 class="text-xl font-medium text-neutral-700">
      Total Pemasukan
    </h3>

    <!-- KPI Numbers -->
    <p class="text-5xl font-bold text-income">
      {{ formatCurrency(totalIncome) }}
    </p>

    <!-- Body Text -->
    <p class="text-base text-neutral-600">
      Jumlah siswa aktif: {{ activeStudents }}
    </p>

    <!-- Helper Text -->
    <p class="text-sm text-neutral-500">
      Update terakhir: {{ lastUpdate }}
    </p>

    <!-- Caption / Labels -->
    <span class="text-xs uppercase tracking-wide text-neutral-400">
      Tahun Ajaran 2024/2025
    </span>
  </div>
</template>
```

---

#### Spacing System

```javascript
// src/assets/styles/spacing.scss
// 8pt Grid System (Base: 8px)
$spacing: (
  '0': 0,
  '1': 0.25rem,   // 4px  - Tight spacing
  '2': 0.5rem,    // 8px  - Base unit
  '3': 0.75rem,   // 12px - Small gaps
  '4': 1rem,      // 16px - Default spacing
  '5': 1.25rem,   // 20px
  '6': 1.5rem,    // 24px - Card padding
  '8': 2rem,      // 32px - Section spacing
  '10': 2.5rem,   // 40px
  '12': 3rem,     // 48px - Large gaps
  '16': 4rem,     // 64px - Hero spacing
  '20': 5rem,     // 80px
  '24': 6rem,     // 96px
);

// Container Widths
$containers: (
  'sm': 640px,
  'md': 768px,
  'lg': 1024px,
  'xl': 1280px,
  '2xl': 1536px,
);
```

**Spacing Guidelines**:

```vue
<template>
  <!-- ✅ GOOD - Consistent spacing -->
  <v-container fluid class="pa-6">
    <v-row class="mb-8">
      <v-col cols="12">
        <v-card class="pa-6">
          <v-card-title class="mb-4">Title</v-card-title>
          <v-card-text class="px-0">Content</v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>

  <!-- ❌ BAD - Arbitrary spacing -->
  <div style="padding: 13px; margin-bottom: 27px;">
    Content
  </div>
</template>
```

---

#### Elevation & Shadows

```javascript
// Design Tokens for Elevation
const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
}

// Vuetify Elevation Mapping
export default createVuetify({
  defaults: {
    VCard: {
      elevation: 2,  // Use 'base' shadow for cards
    },
    VMenu: {
      elevation: 4,  // Use 'md' shadow for menus
    },
    VDialog: {
      elevation: 8,  // Use 'lg' shadow for dialogs
    },
  },
})
```

---

#### Border Radius

```javascript
// Border Radius Tokens
const borderRadius = {
  none: '0',
  sm: '0.25rem',    // 4px  - Small elements (chips, badges)
  base: '0.375rem', // 6px  - Buttons, inputs
  md: '0.5rem',     // 8px  - Default cards
  lg: '0.75rem',    // 12px - Large cards, modals
  xl: '1rem',       // 16px - Hero sections
  '2xl': '1.5rem',  // 24px
  full: '9999px',   // Pills, avatars
}

// Vuetify Configuration
export default createVuetify({
  defaults: {
    VBtn: {
      rounded: 'md',  // 8px border radius
    },
    VCard: {
      rounded: 'lg',  // 12px border radius
    },
    VTextField: {
      rounded: 'md',
    },
    VChip: {
      rounded: 'sm',
    },
  },
})
```

---

### 🧩 Component Patterns

#### 1. **KPI Card Pattern** (Key Performance Indicators)

```vue
<!-- src/components/dashboard/KPICard.vue -->
<template>
  <v-card :color="color" dark class="kpi-card">
    <v-card-text>
      <div class="d-flex align-center justify-space-between">
        <div class="kpi-content">
          <!-- Label -->
          <div class="text-overline mb-1 opacity-80">
            {{ label }}
          </div>

          <!-- Value (Large Number) -->
          <div class="text-h3 font-weight-bold mb-2">
            {{ formattedValue }}
          </div>

          <!-- Trend Indicator -->
          <div class="d-flex align-center text-caption">
            <v-icon
              :icon="trend >= 0 ? 'mdi-trending-up' : 'mdi-trending-down'"
              size="small"
              class="mr-1"
            />
            <span>{{ Math.abs(trend) }}% dari bulan lalu</span>
          </div>
        </div>

        <!-- Icon -->
        <v-avatar size="72" color="rgba(255,255,255,0.2)">
          <v-icon :icon="icon" size="48" />
        </v-avatar>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  value: [Number, String],
  trend: Number,
  icon: String,
  color: {
    type: String,
    default: 'primary',
  },
  format: {
    type: String,
    default: 'number', // 'number', 'currency', 'percent'
  },
})

const formattedValue = computed(() => {
  if (props.format === 'currency') {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(props.value)
  } else if (props.format === 'percent') {
    return `${props.value}%`
  }
  return props.value.toLocaleString('id-ID')
})
</script>

<style scoped>
.kpi-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}
</style>

<!-- Usage -->
<!--
<k-p-i-card
  label="Total Pemasukan"
  :value="totalIncome"
  :trend="12.5"
  icon="mdi-trending-up"
  color="income"
  format="currency"
/>
-->
```

#### 2. **Transaction List Item Pattern**

```vue
<!-- src/components/keuangan/TransactionItem.vue -->
<template>
  <v-list-item class="transaction-item">
    <template v-slot:prepend>
      <v-avatar :color="avatarColor" size="48">
        <v-icon :icon="avatarIcon" size="24" color="white" />
      </v-avatar>
    </template>

    <v-list-item-title class="font-weight-medium">
      {{ transaction.deskripsi }}
    </v-list-item-title>

    <v-list-item-subtitle class="d-flex align-center mt-1">
      <v-icon icon="mdi-calendar" size="small" class="mr-1" />
      {{ formatDate(transaction.tanggal) }}
      <v-chip
        v-if="transaction.kategori"
        size="x-small"
        class="ml-2"
        variant="outlined"
      >
        {{ transaction.kategori }}
      </v-chip>
    </v-list-item-subtitle>

    <template v-slot:append>
      <div class="transaction-amount">
        <div
          :class="[
            'text-h6',
            'font-weight-bold',
            transaction.jenis === 'Masuk' ? 'text-income' : 'text-expense'
          ]"
        >
          {{ transaction.jenis === 'Masuk' ? '+' : '-' }}
          {{ formatCurrency(transaction.jumlah) }}
        </div>
      </div>
    </template>
  </v-list-item>
</template>

<script setup>
import { computed } from 'vue'
import { formatCurrency, formatDate } from '@/utils/formatters'

const props = defineProps({
  transaction: {
    type: Object,
    required: true,
  },
})

const avatarColor = computed(() =>
  props.transaction.jenis === 'Masuk' ? 'income' : 'expense'
)

const avatarIcon = computed(() =>
  props.transaction.jenis === 'Masuk' ? 'mdi-arrow-down' : 'mdi-arrow-up'
)
</script>

<style scoped>
.transaction-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: background-color 0.2s;
}

.transaction-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.transaction-amount {
  min-width: 140px;
  text-align: right;
}
</style>
```

#### 3. **Form Field Pattern dengan Validation**

```vue
<!-- src/components/forms/CurrencyInput.vue -->
<template>
  <v-text-field
    :model-value="displayValue"
    @update:model-value="handleInput"
    :label="label"
    :error-messages="errorMessages"
    :hint="hint"
    :persistent-hint="persistentHint"
    variant="outlined"
    density="comfortable"
    prepend-inner-icon="mdi-currency-usd"
    suffix="IDR"
    type="text"
    inputmode="numeric"
  >
    <template v-slot:prepend-inner>
      <span class="text-caption text-neutral-500">Rp</span>
    </template>
  </v-text-field>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: [Number, String],
  label: String,
  errorMessages: [String, Array],
  hint: String,
  persistentHint: Boolean,
})

const emit = defineEmits(['update:modelValue'])

const displayValue = computed(() => {
  if (!props.modelValue) return ''
  return Number(props.modelValue).toLocaleString('id-ID')
})

function handleInput(value) {
  // Remove formatting and convert to number
  const numericValue = value.replace(/\D/g, '')
  emit('update:modelValue', numericValue ? Number(numericValue) : null)
}
</script>
```

---

### 📱 Responsive Design Guidelines

#### Breakpoints

```javascript
// Vuetify Default Breakpoints (Mobile-First)
const breakpoints = {
  xs: 0,      // Extra small (phones, < 600px)
  sm: 600,    // Small (tablets, ≥ 600px)
  md: 960,    // Medium (small laptops, ≥ 960px)
  lg: 1264,   // Large (desktops, ≥ 1264px)
  xl: 1904,   // Extra large (large desktops, ≥ 1904px)
}
```

#### Responsive Layout Patterns

```vue
<template>
  <!-- KPI Grid: 1 col (mobile) → 2 cols (tablet) → 4 cols (desktop) -->
  <v-row>
    <v-col
      v-for="kpi in kpis"
      :key="kpi.id"
      cols="12"
      sm="6"
      md="3"
    >
      <k-p-i-card v-bind="kpi" />
    </v-col>
  </v-row>

  <!-- Chart Layout: Stack on mobile, side-by-side on desktop -->
  <v-row>
    <v-col cols="12" lg="8">
      <v-card>
        <line-chart :data="chartData" />
      </v-card>
    </v-col>
    <v-col cols="12" lg="4">
      <v-card>
        <pie-chart :data="pieData" />
      </v-card>
    </v-col>
  </v-row>

  <!-- Data Table: Responsive columns -->
  <v-data-table
    :headers="responsiveHeaders"
    :items="items"
    mobile-breakpoint="md"
  >
    <!-- Show fewer columns on mobile -->
    <template v-slot:item="{ item }">
      <tr>
        <td>{{ item.nama }}</td>
        <!-- Hide on mobile -->
        <td class="d-none d-md-table-cell">{{ item.kelompok }}</td>
        <td>{{ formatCurrency(item.spp) }}</td>
        <!-- Actions always visible -->
        <td>
          <v-btn icon size="small">
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
        </td>
      </tr>
    </template>
  </v-data-table>
</template>
```

---

### ♿ Accessibility Standards (WCAG 2.1 AA)

#### Color Contrast

```scss
// Minimum contrast ratios:
// - Normal text: 4.5:1
// - Large text (18pt+): 3:1
// - UI components: 3:1

// ✅ GOOD - High contrast
.primary-button {
  background: #2196F3;  // Primary blue
  color: #FFFFFF;       // White text (Contrast: 8.59:1)
}

// ✅ GOOD - Text on background
.text-primary {
  color: rgba(0, 0, 0, 0.87);  // Almost black
  background: #FFFFFF;          // White (Contrast: 14.8:1)
}

// ❌ BAD - Low contrast
.bad-contrast {
  color: #BDBDBD;      // Light grey
  background: #E0E0E0; // Lighter grey (Contrast: 1.5:1 - FAIL)
}
```

#### Keyboard Navigation

```vue
<template>
  <!-- ✅ GOOD - Keyboard accessible -->
  <v-list>
    <v-list-item
      v-for="item in items"
      :key="item.id"
      tabindex="0"
      @click="handleClick(item)"
      @keydown.enter="handleClick(item)"
      @keydown.space.prevent="handleClick(item)"
      role="button"
      :aria-label="`Select ${item.nama}`"
    >
      {{ item.nama }}
    </v-list-item>
  </v-list>

  <!-- ✅ GOOD - Form with labels -->
  <v-form>
    <v-text-field
      id="nis-input"
      v-model="formData.nis"
      label="NIS"
      aria-required="true"
      aria-describedby="nis-hint"
    />
    <span id="nis-hint" class="text-caption">
      Nomor Induk Siswa (6 digit)
    </span>
  </v-form>

  <!-- ✅ GOOD - Skip navigation -->
  <a href="#main-content" class="skip-link">
    Skip to main content
  </a>
</template>

<style>
/* Focus indicators */
*:focus-visible {
  outline: 2px solid #2196F3;
  outline-offset: 2px;
}

/* Skip link (hidden until focused) */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #2196F3;
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>
```

#### Screen Reader Support

```vue
<template>
  <!-- Live regions for dynamic content -->
  <div role="alert" aria-live="assertive" v-if="error">
    {{ error }}
  </div>

  <div role="status" aria-live="polite" v-if="successMessage">
    {{ successMessage }}
  </div>

  <!-- Loading state -->
  <div v-if="loading" role="status" aria-live="polite">
    <v-progress-circular indeterminate />
    <span class="sr-only">Memuat data...</span>
  </div>

  <!-- Complex widgets -->
  <v-data-table
    role="table"
    aria-label="Daftar siswa"
    :headers="headers"
    :items="items"
  >
    <template v-slot:item.actions="{ item }">
      <v-btn
        icon="mdi-pencil"
        size="small"
        :aria-label="`Edit ${item.nama}`"
        @click="editStudent(item)"
      />
      <v-btn
        icon="mdi-delete"
        size="small"
        :aria-label="`Hapus ${item.nama}`"
        @click="deleteStudent(item)"
      />
    </template>
  </v-data-table>
</template>

<style>
/* Screen reader only content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
```

---

### ✅ Visual Consistency Checklist

#### Component Consistency

- [ ] **Buttons**
  - Primary actions use `color="primary"` with `variant="flat"`
  - Secondary actions use `variant="outlined"` or `variant="text"`
  - Destructive actions use `color="error"`
  - Consistent sizing: `size="small"`, `size="default"`, `size="large"`

- [ ] **Cards**
  - All cards use `elevation="2"` (subtle shadow)
  - Padding: `class="pa-6"` (24px)
  - Border radius: `rounded="lg"` (12px)

- [ ] **Forms**
  - All inputs use `variant="outlined"`
  - Density: `density="comfortable"`
  - Required fields marked with asterisk (*)
  - Consistent validation messages

- [ ] **Tables**
  - Zebra striping for readability
  - Row hover state
  - Consistent action button placement (right column)
  - Loading skeleton while fetching data

- [ ] **Dialogs & Modals**
  - Max width: `max-width="600"` for forms
  - Max width: `max-width="900"` for detail views
  - Consistent action button layout (Cancel left, Confirm right)

- [ ] **Notifications**
  - Success: Green with check icon
  - Error: Red with alert icon
  - Warning: Orange with warning icon
  - Info: Blue with info icon
  - Position: Bottom-right or top-center
  - Auto-dismiss after 3-5 seconds

#### Financial Data Display

- [ ] **Currency Formatting**
  - Always use `Rp` prefix
  - Thousand separators: `.` (dot)
  - No decimal places for IDR
  - Example: `Rp 1.500.000`

- [ ] **Income/Expense Indicators**
  - Income: Green color with `+` prefix
  - Expense: Red color with `-` prefix
  - Use `mdi-arrow-down` for income
  - Use `mdi-arrow-up` for expense

- [ ] **Status Badges**
  - Lunas (Paid): Green chip
  - Pending: Orange chip
  - Terlambat (Overdue): Red chip
  - Consistent label placement

---

### 🎯 Implementation Checklist

When implementing new features, ensure:

- [ ] Colors use design tokens (no hardcoded hex values)
- [ ] Spacing follows 8pt grid system
- [ ] Typography uses predefined scale
- [ ] Components are responsive (test on mobile, tablet, desktop)
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes
- [ ] Color contrast meets WCAG AA (4.5:1 minimum)
- [ ] Focus indicators are visible
- [ ] Loading states are indicated
- [ ] Error states are clear and actionable
- [ ] Empty states provide guidance
- [ ] Consistent with existing patterns

---

## Component Migration

### Example 1: Student List Page

**BEFORE (Django Template + jQuery)**:

```django
<!-- templates/siswa/daftar.html -->
{% extends "backend/base.html" %}
{% load humanize %}

{% block content %}
<div class="card">
  <div class="card-header">
    <h3>Daftar Siswa</h3>
    <a href="{% url 'tambah_siswa' %}" class="btn btn-primary">
      <i class="fas fa-plus"></i> Tambah Siswa
    </a>
  </div>
  <div class="card-body">
    <table class="table table-striped">
      <thead>
        <tr>
          <th>NIS</th>
          <th>Nama</th>
          <th>Kelompok</th>
          <th>SPP</th>
          <th>Status</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        {% for siswa in siswa_list %}
        <tr>
          <td>{{ siswa.nis }}</td>
          <td>{{ siswa.nama }}</td>
          <td>{{ siswa.kelompok.nama }}</td>
          <td>Rp {{ siswa.spp|intcomma }}</td>
          <td>{{ siswa.status }}</td>
          <td>
            <a href="{% url 'edit_siswa' siswa.pk %}" class="btn btn-sm btn-primary">
              Edit
            </a>
            <a href="{% url 'hapus_siswa' siswa.pk %}" class="btn btn-sm btn-danger"
               onclick="return confirm('Yakin hapus?')">
              Hapus
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

**AFTER (Vue.js + Vuetify)**:

```vue
<!-- src/views/siswa/SiswaList.vue -->
<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span class="text-h5">Daftar Siswa</span>

            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="router.push({ name: 'SiswaCreate' })"
            >
              Tambah Siswa
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Filters -->
            <v-row class="mb-4">
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="search"
                  label="Cari siswa..."
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  density="compact"
                  clearable
                  hide-details
                />
              </v-col>

              <v-col cols="12" md="3">
                <v-select
                  v-model="filterStatus"
                  :items="statusOptions"
                  label="Status"
                  variant="outlined"
                  density="compact"
                  clearable
                  hide-details
                />
              </v-col>

              <v-col cols="12" md="3">
                <v-select
                  v-model="filterKelompok"
                  :items="kelompokOptions"
                  item-title="nama"
                  item-value="id"
                  label="Kelompok"
                  variant="outlined"
                  density="compact"
                  clearable
                  hide-details
                />
              </v-col>

              <v-col cols="12" md="2">
                <v-btn
                  color="primary"
                  variant="outlined"
                  block
                  @click="exportData"
                >
                  <v-icon left>mdi-download</v-icon>
                  Export
                </v-btn>
              </v-col>
            </v-row>

            <!-- Data Table -->
            <v-data-table
              :headers="headers"
              :items="filteredStudents"
              :loading="loading"
              :search="search"
              :items-per-page="25"
              class="elevation-1"
            >
              <!-- Custom slots -->
              <template v-slot:item.nis="{ item }">
                <router-link
                  :to="{ name: 'SiswaDetail', params: { id: item.id } }"
                  class="text-decoration-none"
                >
                  {{ item.nis }}
                </router-link>
              </template>

              <template v-slot:item.spp="{ item }">
                {{ formatCurrency(item.spp) }}
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip
                  :color="getStatusColor(item.status)"
                  size="small"
                  label
                >
                  {{ item.status }}
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon="mdi-pencil"
                  size="small"
                  variant="text"
                  color="primary"
                  @click="editStudent(item)"
                />
                <v-btn
                  icon="mdi-delete"
                  size="small"
                  variant="text"
                  color="error"
                  @click="confirmDelete(item)"
                />
              </template>

              <!-- Loading state -->
              <template v-slot:loading>
                <v-skeleton-loader type="table-row@10" />
              </template>

              <!-- No data state -->
              <template v-slot:no-data>
                <v-img
                  src="@/assets/img/empty-state.svg"
                  max-height="200"
                  contain
                  class="my-4"
                />
                <p class="text-center text-grey">
                  Belum ada data siswa
                </p>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title>Konfirmasi Hapus</v-card-title>
        <v-card-text>
          Apakah Anda yakin ingin menghapus siswa
          <strong>{{ selectedStudent?.nama }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">
            Batal
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="deleting"
            @click="deleteStudent"
          >
            Hapus
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSiswaStore } from '@/stores/siswa'
import { storeToRefs } from 'pinia'
import { formatCurrency } from '@/utils/formatters'

const router = useRouter()
const siswaStore = useSiswaStore()
const { students, loading } = storeToRefs(siswaStore)

// Filters
const search = ref('')
const filterStatus = ref(null)
const filterKelompok = ref(null)

// Dialog
const deleteDialog = ref(false)
const selectedStudent = ref(null)
const deleting = ref(false)

// Table headers
const headers = [
  { title: 'NIS', key: 'nis', sortable: true },
  { title: 'Nama', key: 'nama', sortable: true },
  { title: 'Kelompok', key: 'kelompok.nama', sortable: true },
  { title: 'SPP', key: 'spp', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Aksi', key: 'actions', sortable: false, align: 'center' },
]

// Options
const statusOptions = [
  { title: 'Aktif', value: 'aktif' },
  { title: 'Lulus', value: 'lulus' },
  { title: 'Cuti', value: 'cuti' },
  { title: 'Pindah', value: 'pindah' },
]

const kelompokOptions = computed(() => {
  // Get unique kelompok from students
  const kelompoks = students.value.map(s => s.kelompok).filter(Boolean)
  return [...new Map(kelompoks.map(k => [k.id, k])).values()]
})

// Computed
const filteredStudents = computed(() => {
  let result = students.value

  if (filterStatus.value) {
    result = result.filter(s => s.status === filterStatus.value)
  }

  if (filterKelompok.value) {
    result = result.filter(s => s.kelompok?.id === filterKelompok.value)
  }

  return result
})

// Methods
function getStatusColor(status) {
  const colors = {
    aktif: 'success',
    lulus: 'info',
    cuti: 'warning',
    pindah: 'error',
  }
  return colors[status] || 'grey'
}

function editStudent(student) {
  router.push({ name: 'SiswaEdit', params: { id: student.id } })
}

function confirmDelete(student) {
  selectedStudent.value = student
  deleteDialog.value = true
}

async function deleteStudent() {
  if (!selectedStudent.value) return

  deleting.value = true
  try {
    await siswaStore.deleteStudent(selectedStudent.value.id)
    deleteDialog.value = false
    selectedStudent.value = null
  } catch (error) {
    console.error('Delete error:', error)
  } finally {
    deleting.value = false
  }
}

async function exportData() {
  // Implement export functionality
  console.log('Exporting data...')
}

// Lifecycle
onMounted(async () => {
  await siswaStore.fetchStudents()
})
</script>

<style scoped>
.v-data-table :deep(th) {
  background-color: rgba(0, 0, 0, 0.03);
  font-weight: 600;
}
</style>
```

### Example 2: Dashboard with Charts

```vue
<!-- src/views/dashboard/Dashboard.vue -->
<template>
  <v-container fluid>
    <!-- KPI Cards -->
    <v-row>
      <v-col v-for="kpi in kpis" :key="kpi.id" cols="12" md="3">
        <v-card :color="kpi.color" dark>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-overline">{{ kpi.title }}</div>
                <div class="text-h4 mt-2">{{ kpi.value }}</div>
                <div class="text-caption mt-1">
                  <v-icon small>{{ kpi.trend > 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ Math.abs(kpi.trend) }}% dari bulan lalu
                </div>
              </div>
              <v-avatar size="60" color="rgba(255,255,255,0.2)">
                <v-icon size="40">{{ kpi.icon }}</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts -->
    <v-row class="mt-4">
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            Trend Keuangan
            <v-spacer />
            <v-btn-toggle v-model="chartPeriod" mandatory>
              <v-btn value="week" size="small">Minggu</v-btn>
              <v-btn value="month" size="small">Bulan</v-btn>
              <v-btn value="year" size="small">Tahun</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <line-chart :chart-data="chartData" :options="chartOptions" height="300" />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Distribusi Pengeluaran</v-card-title>
          <v-card-text>
            <pie-chart :chart-data="pieData" :options="pieOptions" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Transactions -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Transaksi Terbaru</v-card-title>
          <v-list>
            <v-list-item
              v-for="transaction in recentTransactions"
              :key="transaction.id"
            >
              <template v-slot:prepend>
                <v-avatar
                  :color="transaction.jenis === 'Masuk' ? 'success' : 'error'"
                >
                  <v-icon>
                    {{ transaction.jenis === 'Masuk' ? 'mdi-arrow-down' : 'mdi-arrow-up' }}
                  </v-icon>
                </v-avatar>
              </template>

              <v-list-item-title>{{ transaction.deskripsi }}</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(transaction.tanggal) }}</v-list-item-subtitle>

              <template v-slot:append>
                <div :class="transaction.jenis === 'Masuk' ? 'text-success' : 'text-error'">
                  {{ transaction.jenis === 'Masuk' ? '+' : '-' }}
                  {{ formatCurrency(transaction.jumlah) }}
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import LineChart from '@/components/charts/LineChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { storeToRefs } from 'pinia'
import { formatCurrency, formatDate } from '@/utils/formatters'

const dashboardStore = useDashboardStore()
const { kpis, chartData, pieData, recentTransactions } = storeToRefs(dashboardStore)

const chartPeriod = ref('month')

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}

const pieOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom',
    },
  },
}

onMounted(async () => {
  await dashboardStore.fetchDashboardData()
})
</script>
```

---

## State Management

### Pinia Store Structure

```javascript
// src/stores/siswa.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import siswaService from '@/services/siswa.service'
import { useNotificationStore } from './notification'

export const useSiswaStore = defineStore('siswa', () => {
  // State
  const students = ref([])
  const currentStudent = ref(null)
  const loading = ref(false)
  const filters = ref({
    status: null,
    kelompok: null,
    search: ''
  })

  // Getters
  const activeStudents = computed(() => 
    students.value.filter(s => s.status === 'aktif')
  )

  const studentCount = computed(() => ({
    total: students.value.length,
    aktif: students.value.filter(s => s.status === 'aktif').length,
    lulus: students.value.filter(s => s.status === 'lulus').length,
    cuti: students.value.filter(s => s.status === 'cuti').length,
  }))

  const filteredStudents = computed(() => {
    let result = students.value

    if (filters.value.status) {
      result = result.filter(s => s.status === filters.value.status)
    }

    if (filters.value.kelompok) {
      result = result.filter(s => s.kelompok?.id === filters.value.kelompok)
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(s => 
        s.nis.toLowerCase().includes(search) ||
        s.nama.toLowerCase().includes(search)
      )
    }

    return result
  })

  // Actions
  async function fetchStudents() {
    loading.value = true
    try {
      const response = await siswaService.getAll()
      students.value = response.data.results || response.data
    } catch (error) {
      console.error('Error fetching students:', error)
      useNotificationStore().error('Gagal memuat data siswa')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchStudent(id) {
    loading.value = true
    try {
      const response = await siswaService.getById(id)
      currentStudent.value = response.data
      return response.data
    } catch (error) {
      console.error('Error fetching student:', error)
      useNotificationStore().error('Gagal memuat data siswa')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createStudent(data) {
    loading.value = true
    try {
      const response = await siswaService.create(data)
      students.value.push(response.data)
      useNotificationStore().success('Siswa berhasil ditambahkan')
      return response.data
    } catch (error) {
      console.error('Error creating student:', error)
      useNotificationStore().error('Gagal menambahkan siswa')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateStudent(id, data) {
    loading.value = true
    try {
      const response = await siswaService.update(id, data)
      const index = students.value.findIndex(s => s.id === id)
      if (index !== -1) {
        students.value[index] = response.data
      }
      useNotificationStore().success('Data siswa berhasil diubah')
      return response.data
    } catch (error) {
      console.error('Error updating student:', error)
      useNotificationStore().error('Gagal mengubah data siswa')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteStudent(id) {
    loading.value = true
    try {
      await siswaService.delete(id)
      students.value = students.value.filter(s => s.id !== id)
      useNotificationStore().success('Siswa berhasil dihapus')
    } catch (error) {
      console.error('Error deleting student:', error)
      useNotificationStore().error('Gagal menghapus siswa')
      throw error
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function resetFilters() {
    filters.value = {
      status: null,
      kelompok: null,
      search: ''
    }
  }

  return {
    // State
    students,
    currentStudent,
    loading,
    filters,
    
    // Getters
    activeStudents,
    studentCount,
    filteredStudents,
    
    // Actions
    fetchStudents,
    fetchStudent,
    createStudent,
    updateStudent,
    deleteStudent,
    setFilters,
    resetFilters,
  }
})
```

### Notification Store (Global)

```javascript
// src/stores/notification.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const snackbar = ref(false)
  const message = ref('')
  const color = ref('success')
  const timeout = ref(3000)

  function show(msg, type = 'success', duration = 3000) {
    message.value = msg
    color.value = type
    timeout.value = duration
    snackbar.value = true
  }

  function success(msg) {
    show(msg, 'success')
  }

  function error(msg) {
    show(msg, 'error', 5000)
  }

  function warning(msg) {
    show(msg, 'warning')
  }

  function info(msg) {
    show(msg, 'info')
  }

  return {
    snackbar,
    message,
    color,
    timeout,
    show,
    success,
    error,
    warning,
    info,
  }
})
```

### App Store (Global State)

```javascript
// src/stores/app.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const drawer = ref(true)
  const breadcrumbs = ref([])

  function setLoading(value) {
    loading.value = value
  }

  function toggleDrawer() {
    drawer.value = !drawer.value
  }

  function setBreadcrumbs(items) {
    breadcrumbs.value = items
  }

  return {
    loading,
    drawer,
    breadcrumbs,
    setLoading,
    toggleDrawer,
    setBreadcrumbs,
  }
})
```

---

## API Integration

### Service Layer Pattern

```javascript
// src/services/api.js
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    // Show loading for non-GET requests
    if (config.method !== 'get') {
      const appStore = useAppStore()
      appStore.setLoading(true)
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    const appStore = useAppStore()
    appStore.setLoading(false)
    return response
  },
  (error) => {
    const appStore = useAppStore()
    appStore.setLoading(false)
    
    const notificationStore = useNotificationStore()
    
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - token expired or invalid
          const authStore = useAuthStore()
          authStore.logout()
          router.push({ name: 'Login' })
          notificationStore.error('Sesi Anda telah berakhir. Silakan login kembali.')
          break
          
        case 403:
          // Forbidden
          notificationStore.error('Anda tidak memiliki akses untuk melakukan aksi ini.')
          break
          
        case 404:
          // Not found
          notificationStore.error('Data tidak ditemukan.')
          break
          
        case 422:
          // Validation error
          const errors = error.response.data
          if (typeof errors === 'object') {
            const firstError = Object.values(errors)[0]
            notificationStore.error(Array.isArray(firstError) ? firstError[0] : firstError)
          }
          break
          
        case 500:
          // Server error
          notificationStore.error('Terjadi kesalahan pada server. Silakan coba lagi.')
          break
          
        default:
          notificationStore.error('Terjadi kesalahan. Silakan coba lagi.')
      }
    } else if (error.request) {
      // Network error
      notificationStore.error('Tidak dapat terhubung ke server. Periksa koneksi internet Anda.')
    }
    
    return Promise.reject(error)
  }
)

export default api
```

### Service for Siswa Module

```javascript
// src/services/siswa.service.js
import api from './api'

const ENDPOINT = '/api/siswa'

export default {
  /**
   * Get all students with optional filters
   */
  getAll(params = {}) {
    return api.get(ENDPOINT, { params })
  },

  /**
   * Get student by ID
   */
  getById(id) {
    return api.get(`${ENDPOINT}/${id}/`)
  },

  /**
   * Create new student
   */
  create(data) {
    return api.post(`${ENDPOINT}/`, data)
  },

  /**
   * Update student
   */
  update(id, data) {
    return api.put(`${ENDPOINT}/${id}/`, data)
  },

  /**
   * Partial update student
   */
  patch(id, data) {
    return api.patch(`${ENDPOINT}/${id}/`, data)
  },

  /**
   * Delete student
   */
  delete(id) {
    return api.delete(`${ENDPOINT}/${id}/`)
  },

  /**
   * Get student attendance records
   */
  getKehadiran(id, params = {}) {
    return api.get(`${ENDPOINT}/${id}/kehadiran/`, { params })
  },

  /**
   * Get student statistics
   */
  getStatistics() {
    return api.get(`${ENDPOINT}/statistics/`)
  },

  /**
   * Export students to CSV/Excel
   */
  export(format = 'csv') {
    return api.get(`${ENDPOINT}/export/`, {
      params: { format },
      responseType: 'blob'
    })
  },

  /**
   * Search students
   */
  search(query) {
    return api.get(`${ENDPOINT}/`, {
      params: { search: query }
    })
  },

  /**
   * Get students by kelompok
   */
  getByKelompok(kelompokId) {
    return api.get(`${ENDPOINT}/`, {
      params: { kelompok: kelompokId }
    })
  },

  /**
   * Get students by status
   */
  getByStatus(status) {
    return api.get(`${ENDPOINT}/`, {
      params: { status }
    })
  },
}
```

### Composable for API Calls (Advanced Pattern)

```javascript
// src/composables/useApi.js
import { ref } from 'vue'
import { useNotificationStore } from '@/stores/notification'

export function useApi(apiFunction) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const notificationStore = useNotificationStore()

  async function execute(...args) {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiFunction(...args)
      data.value = response.data
      return response.data
    } catch (err) {
      error.value = err
      console.error('API Error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    execute,
  }
}

// Usage in component
/*
<script setup>
import { useApi } from '@/composables/useApi'
import siswaService from '@/services/siswa.service'

const { data: students, loading, execute: fetchStudents } = useApi(siswaService.getAll)

onMounted(async () => {
  await fetchStudents()
})
</script>
*/
```

---

## UI/UX Improvements

### 1. Form Validation dengan VeeValidate

```vue
<!-- src/components/forms/SiswaForm.vue -->
<template>
  <v-form ref="formRef" @submit.prevent="handleSubmit">
    <v-container>
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.nis"
            label="NIS *"
            :error-messages="errors.nis"
            prepend-inner-icon="mdi-card-account-details"
            variant="outlined"
            required
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.nama"
            label="Nama Lengkap *"
            :error-messages="errors.nama"
            prepend-inner-icon="mdi-account"
            variant="outlined"
            required
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.tanggal_lahir"
            label="Tanggal Lahir"
            type="date"
            :error-messages="errors.tanggal_lahir"
            prepend-inner-icon="mdi-calendar"
            variant="outlined"
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-select
            v-model="formData.kelompok"
            :items="kelompokOptions"
            item-title="nama"
            item-value="id"
            label="Kelompok *"
            :error-messages="errors.kelompok"
            prepend-inner-icon="mdi-google-classroom"
            variant="outlined"
            required
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model.number="formData.spp"
            label="SPP (Rp) *"
            type="number"
            :error-messages="errors.spp"
            prepend-inner-icon="mdi-currency-usd"
            variant="outlined"
            required
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-select
            v-model="formData.status"
            :items="statusOptions"
            label="Status"
            :error-messages="errors.status"
            prepend-inner-icon="mdi-check-circle"
            variant="outlined"
          />
        </v-col>

        <v-col cols="12">
          <v-textarea
            v-model="formData.alamat"
            label="Alamat"
            :error-messages="errors.alamat"
            prepend-inner-icon="mdi-map-marker"
            variant="outlined"
            rows="3"
          />
        </v-col>

        <!-- Parent Information -->
        <v-col cols="12">
          <v-divider class="my-2" />
          <h3 class="text-h6 mb-4">Informasi Orang Tua</h3>
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.nama_ayah"
            label="Nama Ayah"
            :error-messages="errors.nama_ayah"
            prepend-inner-icon="mdi-account"
            variant="outlined"
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.kontak_ayah"
            label="Kontak Ayah"
            :error-messages="errors.kontak_ayah"
            prepend-inner-icon="mdi-phone"
            variant="outlined"
            placeholder="+628xxxxxxxxx"
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.nama_ibu"
            label="Nama Ibu"
            :error-messages="errors.nama_ibu"
            prepend-inner-icon="mdi-account"
            variant="outlined"
          />
        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
            v-model="formData.kontak_ibu"
            label="Kontak Ibu"
            :error-messages="errors.kontak_ibu"
            prepend-inner-icon="mdi-phone"
            variant="outlined"
            placeholder="+628xxxxxxxxx"
          />
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <v-row>
        <v-col cols="12" class="d-flex justify-end gap-2">
          <v-btn
            variant="outlined"
            @click="$router.back()"
          >
            Batal
          </v-btn>
          <v-btn
            type="submit"
            color="primary"
            :loading="loading"
          >
            <v-icon left>mdi-content-save</v-icon>
            Simpan
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-form>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { useSiswaStore } from '@/stores/siswa'

const router = useRouter()
const route = useRoute()
const siswaStore = useSiswaStore()

const loading = ref(false)
const isEdit = ref(false)
const studentId = ref(null)

// Validation schema
const schema = yup.object({
  nis: yup.string().required('NIS wajib diisi').matches(/^[0-9]+$/, 'NIS harus berupa angka'),
  nama: yup.string().required('Nama wajib diisi').min(3, 'Nama minimal 3 karakter'),
  kelompok: yup.number().required('Kelompok wajib dipilih'),
  spp: yup.number().required('SPP wajib diisi').min(0, 'SPP tidak boleh negatif'),
  kontak_ayah: yup.string().matches(/^(\+62|62|0)[0-9]{9,12}$/, 'Format nomor tidak valid').nullable(),
  kontak_ibu: yup.string().matches(/^(\+62|62|0)[0-9]{9,12}$/, 'Format nomor tidak valid').nullable(),
})

const { errors, handleSubmit, setValues } = useForm({
  validationSchema: schema,
})

const formData = reactive({
  nis: '',
  nama: '',
  tanggal_lahir: null,
  alamat: '',
  kelompok: null,
  periode: null,
  nama_ayah: '',
  kontak_ayah: '',
  nama_ibu: '',
  kontak_ibu: '',
  spp: 0,
  status: 'aktif',
})

const statusOptions = [
  { title: 'Aktif', value: 'aktif' },
  { title: 'Lulus', value: 'lulus' },
  { title: 'Cuti', value: 'cuti' },
  { title: 'Pindah', value: 'pindah' },
]

const kelompokOptions = ref([])

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    if (isEdit.value) {
      await siswaStore.updateStudent(studentId.value, values)
    } else {
      await siswaStore.createStudent(values)
    }
    router.push({ name: 'SiswaList' })
  } catch (error) {
    console.error('Error saving student:', error)
  } finally {
    loading.value = false
  }
})

onMounted(async () => {
  // Check if edit mode
  if (route.params.id) {
    isEdit.value = true
    studentId.value = route.params.id
    
    const student = await siswaStore.fetchStudent(studentId.value)
    setValues(student)
  }
  
  // Load kelompok options
  // await loadKelompokOptions()
})
</script>
```

### 2. Data Table dengan Advanced Features

```vue
<!-- src/components/common/DataTable.vue -->
<template>
  <v-card>
    <v-card-title v-if="title" class="d-flex justify-space-between align-center">
      <span>{{ title }}</span>
      <slot name="actions" />
    </v-card-title>

    <v-card-text>
      <!-- Filters -->
      <slot name="filters" />

      <!-- Table -->
      <v-data-table
        :headers="headers"
        :items="items"
        :loading="loading"
        :search="search"
        :items-per-page="itemsPerPage"
        :items-per-page-options="itemsPerPageOptions"
        class="elevation-1"
        @update:options="handleOptionsUpdate"
      >
        <!-- Custom slots forwarding -->
        <template
          v-for="(_, slot) in $slots"
          #[slot]="scope"
        >
          <slot :name="slot" v-bind="scope" />
        </template>

        <!-- Loading state -->
        <template #loading>
          <v-skeleton-loader
            type="table-row@10"
            class="mx-auto"
          />
        </template>

        <!-- No data state -->
        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="64" color="grey-lighten-1">
              mdi-database-off
            </v-icon>
            <p class="text-grey mt-2">{{ noDataText }}</p>
          </div>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: String,
  headers: {
    type: Array,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  loading: Boolean,
  search: String,
  itemsPerPage: {
    type: Number,
    default: 25,
  },
  noDataText: {
    type: String,
    default: 'Tidak ada data',
  },
})

const emit = defineEmits(['update:options'])

const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
  { value: -1, title: 'Semua' },
]

function handleOptionsUpdate(options) {
  emit('update:options', options)
}
</script>
```

### 3. Confirm Dialog Component

```vue
<!-- src/components/common/ConfirmDialog.vue -->
<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title class="text-h5">
        <v-icon :color="iconColor" class="mr-2">{{ icon }}</v-icon>
        {{ title }}
      </v-card-title>

      <v-card-text>
        {{ message }}
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="cancel"
        >
          {{ cancelText }}
        </v-btn>
        <v-btn
          :color="confirmColor"
          variant="flat"
          :loading="loading"
          @click="confirm"
        >
          {{ confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: 'Konfirmasi',
  },
  message: {
    type: String,
    required: true,
  },
  confirmText: {
    type: String,
    default: 'Ya',
  },
  cancelText: {
    type: String,
    default: 'Tidak',
  },
  confirmColor: {
    type: String,
    default: 'primary',
  },
  icon: {
    type: String,
    default: 'mdi-help-circle',
  },
  iconColor: {
    type: String,
    default: 'primary',
  },
})

const emit = defineEmits(['confirm', 'cancel'])

const dialog = ref(false)
const loading = ref(false)
const resolvePromise = ref(null)
const rejectPromise = ref(null)

function show() {
  dialog.value = true
  return new Promise((resolve, reject) => {
    resolvePromise.value = resolve
    rejectPromise.value = reject
  })
}

function confirm() {
  emit('confirm')
  if (resolvePromise.value) {
    resolvePromise.value(true)
  }
  dialog.value = false
}

function cancel() {
  emit('cancel')
  if (rejectPromise.value) {
    rejectPromise.value(false)
  }
  dialog.value = false
}

defineExpose({
  show,
})
</script>

<!-- Usage in parent component:
<template>
  <confirm-dialog
    ref="confirmDialog"
    title="Hapus Siswa"
    message="Apakah Anda yakin ingin menghapus siswa ini?"
    confirm-color="error"
    icon="mdi-delete"
    icon-color="error"
  />
</template>

<script setup>
const confirmDialog = ref(null)

async function deleteStudent(student) {
  try {
    await confirmDialog.value.show()
    // User confirmed, proceed with delete
    await siswaStore.deleteStudent(student.id)
  } catch {
    // User cancelled
  }
}
</script>
-->
```

### 4. Loading Overlay

```vue
<!-- src/components/common/LoadingOverlay.vue -->
<template>
  <v-overlay
    :model-value="loading"
    persistent
    class="align-center justify-center"
  >
    <v-progress-circular
      indeterminate
      size="64"
      color="primary"
    />
    <p class="text-white mt-4" v-if="message">{{ message }}</p>
  </v-overlay>
</template>

<script setup>
defineProps({
  loading: Boolean,
  message: String,
})
</script>
```

### 5. Empty State Component

```vue
<!-- src/components/common/EmptyState.vue -->
<template>
  <div class="text-center pa-8">
    <v-icon :size="iconSize" :color="iconColor">
      {{ icon }}
    </v-icon>
    <h3 class="text-h6 mt-4">{{ title }}</h3>
    <p class="text-grey mt-2">{{ description }}</p>
    
    <v-btn
      v-if="actionText"
      :color="actionColor"
      class="mt-4"
      @click="$emit('action')"
    >
      <v-icon left>{{ actionIcon }}</v-icon>
      {{ actionText }}
    </v-btn>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    default: 'mdi-inbox',
  },
  iconSize: {
    type: [String, Number],
    default: 64,
  },
  iconColor: {
    type: String,
    default: 'grey-lighten-1',
  },
  title: {
    type: String,
    default: 'Tidak ada data',
  },
  description: String,
  actionText: String,
  actionIcon: {
    type: String,
    default: 'mdi-plus',
  },
  actionColor: {
    type: String,
    default: 'primary',
  },
})

defineEmits(['action'])
</script>
```

---

## Migration Strategy

### Phased Migration Approach

#### **Phase 1: Parallel Development** (Recommended)

Develop Vue.js frontend in parallel with existing Django templates:

```
Project Structure:
beesmartfinance/
├── frontend/              # New Vue.js app
│   └── src/
│       ├── views/
│       └── components/
├── templates/             # Existing Django templates
│   └── backend/
└── static/
```

**Benefits**:
- Zero downtime
- Gradual migration
- Easy rollback
- User testing before full switch

**Implementation**:
1. Setup Vue.js project in `frontend/` directory
2. Develop API endpoints alongside existing views
3. Build Vue.js pages module by module
4. Test thoroughly before switching routes
5. Gradually redirect routes from Django templates to Vue.js SPA

#### **Phase 2: Module-by-Module Migration**

Migrate one module at a time:

```
Week 1-2: Setup & Dashboard
Week 3: Siswa Module
Week 4: Pegawai Module
Week 5: Keuangan Module
Week 6: Katering & Jemputan
Week 7: Testing & Polish
```

**For each module**:
1. ✅ Build API endpoint (if not exist)
2. ✅ Create Pinia store
3. ✅ Build service layer
4. ✅ Create Vue components
5. ✅ Test functionality
6. ✅ Update routing

#### **Phase 3: Feature Flags**

Use feature flags to toggle between old and new UI:

```python
# settings.py
FEATURE_FLAGS = {
    'use_vue_dashboard': config('FEATURE_USE_VUE_DASHBOARD', default=False, cast=bool),
    'use_vue_siswa': config('FEATURE_USE_VUE_SISWA', default=False, cast=bool),
    # ... other modules
}
```

```python
# core/views.py
def dashboard(request):
    if settings.FEATURE_FLAGS.get('use_vue_dashboard'):
        # Serve Vue.js SPA
        return render(request, 'vue_app.html')
    else:
        # Serve Django template
        return render(request, 'backend/dashboard.html', context)
```

### Data Migration Strategy

#### Handling Existing Data

Since moving from Django templates to Vue.js SPA, no database migration needed. Only route changes:

**Old Routes**:
```
/siswa/                    -> Django template
/siswa/tambah/             -> Django template
/siswa/edit/1/             -> Django template
```

**New Routes** (with API):
```
/                          -> Vue.js SPA (handles all routes client-side)
  └─ /siswa                -> Vue component
  └─ /siswa/create         -> Vue component
  └─ /siswa/1/edit         -> Vue component

/api/siswa/                -> DRF API (GET, POST)
/api/siswa/1/              -> DRF API (GET, PUT, PATCH, DELETE)
```

### Testing Strategy During Migration

```javascript
// Cypress E2E tests
describe('Siswa Module Migration', () => {
  it('should load student list', () => {
    cy.visit('/siswa')
    cy.get('[data-cy=student-table]').should('be.visible')
    cy.get('[data-cy=student-row]').should('have.length.gt', 0)
  })

  it('should create new student', () => {
    cy.visit('/siswa/create')
    cy.get('[data-cy=nis-input]').type('12345')
    cy.get('[data-cy=nama-input]').type('Test Student')
    cy.get('[data-cy=submit-btn]').click()
    cy.url().should('include', '/siswa')
    cy.contains('Test Student').should('be.visible')
  })

  it('should match data with old system', () => {
    // Compare data between Django template and Vue.js
    cy.request('/api/siswa/').then((response) => {
      const apiData = response.body.results
      cy.visit('/siswa')
      
      apiData.forEach((student) => {
        cy.contains(student.nama).should('be.visible')
      })
    })
  })
})
```

### Rollback Plan

In case of issues, rollback strategy:

```python
# settings.py - Easy rollback via environment variable
USE_VUE_FRONTEND = config('USE_VUE_FRONTEND', default=False, cast=bool)

# penelitian_tk/urls.py
if settings.USE_VUE_FRONTEND:
    # Serve Vue.js SPA for all routes except /api
    urlpatterns = [
        path('api/', include(api_router.urls)),
        re_path(r'^.*$', TemplateView.as_view(template_name='vue_app.html')),
    ]
else:
    # Use existing Django template routes
    urlpatterns = [
        path('', include('core.urls')),
        path('siswa/', include('siswa.urls')),
        # ... existing routes
    ]
```

To rollback: `USE_VUE_FRONTEND=False` in `.env` and restart server.

### Performance Monitoring

Track metrics before and after migration:

```javascript
// src/utils/analytics.js
export function trackPageLoad(pageName) {
  const loadTime = performance.now()
  console.log(`${pageName} loaded in ${loadTime}ms`)
  
  // Send to analytics service
  if (window.gtag) {
    gtag('event', 'timing_complete', {
      name: 'load',
      value: Math.round(loadTime),
      event_category: pageName
    })
  }
}

// Usage in component
onMounted(() => {
  trackPageLoad('SiswaList')
})
```

**Target Metrics**:
- Page load time: < 1s (vs 2-3s in Django templates)
- Time to interactive: < 1.5s
- API response time: < 200ms
- Bundle size: < 500KB (gzipped)

---

## Best Practices

### 1. Component Composition

Use composition over inheritance:

```vue
<script setup>
// ✅ GOOD - Composable
import { useStudentFilters } from '@/composables/useStudentFilters'
import { useDataTable } from '@/composables/useDataTable'

const { filters, applyFilters } = useStudentFilters()
const { items, loading, fetchItems } = useDataTable('siswa')
</script>
```

### 2. Code Splitting

Lazy load routes for better performance:

```javascript
// router/index.js
const routes = [
  {
    path: '/siswa',
    name: 'SiswaList',
    component: () => import('@/views/siswa/SiswaList.vue'), // Lazy loaded
  },
  {
    path: '/pegawai',
    name: 'PegawaiList',
    component: () => import('@/views/pegawai/PegawaiList.vue'),
  },
]
```

### 3. Environment Configuration

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Beesmartfinance Dev

# .env.production
VITE_API_BASE_URL=https://api.beesmartfinance.com
VITE_APP_NAME=Beesmartfinance
```

### 4. Error Boundaries

```vue
<!-- src/components/ErrorBoundary.vue -->
<template>
  <div v-if="error" class="error-boundary">
    <v-alert type="error">
      <h3>Terjadi kesalahan</h3>
      <p>{{ error.message }}</p>
      <v-btn @click="reset">Muat Ulang</v-btn>
    </v-alert>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const error = ref(null)

onErrorCaptured((err) => {
  error.value = err
  return false
})

function reset() {
  error.value = null
  window.location.reload()
}
</script>
```

### 5. Accessibility

```vue
<template>
  <!-- Add proper ARIA labels -->
  <v-btn
    aria-label="Tambah siswa baru"
    @click="createStudent"
  >
    <v-icon>mdi-plus</v-icon>
  </v-btn>

  <!-- Keyboard navigation -->
  <div
    role="button"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    {{ item.nama }}
  </div>

  <!-- Screen reader support -->
  <div role="alert" aria-live="polite" v-if="notification">
    {{ notification }}
  </div>
</template>
```

---

## Summary

### What We've Covered

1. ✅ **Project Setup** - Vite, Vuetify, Pinia, Vue Router
2. ✅ **Architecture** - Component hierarchy, layouts
3. ✅ **Component Migration** - Before/After examples (Student List, Dashboard, Forms)
4. ✅ **State Management** - Pinia stores for siswa, notifications, app state
5. ✅ **API Integration** - Axios setup, interceptors, service layer
6. ✅ **UI/UX Improvements** - Forms, data tables, dialogs, loading states
7. ✅ **Migration Strategy** - Phased approach, testing, rollback plan
8. ✅ **Best Practices** - Composition, code splitting, accessibility

### Key Benefits

| Aspect | Before (Django Templates) | After (Vue.js 3 + Vuetify) |
|--------|--------------------------|----------------------------|
| **User Experience** | Page reloads | No page reloads, instant feedback |
| **Performance** | ~2-3s load time | < 1s load time |
| **Interactivity** | Limited (jQuery) | Full reactive UI |
| **Mobile Support** | Basic responsive | Native-like PWA |
| **Development** | Tight coupling | Separation of concerns |
| **Scalability** | Monolith | Independent frontend/backend |

### Next Steps

1. **Start with Setup** (Week 1)
   - Create Vue.js project
   - Setup Vuetify, Pinia, Router
   - Configure Axios

2. **Dashboard First** (Week 2)
   - Migrate dashboard as proof of concept
   - Test performance improvements
   - Get user feedback

3. **Module by Module** (Week 3-6)
   - Siswa → Pegawai → Keuangan → Katering → Jemputan

4. **Testing & Deployment** (Week 7-8)
   - E2E testing
   - Performance optimization
   - Production deployment

**Estimated Timeline**: 8-10 weeks for complete migration

---

**Last Updated**: 2025-12-28
**Version**: 1.0.0

