import { createPinia } from "pinia"
import PrimeVue from "primevue/config"
import ConfirmationService from "primevue/confirmationservice"
import ToastService from "primevue/toastservice"
import { createApp } from "vue"

import App from "./App.vue"
import { BeePreset } from "./core/theme"
import router from "./core/router"

import "primeicons/primeicons.css"
import "./assets/main.css"

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: { preset: BeePreset, options: { darkModeSelector: ".app-dark" } },
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount("#app")
