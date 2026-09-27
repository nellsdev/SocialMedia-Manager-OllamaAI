"use client";

import { useEffect, useState } from "react";
import { getApi } from "@/lib/api";
import { IdeaCard } from "./IdeaCard";
import { IdeaFilters } from "./IdeaFilters";
import { NewIdeaModal } from "./NewIdeaModal";
import { Plus } from "lucide-react";

interface Idea {
  id: string;
  title: string;
  description?: string;
  suggested_format?: string;
  content_pillar?: string;
  source?: string;
  status?: string;
}

export function IdeaBankList() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [pillarFilter, setPillarFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [showNewModal, setShowNewModal] = useState(false);

  const loadIdeas = async () => {
    setLoading(true);
    try {
      const api = getApi();
      const data = await api.getIdeas({
        pillar: pillarFilter || undefined,
        status: statusFilter || undefined,
        source: sourceFilter || undefined,
      });
      setIdeas(data as unknown as Idea[]);
    } catch {
      setIdeas([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIdeas();
  }, [pillarFilter, statusFilter, sourceFilter]);

  const handleConvert = async (id: string) => {
    try {
      const api = getApi();
      const { post_id } = await api.convertIdea(id);
      window.location.href = `/posts/${post_id}`;
    } catch (err) {
      console.error("Convert failed", err);
    }
  };

  // Extract unique pillars from ideas for the filter
  const pillars = [...new Set(ideas.map((i) => i.content_pillar).filter(Boolean) as string[])];

  // Get profile pillars if no ideas yet
  useEffect(() => {
    if (pillars.length === 0) {
      const loadPillars = async () => {
        try {
          const api = getApi();
          const profile = await api.getMyProfile();
          const profilePillars = (profile as { content_pillars?: string[] }).content_pillars;
          if (profilePillars) {
            // Just ensure they're in state for filter dropdown
            setPillarFilter("");
          }
        } catch {
          // ignore
        }
      };
      loadPillars();
    }
  }, [ideas]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <IdeaFilters
          pillars={pillars}
          selectedPillar={pillarFilter}
          onPillarChange={setPillarFilter}
          selectedStatus={statusFilter}
          onStatusChange={setStatusFilter}
          selectedSource={sourceFilter}
          onSourceChange={setSourceFilter}
        />
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90"
        >
          <Plus size={16} />
          New Idea
        </button>
      </div>

      {loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">Loading ideas...</div>
      ) : ideas.length === 0 ? (
        <div className="py-8 text-center text-sm text-muted-foreground">
          No ideas yet. Click &quot;New Idea&quot; to capture your first content idea.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ideas.map((idea) => (
            <IdeaCard
              key={idea.id}
              id={idea.id}
              title={idea.title}
              description={idea.description}
              suggestedFormat={idea.suggested_format}
              contentPillar={idea.content_pillar}
              source={idea.source}
              status={idea.status}
              onConvert={handleConvert}
              draggable
            />
          ))}
        </div>
      )}

      <NewIdeaModal
        open={showNewModal}
        onClose={() => setShowNewModal(false)}
        onCreated={loadIdeas}
      />
    </div>
  );
}
