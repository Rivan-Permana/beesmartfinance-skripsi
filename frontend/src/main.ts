import { Chart as ChartJS, registerables } from "chart.js"
import { createPinia } from "pinia"
import PrimeVue from "primevue/config"
import { primevueLocale } from "./core/primevueLocale"
import ConfirmationService from "primevue/confirmationservice"
import ToastService from "primevue/toastservice"
import { createApp } from "vue"

ChartJS.register(...registerables)

import App from "./App.vue"
import { BeePreset } from "./core/theme"
import { cssVariables } from "./core/designTokens"
import router from "./core/router"

import "primeicons/primeicons.css"
import "./assets/main.css"
import "./assets/primevue-overrides.css"

for (const [name, value] of Object.entries(cssVariables)) document.documentElement.style.setProperty(name, value)

const app = createApp(App)

// Logger error global utk runtime errors yg lolos ErrorBoundary.
app.config.errorHandler = (err, _instance, info) => {
  console.error("[App error]", info, err)
}
window.addEventListener("unhandledrejection", (event) => {
  console.error("[Unhandled promise]", event.reason)
})

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  locale: primevueLocale,
  theme: { preset: BeePreset, options: { darkModeSelector: ".app-dark" } },
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount("#app")
