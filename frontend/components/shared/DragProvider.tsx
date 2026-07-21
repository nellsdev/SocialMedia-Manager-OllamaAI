"use client";

import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { useState } from "react";

interface DragProviderProps {
  children: React.ReactNode;
  onDragEnd?: (event: DragEndEvent) => void;
}

export function DragProvider({ children, onDragEnd }: DragProviderProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveId(null);
    onDragEnd?.(event);
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      {children}
      <DragOverlay>
        {activeId ? (
          <div className="rounded-lg border-2 border-primary bg-card p-3 shadow-lg opacity-90">
            <span className="text-sm font-medium">Dragging...</span>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
