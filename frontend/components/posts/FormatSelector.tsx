"use client";

import { Film, Image, Play, Radio } from "lucide-react";

interface FormatSelectorProps {
  selected: string;
  onSelect: (format: string) => void;
}

const formats = [
  {
    id: "story",
    label: "Story",
    description: "9:16 image or video, 24h duration",
    icon: Image,
  },
  {
    id: "carousel",
    label: "Carousel",
    description: "2-10 images in a swipeable post",
    icon: Film,
  },
  {
    id: "reel",
    label: "Reel",
    description: "Vertical video, max 90s",
    icon: Play,
  },
  {
    id: "live",
    label: "Live",
    description: "Live broadcast announcement",
    icon: Radio,
  },
];

export function FormatSelector({ selected, onSelect }: FormatSelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {formats.map((fmt) => {
        const Icon = fmt.icon;
        const isSelected = selected === fmt.id;
        return (
          <button
            key={fmt.id}
            type="button"
            onClick={() => onSelect(fmt.id)}
            className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 text-center transition-all ${
              isSelected
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            }`}
          >
            <Icon
              size={24}
              className={isSelected ? "text-primary" : "text-muted-foreground"}
            />
            <div>
              <div className="text-sm font-semibold">{fmt.label}</div>
              <div className="text-xs text-muted-foreground">{fmt.description}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
