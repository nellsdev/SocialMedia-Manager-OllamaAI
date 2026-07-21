"use client";

import { useDroppable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";

interface DroppableDateProps {
  date: string;
  day: number;
  isToday?: boolean;
  children: React.ReactNode;
}

export function DroppableDate({ date, day, isToday, children }: DroppableDateProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `date-${date}`,
    data: { type: "date", date },
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "min-h-[100px] rounded-lg border border-border p-2 transition-colors",
        isOver && "border-primary bg-primary/5",
        isToday && "border-primary/50"
      )}
    >
      <div
        className={cn(
          "mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium",
          isToday && "bg-primary text-primary-foreground"
        )}
      >
        {day}
      </div>
      {children}
    </div>
  );
}
