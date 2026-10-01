"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getApi } from "@/lib/api";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Search,
  Send,
} from "lucide-react";

const STATES = [
  "topic",
  "starting_point",
  "content_review",
  "audience",
  "references",
  "goals",
];

const ARCHETYPES = [
  { value: "aspiring_influencer", label: "Aspiring Influencer" },
  { value: "authority_professional", label: "Authority Professional" },
  { value: "personal_sharing", label: "Personal Sharing" },
  { value: "business_owner", label: "Business Owner" },
  { value: "community_builder", label: "Community Builder" },
];

const MAX_POLL_TRIES = 30;
const POLL_INTERVAL_MS = 8000;

type Phase =
  | "asking"
  | "finishing"
  | "summary"
  | "researching"
  | "done"
  | "failed";

interface ChatMessage {
  role: string;
  content: string;
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((v) => (typeof v === "string" ? v : String(v)));
}

function asRecordArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (v): v is Record<string, unknown> => typeof v === "object" && v !== null
  );
}

export function ConversationalOnboarding() {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [currentStateIdx, setCurrentStateIdx] = useState(0);
  const [question, setQuestion] = useState("");
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<Phase>("asking");
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [research, setResearch] = useState<Record<string, unknown> | null>(
    null
  );
  const [researchStatus, setResearchStatus] = useState<
    "pending" | "done" | "failed"
  >("pending");
  const [loading, setLoading] = useState(false);
  const [nicheGuess, setNicheGuess] = useState<string>("");
  const [error, setError] = useState("");

  // Editable summary fields (client-side only; profile already persisted).
  const [archetype, setArchetype] = useState("");
  const [voice, setVoice] = useState("");
  const [pillarsCsv, setPillarsCsv] = useState("");
  const [audience, setAudience] = useState("");
  const [goalsText, setGoalsText] = useState("");

  const mountedRef = useRef(true);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTriesRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const api = getApi();

  useEffect(() => {
    mountedRef.current = true;
    const init = async () => {
      setLoading(true);
      try {
        const resp = await api.onboardingTurn({
          history: [],
          current_state: STATES[0],
        });
        if (mountedRef.current) setQuestion(resp.question);
      } catch (err: unknown) {
        if (mountedRef.current) {
          setError(
            err instanceof Error ? err.message : "No se pudo iniciar el chat"
          );
        }
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    };
    init();
    return () => {
      mountedRef.current = false;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, question, loading, phase]);

  const pollOnce = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const resp = await api.getOnboardingResearch();
      if (resp.status === "done") {
        if (!mountedRef.current) return;
        setResearch(resp.niche_analysis);
        setResearchStatus("done");
        setPhase((prev) => (prev === "researching" ? "done" : prev));
        return;
      }
      if (resp.status === "failed") {
        if (!mountedRef.current) return;
        setResearchStatus("failed");
        setPhase((prev) => (prev === "researching" ? "failed" : prev));
        return;
      }
    } catch {
      // Transient polling errors are ignored; the loop keeps trying.
    }
    pollTriesRef.current += 1;
    if (pollTriesRef.current < MAX_POLL_TRIES) {
      pollTimerRef.current = setTimeout(pollOnce, POLL_INTERVAL_MS);
    } else if (mountedRef.current) {
      setResearchStatus("failed");
      setPhase((prev) => (prev === "researching" ? "failed" : prev));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startPolling = useCallback(() => {
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    pollTriesRef.current = 0;
    setResearchStatus("pending");
    pollOnce();
  }, [pollOnce]);

  const handleSend = async () => {
    const answer = input.trim();
    if (!answer || loading || phase !== "asking") return;

    const withQA: ChatMessage[] = [
      ...history,
      { role: "assistant", content: question },
      { role: "user", content: answer },
    ];
    // Optimistic: show the exchange immediately.
    setHistory(withQA);
    setInput("");
    setError("");
    setLoading(true);

    const niche = currentStateIdx === 0 ? answer : nicheGuess;
    if (currentStateIdx === 0) setNicheGuess(answer);

    const nextIdx = currentStateIdx + 1;
    try {
      if (nextIdx < STATES.length) {
        const resp = await api.onboardingTurn({
          history: withQA,
          current_state: STATES[nextIdx],
          niche: niche || undefined,
        });
        if (!mountedRef.current) return;
        setQuestion(resp.question);
        setCurrentStateIdx(nextIdx);
      } else {
        setPhase("finishing");
        const resp = await api.onboardingFinish({ history: withQA });
        if (!mountedRef.current) return;
        setProfile(resp.profile);
        setArchetype(asString(resp.profile.archetype));
        setVoice(asString(resp.profile.voice_description));
        setPillarsCsv(asStringArray(resp.profile.content_pillars).join(", "));
        setAudience(asString(resp.profile.target_audience));
        setGoalsText(asString(resp.profile.goals));
        setPhase("summary");
        startPolling();
      }
    } catch (err: unknown) {
      if (!mountedRef.current) return;
      setError(
        err instanceof Error ? err.message : "Algo salió mal. Intenta de nuevo."
      );
      // Stay on (or return to) the asking phase so the user can retry.
      setPhase("asking");
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  };

  const handleViewResearch = () => {
    if (researchStatus === "done") setPhase("done");
    else if (researchStatus === "failed") setPhase("failed");
    else setPhase("researching");
  };

  const handleRetryResearch = () => {
    setPhase("researching");
    startPolling();
  };

  // ---------- Render helpers ----------

  const renderSummary = (readOnly: boolean) => (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4">
      <div>
        <label className="block text-sm font-medium text-foreground">
          Arquetipo
        </label>
        <select
          value={archetype}
          onChange={(e) => setArchetype(e.target.value)}
          disabled={readOnly}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        >
          <option value="">Seleccionar...</option>
          {ARCHETYPES.map((a) => (
            <option key={a.value} value={a.value}>
              {a.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Descripción de voz
        </label>
        <textarea
          value={voice}
          onChange={(e) => setVoice(e.target.value)}
          disabled={readOnly}
          rows={3}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Pilares de contenido (separados por coma)
        </label>
        <input
          type="text"
          value={pillarsCsv}
          onChange={(e) => setPillarsCsv(e.target.value)}
          disabled={readOnly}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Audiencia objetivo
        </label>
        <input
          type="text"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          disabled={readOnly}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground">
          Metas
        </label>
        <input
          type="text"
          value={goalsText}
          onChange={(e) => setGoalsText(e.target.value)}
          disabled={readOnly}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        />
      </div>
    </div>
  );

  const renderResearch = () => {
    if (!research) return null;
    const topics = asRecordArray(research.trending_topics);
    const hashtags = asStringArray(research.trending_hashtags);
    const accounts = asRecordArray(research.reference_accounts);
    const opportunities = asStringArray(research.opportunities);
    const recommendation = asString(research.recommendation);

    return (
      <div className="space-y-4">
        {topics.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground">
              Temas en tendencia
            </h3>
            <ul className="mt-2 space-y-2">
              {topics.map((t, i) => {
                const title =
                  asString(t.topic) || asString(t.title) || String(t);
                const relevance =
                  asString(t.relevance) || asString(t.why_relevant);
                return (
                  <li key={i} className="text-sm">
                    <span className="font-medium text-foreground">{title}</span>
                    {relevance && (
                      <span className="block text-xs text-muted-foreground">
                        {relevance}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {hashtags.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground">
              Hashtags en tendencia
            </h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {hashtags.map((h, i) => (
                <span
                  key={i}
                  className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground"
                >
                  {h.startsWith("#") ? h : `#${h}`}
                </span>
              ))}
            </div>
          </div>
        )}

        {accounts.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground">
              Cuentas de referencia
            </h3>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {accounts.map((a, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-border bg-background p-3"
                >
                  <p className="text-sm font-medium text-foreground">
                    @{asString(a.username).replace(/^@/, "")}
                  </p>
                  {asString(a.what_works) && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {asString(a.what_works)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {opportunities.length > 0 && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground">
              Oportunidades
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {opportunities.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
          </div>
        )}

        {recommendation && (
          <div className="rounded-xl border border-primary/40 bg-primary/5 p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              Recomendación
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {recommendation}
            </p>
          </div>
        )}
      </div>
    );
  };

  // ---------- Phase renders ----------

  if (phase === "finishing") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-8">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">
          Analizando tus respuestas...
        </p>
      </div>
    );
  }

  if (phase === "summary") {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-card p-4">
          <CheckCircle2 className="h-5 w-5 text-green-500" />
          <div>
            <p className="text-sm font-medium text-foreground">
              Se guardó tu perfil
            </p>
            <p className="text-xs text-muted-foreground">
              Revisa el resumen; podrás ajustarlo luego en Configuración.
            </p>
          </div>
        </div>
        {renderSummary(false)}
        <button
          type="button"
          onClick={handleViewResearch}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Ver análisis de tendencias
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    );
  }

  if (phase === "researching") {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-4">
          <Search className="h-5 w-5 text-primary" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">
              Analizando tu nicho...
            </p>
            <p className="text-xs text-muted-foreground">
              Esto puede tomar unos minutos. Mientras tanto, revisa tu resumen.
            </p>
          </div>
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
        {renderSummary(true)}
        <div ref={scrollRef} />
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-card p-4">
          <CheckCircle2 className="h-5 w-5 text-green-500" />
          <p className="text-sm font-medium text-foreground">
            Tu análisis de nicho está listo
          </p>
        </div>
        {renderResearch()}
        <button
          type="button"
          onClick={() => (window.location.href = "/ideas")}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Ir al contenido
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    );
  }

  if (phase === "failed") {
    return (
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/20">
          <AlertCircle className="mt-0.5 h-5 w-5 text-red-600 dark:text-red-400" />
          <div>
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              No pudimos completar el análisis de tu nicho
            </p>
            <p className="mt-1 text-xs text-red-700 dark:text-red-400">
              Tu perfil se guardó correctamente. Puedes reintentar el análisis o
              continuar y verlo más tarde.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleRetryResearch}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Volver a intentar el análisis
          </button>
          <button
            type="button"
            onClick={() => (window.location.href = "/ideas")}
            className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
          >
            Continuar igual
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  // phase === "asking"
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">
          Paso {Math.min(currentStateIdx + 1, STATES.length)} de{" "}
          {STATES.length}
        </p>
        <div className="flex gap-1">
          {STATES.map((s, i) => (
            <span
              key={s}
              className={`h-1.5 w-6 rounded-full ${
                i <= currentStateIdx ? "bg-primary" : "bg-muted"
              }`}
            />
          ))}
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="space-y-3 rounded-xl border border-border bg-card p-4">
        {history.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[80%] rounded-xl bg-primary px-3 py-2 text-sm text-primary-foreground">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <div className="max-w-[80%] rounded-xl bg-muted px-3 py-2 text-sm text-foreground">
                {m.content}
              </div>
            </div>
          )
        )}

        {loading ? (
          <div className="flex justify-start">
            <div className="rounded-xl bg-muted px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        ) : (
          question && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-xl bg-muted px-3 py-2 text-sm text-foreground">
                {question}
              </div>
            </div>
          )
        )}
        <div ref={scrollRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder="Escribe tu respuesta..."
          className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-70"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
