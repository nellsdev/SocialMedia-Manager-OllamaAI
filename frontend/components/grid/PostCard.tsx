"use client";

interface PostCardProps {
  title?: string;
  format: string;
  status: string;
  pillarColor?: string;
  scheduledFor?: string;
  onClick?: () => void;
}

const statusColors: Record<string, string> = {
  draft: "bg-gray-400",
  scheduled: "bg-blue-500",
  published: "bg-green-500",
  failed: "bg-red-500",
};

const formatBadges: Record<string, string> = {
  story: "Story",
  carousel: "Crsl",
  reel: "Reel",
  live: "Live",
};

export function PostCard({ title, format, status, pillarColor, scheduledFor, onClick }: PostCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-md border border-border bg-card p-2 text-left text-xs transition-shadow hover:shadow-sm"
    >
      <div className="flex items-center gap-1.5">
        {pillarColor && (
          <span
            className="inline-block h-2 w-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: pillarColor }}
          />
        )}
        <span className="font-medium truncate flex-1">{title || "Untitled"}</span>
      </div>

      <div className="mt-1 flex items-center gap-1.5">
        <span className="inline-flex items-center rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
          {formatBadges[format] || format}
        </span>
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${statusColors[status] || "bg-gray-400"}`} />
        <span className="text-[10px] text-muted-foreground capitalize">{status}</span>
      </div>
    </button>
  );
}
