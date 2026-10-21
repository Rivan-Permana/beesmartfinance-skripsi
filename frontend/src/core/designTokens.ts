import tokens from "./design-tokens.json"

export { tokens }
export const cssVariables = Object.fromEntries(Object.entries(tokens).flatMap(([group, values]) =>
  Object.entries(values).map(([name, value]) => [`--bee-${group}-${name}`, String(value)]),
))

console.assert(tokens.primary[500] === tokens.color.brand && tokens.primary[600] === tokens.color["brand-hover"], "Primary palette must match semantic action colors")
