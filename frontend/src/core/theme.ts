import { definePreset } from "@primeuix/themes"
import Aura from "@primeuix/themes/aura"
import { tokens } from "./designTokens"

const c = tokens.color
const status = {
  secondary: { background: c["neutral-tint"], color: c.muted },
  success: { background: c["positive-tint"], color: c.positive },
  warn: { background: c["warning-tint"], color: c.warning },
  danger: { background: c["critical-tint"], color: c.critical },
  info: { background: c["info-tint"], color: c.info },
}
const feedback = Object.fromEntries(Object.entries(status).map(([name, value]) =>
  [name === "danger" ? "error" : name, { ...value, borderColor: value.color, detailColor: c.ink, shadow: "none" }],
))

export const BeePreset = definePreset(Aura, {
  semantic: {
    transitionDuration: tokens.motion.control,
    primary: tokens.primary,
    focusRing: { width: "3px", style: "solid", color: c.focus, offset: "3px" },
    formField: { borderRadius: tokens.radius.control, paddingX: tokens.space[3], paddingY: tokens.space[3] },
    content: { borderRadius: tokens.radius.panel },
    overlay: { modal: { borderRadius: tokens.radius.overlay, padding: tokens.space[5], shadow: tokens.shadow.overlay } },
    colorScheme: { light: {
      primary: { color: c.brand, contrastColor: c.surface, hoverColor: c["brand-hover"], activeColor: c["brand-active"] },
      text: { color: c.ink, hoverColor: c.ink, mutedColor: c.muted, hoverMutedColor: c.ink },
      content: { background: c.surface, hoverBackground: c["surface-subtle"], borderColor: c.border, color: c.ink, hoverColor: c.ink },
      highlight: { background: c["brand-tint"], focusBackground: c.selection, color: c.brand, focusColor: c["brand-hover"] },
      formField: {
        background: c.surface, color: c.ink, borderColor: c["control-border"], hoverBorderColor: c.ink,
        focusBorderColor: c.focus, invalidBorderColor: c.critical, placeholderColor: c.muted,
        disabledBackground: c["disabled-bg"], disabledColor: c["disabled-text"], iconColor: c.muted,
      },
    } },
  },
  components: {
    button: {
      root: { borderRadius: tokens.radius.control, iconOnlyWidth: tokens.size.control },
      colorScheme: { light: { root: {
        secondary: { background: c.surface, hoverBackground: c["surface-subtle"], activeBackground: c["neutral-tint"], borderColor: c["control-border"], hoverBorderColor: c.ink, activeBorderColor: c.ink, color: c.ink, hoverColor: c.ink, activeColor: c.ink },
        ...Object.fromEntries(Object.entries(status).filter(([name]) => name !== "secondary").map(([name, value]) => [name, { background: value.color, hoverBackground: value.color, activeBackground: value.color, borderColor: value.color, hoverBorderColor: value.color, activeBorderColor: value.color, color: c.surface, hoverColor: c.surface, activeColor: c.surface }])),
      } } },
    },
    datatable: {
      headerCell: { background: c["surface-subtle"], color: c.muted, padding: `${tokens.space[4]} ${tokens.space[5]}` },
      bodyCell: { padding: `${tokens.space[4]} ${tokens.space[5]}`, sm: { padding: `${tokens.space[2]} ${tokens.space[5]}` } },
      row: { color: c.ink, hoverBackground: c["surface-subtle"] },
    },
    paginator: { navButton: { width: tokens.size.control, height: tokens.size.control, borderRadius: tokens.radius.control } },
    tag: { root: { fontSize: tokens.type.caption, fontWeight: tokens.weight.medium, borderRadius: tokens.radius.status }, colorScheme: { light: status } },
    message: { colorScheme: { light: feedback } },
    toast: { root: { width: "min(25rem, calc(100vw - 32px))" }, colorScheme: { light: feedback } },
  },
})
