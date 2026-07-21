"use client";

import { getApi } from "@/lib/api";
import { Hash, Loader2, Plus } from "lucide-react";
import { useState } from "react";

interface HashtagSuggestionsProps {
  caption: string;
  pillars?: string[];
  onAdd: (hashtag: string) => void;
  existingHashtags?: string[];
}

export function HashtagSuggestions({
  caption,
  pillars,
  onAdd,
  existingHashtags = [],
}: HashtagSuggestionsProps) {
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSuggest = async () => {
    if (!caption.trim()) return;

    setLoading(true);
    setError("");
    setHashtags([]);

    try {
      const api = getApi();
      const result = await api.suggestHashtags(caption, pillars);
      setHashtags(result.hashtags || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate hashtags");
    } finally {
      setLoading(false);
    }
  };

  if (hashtags.length === 0 && !loading) {
    return (
      <div>
        <button
          type="button"
          onClick={handleSuggest}
          disabled={!caption.trim()}
          className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent disabled:opacity-50"
        >
          <Hash size={14} />
          Suggest Hashtags
        </button>
      </div>
    );
  }

  const isAdded = (tag: string) =>
    existingHashtags.some((h) => h.toLowerCase() === tag.toLowerCase());

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          AI Hashtag Suggestions
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
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 size={14} className="animate-spin" />
          Generating hashtags...
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {hashtags.map((tag, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => !isAdded(tag) && onAdd(tag)}
            disabled={isAdded(tag)}
            className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm transition-all ${
              isAdded(tag)
                ? "bg-primary/20 text-primary/60 line-through"
                : "bg-secondary text-secondary-foreground hover:bg-primary/20 hover:text-primary"
            }`}
          >
            <span>#{tag}</span>
            {!isAdded(tag) && <Plus size={12} />}
          </button>
        ))}
      </div>

      {hashtags.length > 0 && (
        <p className="text-[11px] text-muted-foreground">
          Click a tag to add it to your post. Added tags are crossed out.
        </p>
      )}
    </div>
  );
}
