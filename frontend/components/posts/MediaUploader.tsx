"use client";

import { Upload, X } from "lucide-react";
import { useState } from "react";

interface MediaUploaderProps {
  urls: string[];
  onChange: (urls: string[]) => void;
  maxFiles?: number;
  accept?: string;
}

export function MediaUploader({
  urls,
  onChange,
  maxFiles = 10,
  accept = "image/*,video/*",
}: MediaUploaderProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    // In a real implementation, this would upload to Supabase Storage
    // and return URLs. For MVP, we simulate with placeholder URLs.
    const files = Array.from(e.dataTransfer.files);
    const remaining = maxFiles - urls.length;
    const toAdd = files.slice(0, remaining);
    const newUrls = toAdd.map(
      (f) => `https://placeholder.supabase.co/storage/v1/object/public/media/${f.name}`
    );
    onChange([...urls, ...newUrls]);
  };

  const removeUrl = (idx: number) => {
    onChange(urls.filter((_, i) => i !== idx));
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground mb-1">
        Media ({urls.length}/{maxFiles})
      </label>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors ${
          dragging
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
        }`}
      >
        <Upload size={24} className="text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          Drag & drop files here, or click to browse
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {accept.split(",").join(", ")}
        </p>
        <input
          type="file"
          multiple
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            const remaining = maxFiles - urls.length;
            const newUrls = files.slice(0, remaining).map(
              (f) => `https://placeholder.supabase.co/storage/v1/object/public/media/${f.name}`
            );
            onChange([...urls, ...newUrls]);
          }}
        />
      </div>

      {/* File list */}
      {urls.length > 0 && (
        <div className="grid grid-cols-4 gap-2">
          {urls.map((url, i) => (
            <div key={i} className="relative group">
              <div className="aspect-square rounded-md bg-muted flex items-center justify-center text-xs text-muted-foreground overflow-hidden">
                {url.split("/").pop()}
              </div>
              <button
                type="button"
                onClick={() => removeUrl(i)}
                className="absolute -top-1.5 -right-1.5 rounded-full bg-red-500 p-0.5 text-white opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
