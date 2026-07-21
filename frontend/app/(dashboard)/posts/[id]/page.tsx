"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getApi } from "@/lib/api";
import { PostEditorForm } from "@/components/posts/PostEditorForm";

export default function EditPostPage() {
  const params = useParams();
  const postId = params.id as string;
  const [post, setPost] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const api = getApi();
        const posts = await api.getPosts();
        const found = (posts as Array<Record<string, unknown>>).find(
          (p: Record<string, unknown>) => p.id === postId
        );
        setPost(found || null);
      } catch {
        setPost(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [postId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-xl py-12 text-center text-sm text-muted-foreground">
        Loading post...
      </div>
    );
  }

  if (!post) {
    return (
      <div className="mx-auto max-w-xl py-12 text-center text-sm text-muted-foreground">
        Post not found.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Edit Post</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Update your post details.
        </p>
      </div>

      <PostEditorForm
        postId={postId}
        initialData={{
          title: post.title as string,
          caption: post.caption as string,
          first_comment: post.first_comment as string,
          format: post.format as string,
          hashtags: post.hashtags as string[],
          media_urls: post.media_urls as string[],
          status: post.status as string,
          scheduled_for: post.scheduled_for as string,
        }}
      />
    </div>
  );
}
