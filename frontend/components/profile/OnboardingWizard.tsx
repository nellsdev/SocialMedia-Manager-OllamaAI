"use client";

import { useEffect, useState } from "react";
import { getApi } from "@/lib/api";
import { ArchetypeCard } from "./ArchetypeCard";
import { StrategyForm } from "./StrategyForm";

interface Archetype {
  id: string;
  name: string;
  description: string;
  default_tone: string;
  primary_metric: string;
  strategy_focus: string;
}

export function OnboardingWizard() {
  const [step, setStep] = useState(0);
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const api = getApi();
        const data = await api.listArchetypes();
        setArchetypes(data as Archetype[]);
      } catch {
        // If API fails, use defaults
        setArchetypes([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleArchetypeSelect = (id: string) => {
    setSelectedArchetype(id);
    setStep(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-sm text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {["Archetype", "Strategy"].map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                i <= step
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground"
              }`}
            >
              {i + 1}
            </div>
            <span className={`text-sm ${i <= step ? "text-foreground" : "text-muted-foreground"}`}>
              {label}
            </span>
            {i < 1 && <div className="h-px w-8 bg-border" />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div>
          <h2 className="text-xl font-bold">Choose your creator archetype</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This helps us tailor suggestions, metrics, and strategy to your goals.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {archetypes.map((a) => (
              <ArchetypeCard
                key={a.id}
                archetype={a}
                selected={selectedArchetype === a.id}
                onSelect={() => handleArchetypeSelect(a.id)}
              />
            ))}
          </div>
        </div>
      )}

      {step === 1 && (
        <div>
          <h2 className="text-xl font-bold">Define your strategy</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Customize your voice, pillars, audience, and goals.
          </p>
          <div className="mt-4">
            <StrategyForm
              initialData={{ archetype: selectedArchetype || "" }}
              onSaved={() => setStep(2)}
            />
          </div>
        </div>
      )}

      {step >= 2 && (
        <div className="rounded-lg border border-border p-6 text-center">
          <h2 className="text-xl font-bold">All set!</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Your profile is configured. Start creating content.
          </p>
        </div>
      )}
    </div>
  );
}
