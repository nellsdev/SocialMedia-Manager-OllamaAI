"use client";

import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string | number;
  delta?: number;
  trend?: "up" | "down" | "neutral";
  icon?: LucideIcon;
  subtitle?: string;
}

export function KpiCard({ title, value, delta, trend = "neutral", icon: Icon, subtitle }: KpiCardProps) {
  const showDelta = typeof delta === "number" && delta !== 0;
  const resolvedTrend =
    trend !== "neutral"
      ? trend
      : delta !== undefined
        ? delta > 0
          ? "up"
          : delta < 0
            ? "down"
            : "neutral"
        : "neutral";

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
        {Icon && <Icon size={16} className="text-muted-foreground" />}
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight">{value}</p>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
      <div className="mt-2 flex items-center gap-1 text-xs">
        {resolvedTrend === "up" && <TrendingUp size={14} className="text-emerald-500" />}
        {resolvedTrend === "down" && <TrendingDown size={14} className="text-red-500" />}
        {resolvedTrend === "neutral" && delta !== undefined && <Minus size={14} className="text-muted-foreground" />}
        {showDelta ? (
          <span className={resolvedTrend === "up" ? "text-emerald-600" : resolvedTrend === "down" ? "text-red-600" : "text-muted-foreground"}>
            {delta !== undefined && delta > 0 ? "+" : ""}
            {delta?.toFixed(1)}% vs prev
          </span>
        ) : delta !== undefined ? (
          <span className="text-muted-foreground">No change</span>
        ) : null}
      </div>
    </div>
  );
}
