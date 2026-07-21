"use client";

import { useCallback, useEffect, useState } from "react";
import { getApi } from "@/lib/api";
import { CalendarView } from "@/components/grid/CalendarView";
import { DayDetail } from "@/components/grid/DayDetail";
import { PillarDonut } from "@/components/grid/PillarDonut";
import { FormatBalanceAlert } from "@/components/grid/FormatBalanceAlert";
import { DragProvider } from "@/components/shared/DragProvider";
import { DragEndEvent } from "@dnd-kit/core";

interface GridDay {
  date: string;
  posts: Array<{
    id: string;
    title?: string;
    format: string;
    status: string;
    scheduled_for?: string;
  }>;
}

interface DistributionData {
  pillars: Array<{ name: string; count: number; percentage: number }>;
  formats: Array<{ name: string; count: number; percentage: number }>;
  total_posts: number;
}

export default function ContentGridPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [days, setDays] = useState<GridDay[]>([]);
  const [distribution, setDistribution] = useState<DistributionData>({ pillars: [], formats: [], total_posts: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const api = getApi();
      const [gridData, distData] = await Promise.all([
        api.getGrid(year, month),
        api.getGridDistribution(),
      ]);
      setDays((gridData.days ?? []) as GridDay[]);
      setDistribution(distData as DistributionData);
    } catch {
      setDays([]);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const ideaId = (active.data.current as { idea?: { id?: string } } | undefined)?.idea?.id;
    const dateStr = (over.data.current as { date?: string } | undefined)?.date;
    if (!ideaId || !dateStr) return;

    try {
      const api = getApi();
      const { post_id } = await api.convertIdea(ideaId);
      // Navigate to the new post
      window.location.href = `/posts/${post_id}`;
    } catch (err) {
      console.error("Failed to convert idea via drag", err);
    }
  };

  const prevMonth = () => {
    if (month === 1) {
      setYear(year - 1);
      setMonth(12);
    } else {
      setMonth(month - 1);
    }
  };

  const nextMonth = () => {
    if (month === 12) {
      setYear(year + 1);
      setMonth(1);
    } else {
      setMonth(month + 1);
    }
  };

  const selectedDayPosts = selectedDate
    ? days.find((d) => d.date === selectedDate)?.posts || []
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Content Grid</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Plan your content calendar, view pillar distribution, and drag ideas into dates.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Calendar */}
        <div className="space-y-3">
          {/* Month navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={prevMonth}
              className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
            >
              ← Previous
            </button>
            <h2 className="text-lg font-semibold">
              {new Date(year, month - 1).toLocaleDateString("en-US", {
                month: "long",
                year: "numeric",
              })}
            </h2>
            <button
              onClick={nextMonth}
              className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
            >
              Next →
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-sm text-muted-foreground">Loading grid...</div>
          ) : (
            <DragProvider onDragEnd={handleDragEnd}>
              <CalendarView
                year={year}
                month={month}
                days={days}
                onDateClick={setSelectedDate}
                onPostClick={(postId) => {
                  window.location.href = `/posts/${postId}`;
                }}
              />
            </DragProvider>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-semibold mb-3">Pillar Distribution</h3>
            <PillarDonut data={distribution.pillars} />
          </div>

          <FormatBalanceAlert formats={distribution.formats} />

          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-semibold mb-2">Summary</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total posts</span>
                <span className="font-medium">{distribution.total_posts}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Formats used</span>
                <span className="font-medium">{distribution.formats.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Day detail modal */}
      {selectedDate && (
        <DayDetail
          date={selectedDate}
          posts={selectedDayPosts}
          onClose={() => setSelectedDate(null)}
          onPostClick={(postId) => {
            window.location.href = `/posts/${postId}`;
          }}
        />
      )}
    </div>
  );
}
