"use client";

interface IdeaFiltersProps {
  pillars: string[];
  selectedPillar: string;
  onPillarChange: (pillar: string) => void;
  selectedStatus: string;
  onStatusChange: (status: string) => void;
  selectedSource: string;
  onSourceChange: (source: string) => void;
}

export function IdeaFilters({
  pillars,
  selectedPillar,
  onPillarChange,
  selectedStatus,
  onStatusChange,
  selectedSource,
  onSourceChange,
}: IdeaFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Pillar</label>
        <select
          value={selectedPillar}
          onChange={(e) => onPillarChange(e.target.value)}
          className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">All pillars</option>
          {pillars.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Status</label>
        <select
          value={selectedStatus}
          onChange={(e) => onStatusChange(e.target.value)}
          className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">All statuses</option>
          <option value="idea">Idea</option>
          <option value="converted">Converted</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Source</label>
        <select
          value={selectedSource}
          onChange={(e) => onSourceChange(e.target.value)}
          className="rounded-md border border-border bg-background px-2.5 py-1.5 text-xs shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">All sources</option>
          <option value="manual">Manual</option>
          <option value="whatsapp">WhatsApp</option>
        </select>
      </div>
    </div>
  );
}
