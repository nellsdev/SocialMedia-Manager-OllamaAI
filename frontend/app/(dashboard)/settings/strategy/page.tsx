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
      <div className="mx-auto max-w-5xl space-y-6 px-4 lg:px-0">
        <div>
          <h1 className="text-2xl font-bold">Cuéntanos sobre ti</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Responde unas preguntas para definir tu estrategia de contenido.
          </p>
        </div>
        <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
          <ConversationalOnboarding />
          <aside className="hidden space-y-4 lg:sticky lg:top-6 lg:block">
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="text-base font-semibold text-foreground">
                ¿Cómo funciona?
              </h3>
              <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted-foreground">
                <li>Conversamos sobre tu marca y objetivos</li>
                <li>Te preguntamos por tu estética (podés subir imágenes de referencia)</li>
                <li>Analizamos tu nicho en segundo plano</li>
                <li>Generamos tu plan de arranque</li>
              </ol>
            </div>
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="text-base font-semibold text-foreground">Tips</h3>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li>No hay respuestas incorrectas.</li>
                <li>Podés subir imágenes del estilo que te gusta.</li>
                <li>Todo lo aprendido es editable al final.</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 lg:px-0">
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
