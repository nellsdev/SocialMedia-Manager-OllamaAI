"use client";

import { useState } from "react";
import { FormatSelector } from "@/components/posts/FormatSelector";
import { PostEditorForm } from "@/components/posts/PostEditorForm";

export default function NewPostPage() {
  const [format, setFormat] = useState<string | null>(null);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">New Post</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Choose a format and create your Instagram post.
        </p>
      </div>

      {!format ? (
        <div>
          <h2 className="text-sm font-semibold mb-3">Select format</h2>
          <FormatSelector selected="" onSelect={setFormat} />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFormat(null)}
              className="text-sm text-primary hover:underline"
            >
              ← Change format
            </button>
            <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium capitalize">
              {format}
            </span>
          </div>
          <PostEditorForm initialData={{ format }} />
        </div>
      )}
    </div>
  );
}
