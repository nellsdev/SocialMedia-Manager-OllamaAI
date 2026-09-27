"use client";

import { useEffect, useState, useCallback } from "react";
import { Users, Heart, MessageCircle, Eye, TrendingUp, BarChart3 } from "lucide-react";
import { getApi } from "@/lib/api";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { TimeSeriesChart } from "@/components/dashboard/TimeSeriesChart";
import { ArchetypeTopMetrics } from "@/components/dashboard/ArchetypeTopMetrics";

interface KpiData {
  followers: number;
  likes: number;
  comments: number;
  reach: number;
  engagement_rate: number;
  followers_delta: number;
  engagement_delta: number;
}

type MetricOption = "followers" | "likes" | "comments" | "reach" | "engagement_rate";

const METRIC_OPTIONS: Array<{ value: MetricOption; label: string }> = [
  { value: "followers", label: "Followers" },
  { value: "likes", label: "Likes" },
  { value: "comments", label: "Comments" },
  { value: "reach", label: "Reach" },
  { value: "engagement_rate", label: "Engagement %" },
];

const DAYS_OPTIONS = [7, 30, 90] as const;

function formatKpiValue(key: keyof KpiData, value: number): string {
  if (key === "engagement_rate") return `${value.toFixed(2)}%`;
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return String(value);
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KpiData | null>(null);
  const [kpisLoading, setKpisLoading] = useState(true);
  const [kpisError, setKpisError] = useState("");

  const [archetype, setArchetype] = useState<string>("personal_sharing");

  const [metric, setMetric] = useState<MetricOption>("followers");
  const [days, setDays] = useState<number>(30);
  const [series, setSeries] = useState<Array<{ date: string; value: number }>>([]);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [seriesError, setSeriesError] = useState("");

  const fetchKpis = useCallback(async () => {
    setKpisLoading(true);
    setKpisError("");
    try {
      const api = getApi();
      const data = await api.getDashboardKpis();
      setKpis(data as unknown as KpiData);
      // Fetch archetype from profile
      try {
        const profile = (await api.getMyProfile()) as unknown as { archetype?: string };
        if (profile?.archetype) setArchetype(profile.archetype);
      } catch {
        // keep default archetype
      }
    } catch (err: unknown) {
      setKpisError(err instanceof Error ? err.message : "Failed to load KPIs");
    } finally {
      setKpisLoading(false);
    }
  }, []);

  const fetchSeries = useCallback(async (m: MetricOption, d: number) => {
    setSeriesLoading(true);
    setSeriesError("");
    try {
      const api = getApi();
      const res = await api.getDashboardTimeseries(m, d);
      setSeries(res.data || []);
    } catch (err: unknown) {
      setSeriesError(err instanceof Error ? err.message : "Failed to load chart");
    } finally {
      setSeriesLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKpis();
  }, [fetchKpis]);

  useEffect(() => {
    fetchSeries(metric, days);
  }, [metric, days, fetchSeries]);

  const isEmpty = kpis && kpis.followers === 0 && kpis.likes === 0 && kpis.comments === 0 && kpis.reach === 0;

  if (kpisLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Loading metrics...</p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-lg border border-border bg-muted/30" />
          ))}
        </div>
      </div>
    );
  }

  if (kpisError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-900/20 dark:text-red-300">
          {kpisError}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Performance overview — archetype-aware</p>
      </div>

      {isEmpty ? (
        <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center">
          <div className="mx-auto flex max-w-md flex-col items-center gap-3">
            <div className="rounded-full bg-primary/10 p-3">
              <BarChart3 className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold">No metrics yet</h3>
            <p className="text-sm text-muted-foreground">Publish your first post to see metrics</p>
          </div>
        </div>
      ) : (
        kpis && (
          <>
            {/* Archetype-adaptive top metrics */}
            <ArchetypeTopMetrics archetype={archetype} kpis={kpis} />

            {/* KPI cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiCard
                title="Followers"
                value={formatKpiValue("followers", kpis.followers)}
                delta={kpis.followers_delta}
                icon={Users}
              />
              <KpiCard
                title="Likes"
                value={formatKpiValue("likes", kpis.likes)}
                icon={Heart}
              />
              <KpiCard
                title="Comments"
                value={formatKpiValue("comments", kpis.comments)}
                icon={MessageCircle}
              />
              <KpiCard
                title="Reach"
                value={formatKpiValue("reach", kpis.reach)}
                icon={Eye}
              />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <KpiCard
                title="Engagement Rate"
                value={formatKpiValue("engagement_rate", kpis.engagement_rate)}
                delta={kpis.engagement_delta}
                icon={TrendingUp}
              />
            </div>
          </>
        )
      )}

      {/* Chart controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted-foreground">Metric</label>
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value as MetricOption)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
          >
            {METRIC_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted-foreground">Range</label>
          <div className="flex rounded-md border border-border">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-xs font-medium first:rounded-l-md last:rounded-r-md ${
                  days === d ? "bg-primary text-primary-foreground" : "bg-background hover:bg-accent"
                }`}
              >
                {d}D
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      {seriesLoading ? (
        <div className="h-64 animate-pulse rounded-lg border border-border bg-muted/30" />
      ) : seriesError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-900/20 dark:text-red-300">
          {seriesError}
        </div>
      ) : (
        <TimeSeriesChart data={series} metric={metric} />
      )}
    </div>
  );
}
