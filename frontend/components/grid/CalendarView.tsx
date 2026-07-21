"use client";

import { useMemo } from "react";
import { PostCard } from "./PostCard";
import { DroppableDate } from "@/components/shared/DroppableDate";

interface Post {
  id: string;
  title?: string;
  format: string;
  status: string;
  scheduled_for?: string;
}

interface CalendarDay {
  date: string;
  posts: Post[];
}

interface CalendarViewProps {
  year: number;
  month: number;
  days: CalendarDay[];
  onDateClick?: (date: string) => void;
  onPostClick?: (postId: string) => void;
}

export function CalendarView({ year, month, days, onDateClick, onPostClick }: CalendarViewProps) {
  // Build a lookup map
  const dayMap = useMemo(() => {
    const map = new Map<string, Post[]>();
    for (const d of days) {
      map.set(d.date, d.posts);
    }
    return map;
  }, [days]);

  const firstDay = new Date(year, month - 1, 1);
  const startDayOfWeek = firstDay.getDay(); // 0=Sun
  const daysInMonth = new Date(year, month, 0).getDate();

  // Calendar grid: 6 weeks × 7 days
  const grid: (number | null)[][] = [];
  let day = 1;
  for (let w = 0; w < 6; w++) {
    const week: (number | null)[] = [];
    for (let d = 0; d < 7; d++) {
      if ((w === 0 && d < startDayOfWeek) || day > daysInMonth) {
        week.push(null);
      } else {
        week.push(day);
        day++;
      }
    }
    grid.push(week);
    if (day > daysInMonth) break;
  }

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  const formatDateStr = (d: number) =>
    `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;

  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header: day names */}
      <div className="grid grid-cols-7 border-b border-border">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((name) => (
          <div key={name} className="px-2 py-2 text-center text-xs font-medium text-muted-foreground">
            {name}
          </div>
        ))}
      </div>

      {/* Grid */}
      <div className="divide-y divide-border">
        {grid.map((week, wi) => (
          <div key={wi} className="grid grid-cols-7 divide-x divide-border">
            {week.map((d, di) => {
              if (d === null) {
                return <div key={`${wi}-${di}`} className="min-h-[100px] bg-muted/30" />;
              }
              const dateStr = formatDateStr(d);
              const isToday = dateStr === todayStr;
              const dayPosts = dayMap.get(dateStr) || [];

              return (
                <DroppableDate key={dateStr} date={dateStr} day={d} isToday={isToday}>
                  <div className="space-y-1" onClick={() => onDateClick?.(dateStr)}>
                    {dayPosts.slice(0, 3).map((post) => (
                      <PostCard
                        key={post.id}
                        title={post.title}
                        format={post.format}
                        status={post.status}
                        scheduledFor={post.scheduled_for}
                        onClick={() => onPostClick?.(post.id)}
                      />
                    ))}
                    {dayPosts.length > 3 && (
                      <div className="text-[10px] text-muted-foreground text-center">
                        +{dayPosts.length - 3} more
                      </div>
                    )}
                  </div>
                </DroppableDate>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
