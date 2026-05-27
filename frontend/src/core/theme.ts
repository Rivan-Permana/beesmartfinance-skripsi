import { definePreset } from "@primeuix/themes"
import Aura from "@primeuix/themes/aura"

// Preset brand "Lebah Madu": primary = magenta khas sekolah.
// Warna oranye/navy dipakai sebagai aksen lewat CSS variabel (lihat main.css).
export const BeePreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: "#fdeaf4",
      100: "#fbcfe4",
      200: "#f7a0c9",
      300: "#f06ba9",
      400: "#ec3f8f",
      500: "#e5197f", // magenta brand
      600: "#c4116b",
      700: "#9c0d55",
      800: "#7a0b43",
      900: "#5f0a36",
      950: "#3a0420",
    },
  },
})
