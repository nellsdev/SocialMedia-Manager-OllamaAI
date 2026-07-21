"use client";

interface IdeaCardProps {
  id: string;
  title: string;
  description?: string;
  suggestedFormat?: string;
  contentPillar?: string;
  source?: string;
  status?: string;
  onConvert?: (id: string) => void;
  draggable?: boolean;
}

const formatColors: Record<string, string> = {
  story: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400",
  carousel: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  reel: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  live: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

const pillarColors: Record<string, string> = {
  tips: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  educational: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  lifestyle: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
  promotional: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
};

export function IdeaCard({
  id,
  title,
  description,
  suggestedFormat,
  contentPillar,
  source,
  status,
  onConvert,
  draggable,
}: IdeaCardProps) {
  const formatClass = suggestedFormat ? formatColors[suggestedFormat] || "bg-gray-100" : "";
  const pillarClass = contentPillar ? pillarColors[contentPillar] || "bg-secondary text-secondary-foreground" : "";

  return (
    <div
      className={`rounded-lg border border-border bg-card p-3 transition-shadow hover:shadow-sm ${
        draggable ? "cursor-grab active:cursor-grabbing" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-foreground">{title}</h3>
        {status === "converted" && (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
            Converted
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{description}</p>
      )}

      <div className="mt-2 flex flex-wrap gap-1.5">
        {suggestedFormat && (
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${formatClass}`}>
            {suggestedFormat}
          </span>
        )}
        {contentPillar && (
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${pillarClass}`}>
            {contentPillar}
          </span>
        )}
        {source && source !== "manual" && (
          <span className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
            {source}
          </span>
        )}
      </div>

      {status === "idea" && onConvert && (
        <button
          onClick={() => onConvert(id)}
          className="mt-2 w-full rounded-md bg-primary/10 px-2 py-1.5 text-xs font-medium text-primary hover:bg-primary/20"
        >
          Convert to Post
        </button>
      )}
    </div>
  );
}
