import { createApp } from "vue"
import PrimeVue from "primevue/config"
import { primevueLocale } from "@/core/primevueLocale"
import ToastService from "primevue/toastservice"
import ConfirmationService from "primevue/confirmationservice"
import { BeePreset } from "@/core/theme"
import "@/assets/main.css"
import "@/assets/primevue-overrides.css"
import DesignSystem from "./DesignSystem.vue"
import { cssVariables } from "./tokens"
import "./system.css"
for (const [name, value] of Object.entries(cssVariables)) document.documentElement.style.setProperty(name, value)
createApp(DesignSystem)
  .use(PrimeVue, { locale: primevueLocale, theme: { preset: BeePreset, options: { darkModeSelector: ".app-dark" } } })
  .use(ToastService).use(ConfirmationService).mount("#app")
