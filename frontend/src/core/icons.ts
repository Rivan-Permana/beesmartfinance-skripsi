// Keep existing icon props working while each module moves to Phosphor names.
const legacy: Record<string, string> = {
  "angle-left": "caret-left", "angle-right": "caret-right", apple: "fork-knife",
  "arrow-down-left": "arrow-down-left", "arrow-left": "arrow-left", "arrow-right": "arrow-right", "arrow-up-right": "arrow-up-right",
  bars: "list", bolt: "lightning", book: "book-open", box: "cube", calendar: "calendar-blank", "calendar-plus": "calendar-plus", car: "van",
  "chart-bar": "chart-bar", "chart-line": "chart-line", "chart-pie": "chart-pie", check: "check", "check-circle": "check-circle",
  "chevron-left": "caret-left", "chevron-right": "caret-right", "credit-card": "credit-card", download: "download",
  "exclamation-circle": "warning-circle", "exclamation-triangle": "warning", eye: "eye", file: "file-text", "file-export": "file-arrow-up",
  filter: "funnel", flag: "flag", history: "clock", "id-card": "identification-card", image: "image", inbox: "tray", lock: "lock",
  "money-bill": "money", pencil: "pencil-simple", percentage: "percent", plus: "plus", print: "printer", receipt: "file-text",
  refresh: "arrows-clockwise", save: "floppy-disk", search: "magnifying-glass", "sign-out": "sign-out", sitemap: "tree-structure",
  "sliders-h": "sliders-horizontal", "th-large": "squares-four", times: "x", "times-circle": "x-circle", trash: "trash", "user-plus": "user-plus", users: "users", wallet: "wallet",
}

export function resolveIcon(name: string): string {
  return name.startsWith("pi pi-") ? legacy[name.slice(6)] ?? "warning-circle" : name
}

console.assert(resolveIcon("pi pi-search") === "magnifying-glass" && resolveIcon("wallet") === "wallet", "Icon aliases must preserve both callers")
