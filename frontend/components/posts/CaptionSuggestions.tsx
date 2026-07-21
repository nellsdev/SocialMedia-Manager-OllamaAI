"use client";

import { getApi } from "@/lib/api";
import { Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

interface CaptionOption {
  text: string;
  tone?: string;
  length?: string;
  pillar?: string;
}

interface CaptionSuggestionsProps {
  postContext: string;
  onSelect: (caption: string) => void;
}

export function CaptionSuggestions({ postContext, onSelect }: CaptionSuggestionsProps) {
  const [options, setOptions] = useState<CaptionOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSuggest = async () => {
    if (!postContext.trim()) return;

    setLoading(true);
    setError("");
    setOptions([]);

    try {
      const api = getApi();
      const result = await api.suggestCaptions(postContext);
      setOptions(result.options || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate captions");
    } finally {
      setLoading(false);
    }
  };

  if (options.length === 0 && !loading) {
    return (
      <div>
        <button
          type="button"
          onClick={handleSuggest}
          disabled={!postContext.trim()}
          className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent disabled:opacity-50"
        >
          <Sparkles size={14} />
          Suggest Captions
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          AI Caption Suggestions
        </span>
        {!loading && (
          <button
            type="button"
            onClick={handleSuggest}
            className="text-xs text-primary hover:underline"
          >
            Regenerate
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 rounded-md border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
          <Loader2 size={14} className="animate-spin" />
          Generating captions...
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="space-y-2">
        {options.map((option, idx) => (
          <div
            key={idx}
            className="group relative rounded-md border border-border bg-background p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="flex-1 text-sm">{option.text}</p>
              <button
                type="button"
                onClick={() => onSelect(option.text)}
                className="shrink-0 rounded bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground opacity-0 transition-opacity group-hover:opacity-100"
              >
                Use This
              </button>
            </div>
            <div className="mt-1.5 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
              {option.tone && (
                <span className="rounded-full bg-secondary px-2 py-0.5 capitalize">
                  {option.tone}
                </span>
              )}
              {option.length && (
                <span className="rounded-full bg-secondary px-2 py-0.5">
                  {option.length}
                </span>
              )}
              {option.pillar && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary">
                  {option.pillar}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
