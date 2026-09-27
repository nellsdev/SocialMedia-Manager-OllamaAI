"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface TimeSeriesPoint {
  date: string;
  value: number;
}

interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  metric: string;
  color?: string;
}

const METRIC_COLORS: Record<string, string> = {
  followers: "#8b5cf6",
  likes: "#ec4899",
  comments: "#3b82f6",
  reach: "#10b981",
  engagement_rate: "#f59e0b",
  saves: "#06b6d4",
  shares: "#ef4444",
};

const METRIC_LABELS: Record<string, string> = {
  followers: "Followers",
  likes: "Likes",
  comments: "Comments",
  reach: "Reach",
  engagement_rate: "Engagement %",
  saves: "Saves",
  shares: "Shares",
};

export function TimeSeriesChart({ data, metric, color }: TimeSeriesChartProps) {
  const stroke = color || METRIC_COLORS[metric] || "#8b5cf6";
  const label = METRIC_LABELS[metric] || metric;

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border bg-card text-sm text-muted-foreground">
        No data yet — collecting more data for trends
      </div>
    );
  }

  const showNote = data.length < 7;

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{label} over time</h3>
        <span className="text-xs text-muted-foreground">{data.length} points</span>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string) => v.slice(5)}
              stroke="var(--muted-foreground)"
            />
            <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" width={48} />
            <Tooltip
              formatter={(value: number) => [value, label]}
              labelFormatter={(label: string) => `Date: ${label}`}
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={stroke}
              strokeWidth={2}
              dot={data.length <= 30}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {showNote && (
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Collecting more data for trends — {7 - data.length} more days needed for weekly view
        </p>
      )}
    </div>
  );
}
