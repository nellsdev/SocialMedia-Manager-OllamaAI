"use client";

interface Archetype {
  id: string;
  name: string;
  description: string;
  default_tone: string;
  primary_metric: string;
  strategy_focus: string;
}

interface ArchetypeCardProps {
  archetype: Archetype;
  selected: boolean;
  onSelect: () => void;
}

export function ArchetypeCard({ archetype, selected, onSelect }: ArchetypeCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg border-2 p-4 text-left transition-all ${
        selected
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50"
      }`}
    >
      <h3 className="font-semibold text-foreground">{archetype.name}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{archetype.description}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
          {archetype.default_tone}
        </span>
        <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
          {archetype.primary_metric}
        </span>
      </div>
      {selected && (
        <p className="mt-2 text-xs text-primary">Selected</p>
      )}
    </button>
  );
}
