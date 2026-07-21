"use client";

import { useDraggable } from "@dnd-kit/core";
import { IdeaCard } from "@/components/ideas/IdeaCard";

interface DraggableIdeaProps {
  id: string;
  title: string;
  description?: string;
  suggestedFormat?: string;
  contentPillar?: string;
  source?: string;
  status?: string;
}

export function DraggableIdea({
  id,
  title,
  description,
  suggestedFormat,
  contentPillar,
  source,
  status,
}: DraggableIdeaProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `idea-${id}`,
    data: {
      type: "idea",
      idea: { id, title, description, suggestedFormat, contentPillar },
    },
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : undefined;

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <IdeaCard
        id={id}
        title={title}
        description={description}
        suggestedFormat={suggestedFormat}
        contentPillar={contentPillar}
        source={source}
        status={status}
        draggable
      />
    </div>
  );
}
