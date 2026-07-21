"use client";

import { FormEvent, useEffect, useState } from "react";
import { getApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { CaptionSuggestions } from "./CaptionSuggestions";
import { HashtagSuggestions } from "./HashtagSuggestions";
import { Loader2 } from "lucide-react";

interface PostEditorFormProps {
  postId?: string;
  initialData?: {
    title?: string;
    caption?: string;
    first_comment?: string;
    format?: string;
    hashtags?: string[];
    media_urls?: string[];
    status?: string;
    scheduled_for?: string;
    platform_post_id?: string;
    platform_permalink?: string;
    failure_reason?: string;
  };
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-400",
  scheduled: "bg-blue-500",
  published: "bg-green-500",
  failed: "bg-red-500",
  retrying: "bg-yellow-500",
};

export function PostEditorForm({ postId, initialData }: PostEditorFormProps) {
  const router = useRouter();
  const isEditing = Boolean(postId);

  const [format, setFormat] = useState(initialData?.format || "carousel");
  const [title, setTitle] = useState(initialData?.title || "");
  const [caption, setCaption] = useState(initialData?.caption || "");
  const [firstComment, setFirstComment] = useState(initialData?.first_comment || "");
  const [hashtags, setHashtags] = useState<string[]>(initialData?.hashtags || []);
  const [scheduledDate, setScheduledDate] = useState(
    initialData?.scheduled_for ? initialData.scheduled_for.slice(0, 16) : ""
  );
  const [status, setStatus] = useState(initialData?.status || "draft");
  const [failureReason, setFailureReason] = useState(initialData?.failure_reason || "");
  const [platformPostId, setPlatformPostId] = useState(initialData?.platform_post_id || "");

  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (postId && !initialData) {
      const load = async () => {
        try {
          const api = getApi();
          const posts = await api.getPosts();
          const post = (posts as Array<Record<string, unknown>>).find(
            (p: Record<string, unknown>) => p.id === postId
          );
          if (post) {
            setFormat((post.format as string) || "carousel");
            setTitle((post.title as string) || "");
            setCaption((post.caption as string) || "");
            setFirstComment((post.first_comment as string) || "");
            setHashtags((post.hashtags as string[]) || []);
            setScheduledDate(
              post.scheduled_for
                ? (post.scheduled_for as string).slice(0, 16)
                : ""
            );
            setStatus((post.status as string) || "draft");
            setFailureReason((post.failure_reason as string) || "");
            setPlatformPostId((post.platform_post_id as string) || "");
          }
        } catch {
          // ignore
        }
      };
      load();
    }
  }, [postId, initialData]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    try {
      const api = getApi();
      const payload: Record<string, unknown> = {
        format,
        title: title || undefined,
        caption: caption || undefined,
        first_comment: firstComment || undefined,
        hashtags: hashtags.length > 0 ? hashtags : undefined,
        scheduled_for: scheduledDate
          ? new Date(scheduledDate).toISOString()
          : undefined,
      };

      if (isEditing) {
        await api.updatePost(postId!, payload);
      } else {
        await api.createPost(payload);
      }

      router.push("/content-grid");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save post");
    } finally {
      setSaving(false);
    }
  };

  const handleSchedule = async () => {
    if (!postId || !scheduledDate) return;

    setScheduling(true);
    setError("");

    try {
      const api = getApi();
      const result = await api.schedulePost(
        postId,
        new Date(scheduledDate).toISOString()
      );
      setStatus(result.status);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to schedule post");
    } finally {
      setScheduling(false);
    }
  };

  const handlePublish = async () => {
    if (!postId) return;

    setPublishing(true);
    setError("");

    try {
      const api = getApi();
      const result = await api.publishPost(postId);
      setStatus(result.status);
      if (result.platform_post_id) setPlatformPostId(result.platform_post_id);
      if (result.failure_reason) setFailureReason(result.failure_reason);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to publish post");
    } finally {
      setPublishing(false);
    }
  };

  const handleAddHashtag = (tag: string) => {
    if (!hashtags.some((h) => h.toLowerCase() === tag.toLowerCase())) {
      setHashtags([...hashtags, tag]);
    }
  };

  const handleRemoveHashtag = (tag: string) => {
    setHashtags(hashtags.filter((h) => h !== tag));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Status indicator */}
      {isEditing && (
        <div className="flex items-center gap-2 rounded-md border border-border bg-muted/30 px-3 py-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              STATUS_COLORS[status] || "bg-gray-400"
            }`}
          />
          <span className="text-xs font-medium capitalize text-muted-foreground">
            {status}
          </span>
          {failureReason && (
            <span className="ml-2 text-xs text-red-500" title={failureReason}>
              — {failureReason.slice(0, 80)}
            </span>
          )}
          {platformPostId && (
            <span className="ml-auto text-xs text-muted-foreground">
              IG ID: {platformPostId.slice(0, 12)}...
            </span>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Post title"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Format
        </label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="story">Story</option>
          <option value="carousel">Carousel</option>
          <option value="reel">Reel</option>
          <option value="live">Live</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Caption
        </label>
        <textarea
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          rows={5}
          className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Write your caption..."
        />

        {/* AI Caption Suggestions */}
        <div className="mt-2">
          <CaptionSuggestions
            postContext={`${title}\n${caption}`}
            onSelect={(text) => setCaption(text)}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          First Comment
        </label>
        <textarea
          value={firstComment}
          onChange={(e) => setFirstComment(e.target.value)}
          rows={2}
          className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Optional first comment"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Hashtags
        </label>
        {/* Selected hashtags */}
        {hashtags.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {hashtags.map((tag, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1 text-xs"
              >
                #{tag}
                <button
                  type="button"
                  onClick={() => handleRemoveHashtag(tag)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        )}

        {/* AI Hashtag Suggestions */}
        <HashtagSuggestions
          caption={caption}
          existingHashtags={hashtags}
          onAdd={handleAddHashtag}
        />
      </div>

      {/* Schedule UI (4.4) */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Schedule for
        </label>
        <div className="flex gap-2">
          <input
            type="datetime-local"
            value={scheduledDate}
            onChange={(e) => setScheduledDate(e.target.value)}
            className="block flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {isEditing && status === "draft" && scheduledDate && (
            <button
              type="button"
              onClick={handleSchedule}
              disabled={scheduling}
              className="inline-flex items-center gap-1 rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 disabled:opacity-50"
            >
              {scheduling ? (
                <Loader2 size={14} className="animate-spin" />
              ) : null}
              Schedule
            </button>
          )}
          {isEditing && status === "failed" && (
            <button
              type="button"
              onClick={handlePublish}
              disabled={publishing}
              className="inline-flex items-center gap-1 rounded-md bg-yellow-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 disabled:opacity-50"
            >
              {publishing ? (
                <Loader2 size={14} className="animate-spin" />
              ) : null}
              Retry
            </button>
          )}
        </div>

        {/* Publish now button (for draft/scheduled posts) */}
        {isEditing && (status === "draft" || status === "scheduled") && (
          <div className="mt-2">
            <button
              type="button"
              onClick={handlePublish}
              disabled={publishing}
              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-green-700 disabled:opacity-50"
            >
              {publishing ? (
                <Loader2 size={12} className="animate-spin" />
              ) : null}
              {publishing ? "Publishing..." : "Publish Now"}
            </button>
          </div>
        )}

        {status === "published" && (
          <p className="mt-1 text-xs text-green-600">
            Published successfully!
          </p>
        )}
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex-1 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {saving ? "Saving..." : isEditing ? "Update Post" : "Create Post"}
        </button>
      </div>
    </form>
  );
}
