import type { ChartOptions } from "chart.js"
import { tokens } from "@/core/designTokens"

/** Brand palette — selaras --bee-* */
export const CHART = {
  navy: tokens.color['chart-ink'], magenta: tokens.color['chart-rose'], orange: tokens.color.warning,
  blue: tokens.color['chart-teal'], green: tokens.color.positive, cream: tokens.color['surface-subtle'],
  muted: tokens.color.muted, grid: tokens.color.border, tooltipBg: tokens.color.ink,
} as const
export const CHART_PALETTE = [CHART.navy, CHART.magenta, CHART.blue, tokens.color['chart-gold']]

const FONT = tokens.font.body

function basePlugins(showLegend = true) {
  return {
    legend: {
      display: showLegend,
      position: "bottom" as const,
      labels: {
        usePointStyle: true,
        pointStyle: "circle" as const,
        padding: 18,
        boxWidth: 8,
        boxHeight: 8,
        color: CHART.navy,
        font: { family: FONT, size: 13, weight: 600 as const },
      },
    },
    tooltip: {
      backgroundColor: CHART.tooltipBg,
      titleColor: "#fff",
      bodyColor: "rgba(255,255,255,0.92)",
      titleFont: { family: FONT, size: 13, weight: 700 as const },
      bodyFont: { family: FONT, size: 13 },
      padding: 12,
      cornerRadius: 10,
      displayColors: true,
      boxPadding: 6,
    },
  }
}

function axisTicks(isPercent = false) {
  return {
    color: CHART.muted,
    font: { family: FONT, size: 13 },
    padding: 6,
    callback: isPercent
      ? (v: string | number) => `${v}%`
      : (v: string | number) => {
          const n = Number(v)
          if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} jt`
          if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)} rb`
          return String(n)
        },
  }
}

function cartesianScales(yPercent = false) {
  return {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: { color: CHART.muted, font: { family: FONT, size: 13 } },
    },
    y: {
      grid: { color: CHART.grid, drawTicks: false },
      border: { display: false },
      beginAtZero: true,
      ticks: axisTicks(yPercent),
    },
  }
}

export function lineChartOptions(rpTooltip = false): ChartOptions<"line"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    animation: false,
    plugins: {
      ...basePlugins(true),
      tooltip: {
        ...basePlugins(true).tooltip,
        callbacks: rpTooltip
          ? {
              label: (ctx) => {
                const v = Number(ctx.parsed.y)
                return ` ${ctx.dataset.label}: Rp ${v.toLocaleString("id-ID")}`
              },
            }
          : undefined,
      },
    },
    scales: {
      x: cartesianScales(false).x,
      y: {
        ...cartesianScales(false).y,
        ticks: {
          ...axisTicks(false),
          callback: (v) => {
            const n = Number(v)
            if (Math.abs(n) >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)} M`
            if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(0)} jt`
            if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)} rb`
            return String(n)
          },
        },
      },
    },
    elements: {
      line: { tension: 0, borderWidth: 2.5 },
      point: { radius: 0, hoverRadius: 5, hitRadius: 12, borderWidth: 2 },
    },
  }
}

export function barChartOptions(opts?: { horizontal?: boolean; percent?: boolean; stacked?: boolean }): ChartOptions<"bar"> {
  const horizontal = opts?.horizontal ?? false
  const percent = opts?.percent ?? false
  const stacked = opts?.stacked ?? false

  if (horizontal) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      animation: false,
      plugins: { ...basePlugins(true), legend: { ...basePlugins(true).legend, display: true } },
      scales: {
        y: {
          grid: { display: false },
          border: { display: false },
          stacked,
          ticks: { color: CHART.muted, font: { family: FONT, size: 13 }, maxTicksLimit: 8 },
        },
        x: {
          stacked,
          grid: { color: CHART.grid, drawTicks: false },
          border: { display: false },
          beginAtZero: true,
          max: percent ? 110 : undefined,
          ticks: axisTicks(percent),
        },
      },
    }
  }

  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { ...basePlugins(!percent), legend: { display: percent ? false : true } },
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        stacked,
        ticks: { color: CHART.muted, font: { family: FONT, size: 13 }, maxTicksLimit: 12 },
      },
      y: {
        stacked,
        grid: { color: CHART.grid, drawTicks: false },
        border: { display: false },
        beginAtZero: true,
        max: percent ? 110 : undefined,
        ticks: axisTicks(percent),
      },
    },
  }
}

export function doughnutChartOptions(): ChartOptions<"doughnut"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "68%",
    spacing: 3,
    animation: false,
    plugins: {
      ...basePlugins(true),
      legend: {
        ...basePlugins(true).legend,
        position: "bottom",
        labels: {
          ...basePlugins(true).legend.labels,
          padding: 14,
        },
      },
    },
  }
}

export function sparkBarOptions(): ChartOptions<"bar"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: basePlugins(false).tooltip },
    scales: {
      x: { display: false },
      y: { display: false, beginAtZero: true },
    },
    animation: false,
  }
}

/** Warna bar dengan gradasi opacity berdasarkan nilai */
export function barColorByThreshold(
  value: number,
  thresholds: { warn: number; danger: number },
  colors: { ok: string; warn: string; danger: string },
) {
  if (value >= thresholds.danger) return colors.danger
  if (value >= thresholds.warn) return colors.warn
  return colors.ok
}
