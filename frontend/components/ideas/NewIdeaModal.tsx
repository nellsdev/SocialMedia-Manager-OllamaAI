"use client";

import { FormEvent, useState } from "react";
import { getApi } from "@/lib/api";
import { X } from "lucide-react";

interface NewIdeaModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function NewIdeaModal({ open, onClose, onCreated }: NewIdeaModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [format, setFormat] = useState("");
  const [pillar, setPillar] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const api = getApi();
      await api.createIdea({
        title,
        description: description || undefined,
        suggested_format: format || undefined,
        content_pillar: pillar || undefined,
      });
      setTitle("");
      setDescription("");
      setFormat("");
      setPillar("");
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create idea");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-card p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">New Idea</h2>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && (
            <div className="rounded-md bg-red-50 p-2.5 text-xs text-red-800 dark:bg-red-900/30 dark:text-red-400">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="What's your idea?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Add more details..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="">Any format</option>
                <option value="story">Story</option>
                <option value="carousel">Carousel</option>
                <option value="reel">Reel</option>
                <option value="live">Live</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Pillar</label>
              <input
                type="text"
                value={pillar}
                onChange={(e) => setPillar(e.target.value)}
                className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
                placeholder="e.g., tips"
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Idea"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
