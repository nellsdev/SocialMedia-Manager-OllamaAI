"use client";

import { Users, Eye, Heart, MessageCircle, TrendingUp, Bookmark } from "lucide-react";

interface KpiData {
  followers: number;
  likes: number;
  comments: number;
  reach: number;
  engagement_rate: number;
  followers_delta: number;
  engagement_delta: number;
}

interface ArchetypeTopMetricsProps {
  archetype: string;
  kpis: KpiData;
}

function archetypeConfig(archetype: string): { title: string; metrics: Array<{ key: keyof KpiData; label: string; icon: typeof Users; highlight?: boolean }> } {
  switch (archetype) {
    case "aspiring_influencer":
      return {
        title: "Growth focus — followers + reach lead",
        metrics: [
          { key: "followers", label: "Followers", icon: Users, highlight: true },
          { key: "reach", label: "Reach", icon: Eye, highlight: true },
          { key: "engagement_rate", label: "Engagement", icon: TrendingUp },
        ],
      };
    case "authority_professional":
      return {
        title: "Quality focus — engagement & conversations",
        metrics: [
          { key: "engagement_rate", label: "Engagement Rate", icon: TrendingUp, highlight: true },
          { key: "comments", label: "Comments", icon: MessageCircle, highlight: true },
          { key: "likes", label: "Likes", icon: Heart },
        ],
      };
    case "business_owner":
      return {
        title: "Impact focus — reach + engagement",
        metrics: [
          { key: "reach", label: "Reach", icon: Eye, highlight: true },
          { key: "engagement_rate", label: "Engagement", icon: TrendingUp, highlight: true },
          { key: "followers", label: "Followers", icon: Users },
        ],
      };
    case "community_builder":
      return {
        title: "Community focus — participation",
        metrics: [
          { key: "comments", label: "Comments", icon: MessageCircle, highlight: true },
          { key: "engagement_rate", label: "Engagement", icon: TrendingUp, highlight: true },
          { key: "reach", label: "Reach", icon: Eye },
        ],
      };
    case "personal_sharing":
    default:
      return {
        title: "Connection focus — interactions",
        metrics: [
          { key: "comments", label: "Comments", icon: MessageCircle, highlight: true },
          { key: "likes", label: "Likes", icon: Heart, highlight: true },
          { key: "reach", label: "Reach", icon: Eye },
        ],
      };
  }
}

function formatValue(key: keyof KpiData, value: number): string {
  if (key === "engagement_rate") return `${value.toFixed(2)}%`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return String(value);
}

export function ArchetypeTopMetrics({ archetype, kpis }: ArchetypeTopMetricsProps) {
  const config = archetypeConfig(archetype);

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">{config.title}</p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {config.metrics.map(({ key, label, icon: Icon, highlight }) => (
          <div
            key={key}
            className={`rounded-lg border p-3 ${highlight ? "border-primary/30 bg-primary/5" : "border-border bg-background"}`}
          >
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Icon size={14} />
              <span>{label}</span>
              {highlight && <span className="ml-auto rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">TOP</span>}
            </div>
            <p className={`mt-1 text-xl font-bold ${highlight ? "text-primary" : ""}`}>{formatValue(key, kpis[key] as number)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
