"use client";

import { useEffect, useState } from "react";
import { getApi } from "@/lib/api";
import { StrategyForm } from "@/components/profile/StrategyForm";
import { ConversationalOnboarding } from "@/components/profile/ConversationalOnboarding";

export default function StrategySettingsPage() {
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const api = getApi();
        const data = await api.getMyProfile();
        setProfile(data);
      } catch {
        // Profile may not exist yet
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  const hasProfile = profile !== null && Object.keys(profile).length > 0;

  if (!hasProfile) {
    return (
      <div className="mx-auto max-w-xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Cuéntanos sobre ti</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Responde unas preguntas para definir tu estrategia de contenido.
          </p>
        </div>
        <ConversationalOnboarding />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Content Strategy</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Define your creator archetype, voice, and content pillars. These settings
          shape all AI suggestions and metric recommendations.
        </p>
      </div>

      <StrategyForm
        initialData={
          profile
            ? {
                archetype: (profile.archetype as string) || "",
                voice_description: (profile.voice_description as string) || "",
                content_pillars: (profile.content_pillars as string[]) || [],
                target_audience: (profile.target_audience as string) || "",
                goals: (profile.goals as string) || "",
              }
            : undefined
        }
      />
    </div>
  );
}
