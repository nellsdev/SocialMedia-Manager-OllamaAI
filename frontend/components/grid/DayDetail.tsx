"use client";

import { X } from "lucide-react";

interface Post {
  id: string;
  title?: string;
  format: string;
  status: string;
  caption?: string;
  scheduled_for?: string;
}

interface DayDetailProps {
  date: string;
  posts: Post[];
  onClose: () => void;
  onPostClick?: (postId: string) => void;
}

const formatLabels: Record<string, string> = {
  story: "Story",
  carousel: "Carousel",
  reel: "Reel",
  live: "Live",
};

export function DayDetail({ date, posts, onClose, onPostClick }: DayDetailProps) {
  const formattedDate = new Date(date + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-lg bg-card p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">{formattedDate}</h2>
            <p className="text-sm text-muted-foreground">
              {posts.length} {posts.length === 1 ? "post" : "posts"}
            </p>
          </div>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X size={18} />
          </button>
        </div>

        {posts.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No posts scheduled for this day.
          </div>
        ) : (
          <div className="space-y-2">
            {posts.map((post) => (
              <button
                key={post.id}
                onClick={() => {
                  onPostClick?.(post.id);
                  onClose();
                }}
                className="w-full rounded-lg border border-border p-3 text-left transition-colors hover:bg-accent"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{post.title || "Untitled"}</span>
                  <span className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs font-medium">
                    {formatLabels[post.format] || post.format}
                  </span>
                </div>
                {post.caption && (
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{post.caption}</p>
                )}
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="text-xs capitalize text-muted-foreground">{post.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
