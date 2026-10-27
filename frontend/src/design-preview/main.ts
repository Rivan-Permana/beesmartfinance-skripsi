import { createApp } from "vue"
import PrimeVue from "primevue/config"
import PreviewApp from "./PreviewApp.vue"
import "./preview.css"
import "./workspace-theme.css"
import "./workflow-preview.css"

// Entry terpisah: tanpa auth store, router aplikasi, API, atau operasi penyimpanan.
createApp(PreviewApp).use(PrimeVue, { unstyled: true }).mount("#app")
