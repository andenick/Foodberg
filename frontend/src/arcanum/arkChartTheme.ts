// Arcanum Site Kit — arkChartTheme.ts (v1.1)
// Shared recharts theming from the kit `--ark-*` tokens (React/Vite stacks,
// e.g. Foodberg). Reads CSS vars at render time so charts follow the kit
// light/dark toggle; useArkTheme() re-reads on the `ark:themechange` event.
import { useEffect, useState } from "react";

export function tok(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name);
  return (v && v.trim()) || fallback;
}

export interface ArkChartTheme {
  fg: string; dim: string; line: string; accent: string; bgSoft: string;
  colorway: string[];
  gridStroke: string;
  axisStroke: string;
  tooltip: { backgroundColor: string; border: string; color: string; borderRadius: number };
}

export function arkChartTheme(): ArkChartTheme {
  const accent = tok("--ark-accent", "#ea580c");
  const line = tok("--ark-line", "#2a313b");
  return {
    fg: tok("--ark-fg", "#e7edf3"),
    dim: tok("--ark-fg-dim", "#9aa7b4"),
    line,
    accent,
    bgSoft: tok("--ark-bg-soft", "#161b22"),
    colorway: [accent, "#6b7280", "#0d9488", "#b8860b", "#7c4dff", "#dc2626", "#15803d", "#0891b2"],
    gridStroke: line,
    axisStroke: tok("--ark-fg-dim", "#9aa7b4"),
    tooltip: {
      backgroundColor: tok("--ark-bg-soft", "#161b22"),
      border: `1px solid ${line}`,
      color: tok("--ark-fg", "#e7edf3"),
      borderRadius: 8,
    },
  };
}

// Hook: returns the current theme, re-reading whenever the kit toggle fires.
export function useArkTheme(): ArkChartTheme {
  const [t, setT] = useState<ArkChartTheme>(() => arkChartTheme());
  useEffect(() => {
    const handler = () => setT(arkChartTheme());
    document.addEventListener("ark:themechange", handler);
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    mq?.addEventListener?.("change", handler);
    return () => {
      document.removeEventListener("ark:themechange", handler);
      mq?.removeEventListener?.("change", handler);
    };
  }, []);
  return t;
}

// Helper: CSV download from in-memory rows (no backend needed).
export function downloadCsv(rows: Record<string, unknown>[], filename: string): void {
  if (!rows?.length) return;
  const cols = Object.keys(rows[0]);
  const esc = (v: unknown) => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const csv = [cols.join(","), ...rows.map((r) => cols.map((c) => esc(r[c])).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = `${filename}.csv`;
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
}
