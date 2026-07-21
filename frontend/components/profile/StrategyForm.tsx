"use client";

import { FormEvent, useEffect, useState } from "react";
import { getApi } from "@/lib/api";

interface StrategyFormProps {
  initialData?: {
    archetype?: string;
    voice_description?: string;
    content_pillars?: string[];
    target_audience?: string;
    goals?: string;
    visual_references?: string[];
  };
  onSaved?: () => void;
}

export function StrategyForm({ initialData, onSaved }: StrategyFormProps) {
  const [archetype, setArchetype] = useState(initialData?.archetype || "");
  const [voice, setVoice] = useState(initialData?.voice_description || "");
  const [pillarsCsv, setPillarsCsv] = useState(
    (initialData?.content_pillars || []).join(", ")
  );
  const [audience, setAudience] = useState(initialData?.target_audience || "");
  const [goals, setGoals] = useState(initialData?.goals || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const api = getApi();
      const pillars = pillarsCsv
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await api.updateStrategy({
        archetype: archetype || undefined,
        voice_description: voice || undefined,
        content_pillars: pillars.length > 0 ? pillars : undefined,
        target_audience: audience || undefined,
        goals: goals || undefined,
      });
      setMessage("Strategy saved!");
      onSaved?.();
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {message && (
        <div
          className={`rounded-md p-3 text-sm ${
            message.includes("saved")
              ? "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-400"
          }`}
        >
          {message}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-foreground">
          Archetype
        </label>
        <select
          value={archetype}
          onChange={(e) => setArchetype(e.target.value)}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">Select archetype...</option>
          <option value="aspiring_influencer">Aspiring Influencer</option>
          <option value="authority_professional">Authority Professional</option>
          <option value="personal_sharing">Personal Sharing</option>
          <option value="business_owner">Business Owner</option>
          <option value="community_builder">Community Builder</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Voice / Tone Description
        </label>
        <textarea
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Describe your brand voice (e.g., 'warm and approachable with industry expertise')"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Content Pillars (comma-separated, max 5)
        </label>
        <input
          type="text"
          value={pillarsCsv}
          onChange={(e) => setPillarsCsv(e.target.value)}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Tips & Tricks, Behind the Scenes, Product Updates"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Target Audience
        </label>
        <textarea
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Describe who you create content for"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Goals
        </label>
        <textarea
          value={goals}
          onChange={(e) => setGoals(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="What do you want to achieve with your content?"
        />
      </div>

      <button
        type="submit"
        disabled={saving}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save Strategy"}
      </button>
    </form>
  );
}
