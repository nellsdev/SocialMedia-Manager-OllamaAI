# Tasks: MVP — Personal Profile + Instagram

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~5,000–7,500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR #1→PR #2→PR #3 |
| Delivery strategy | force-chained |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base Branch |
|------|------|-----------|-------------|
| 1 | Foundation + Auth + Core Domain (backend + frontend) | PR #1 | `mvp-personal-instagram` (tracker) |
| 2 | AI Agents + Scheduling + Publishing + WhatsApp | PR #2 | PR #1 branch |
| 3 | Dashboard & Metrics + All Tests | PR #3 | PR #2 branch |

## Phase 1: Foundation (PR #1)

- [x] 1.1 Create `backend/app/core/config.py` — Pydantic Settings (env, secrets)
- [x] 1.2 Create `backend/app/core/database.py` — Supabase client singleton
- [x] 1.3 Create `backend/app/core/security.py` — Fernet token encrypt/decrypt
- [x] 1.4 Create `backend/app/main.py` — FastAPI app, CORS, router registration
- [x] 1.5 Create `backend/requirements.txt` — all dependencies
- [x] 1.6 Create `backend/app/models/` — SQLAlchemy models (6 tables: profiles, social_accounts, content_ideas, content_posts, metrics_snapshots, scheduler_jobs)
- [x] 1.7 Create `backend/app/schemas/` — Pydantic request/response schemas
- [x] 1.8 Create `backend/app/api/auth.py` — POST /auth/register, POST /auth/login, GET /auth/session
- [x] 1.9 Create `backend/app/api/profiles.py` — GET/PUT /profiles/me, GET /profiles/me/archetypes
- [x] 1.10 Create `backend/app/api/social.py` — Instagram OAuth connect/callback/status

## Phase 2: Core Domain (PR #1)

- [x] 2.1 Create `backend/app/api/ideas.py` — GET/POST /ideas, PUT /ideas/{id}/convert
- [x] 2.2 Create `backend/app/api/posts.py` — GET/POST /posts, PUT /posts/{id}
- [x] 2.3 Create `backend/app/api/grid.py` — GET /grid, GET /grid/distribution
- [x] 2.4 Create `frontend/package.json` — next, react, recharts, dnd-kit, tailwind
- [x] 2.5 Create `frontend/lib/api.ts` — typed FastAPI client
- [x] 2.6 Create `frontend/app/layout.tsx` — AuthProvider, ThemeProvider
- [x] 2.7 Create `frontend/app/(auth)/login/page.tsx` + `register/page.tsx`
- [x] 2.8 Create `frontend/app/(dashboard)/layout.tsx` — Sidebar, TopBar, ProfileSwitcher
- [x] 2.9 Create `frontend/components/auth/LoginForm.tsx`, `RegisterForm.tsx`
- [x] 2.10 Create `frontend/components/profile/` — OnboardingWizard, ArchetypeCard, StrategyForm
- [x] 2.11 Create `frontend/components/settings/InstagramConnect.tsx`
- [x] 2.12 Create `frontend/app/(dashboard)/settings/` — strategy, integrations, account pages
- [x] 2.13 Create `frontend/components/ideas/` — IdeaBankList, IdeaCard, IdeaFilters, NewIdeaModal
- [x] 2.14 Create `frontend/app/(dashboard)/ideas/page.tsx`
- [x] 2.15 Create `frontend/components/grid/` — CalendarView, PostCard, DayDetail, PillarDonut, FormatBalanceAlert
- [x] 2.16 Create `frontend/components/shared/` — DragProvider, DraggableIdea, DroppableDate
- [x] 2.17 Create `frontend/app/(dashboard)/content-grid/page.tsx`
- [x] 2.18 Create `frontend/components/posts/FormatSelector.tsx`, `PostEditorForm.tsx`, `MediaUploader.tsx`
- [x] 2.19 Create `frontend/app/(dashboard)/posts/new/page.tsx` + `[id]/page.tsx`

## Phase 3: AI & Agents (PR #2)

- [x] 3.1 Create `backend/app/agents/base.py` — abstract BaseAgent with ProfileStrategy dataclass
- [x] 3.2 Create `backend/app/agents/orchestrator.py` — Orchestrator coordinator with task routing, phi4-mini fallback
- [x] 3.3 Create `backend/app/agents/content_creator.py` — captions, hashtags, format recs via qwen2.5:7b Ollama
- [x] 3.4 Create `backend/app/agents/trend_researcher.py` — trending topics/hashtags via qwen2.5:7b
- [x] 3.5 Create `backend/app/agents/analytics_agent.py` — metrics fetch, engagement rate calculator
- [x] 3.6 Create `backend/app/agents/scheduler_agent.py` — APScheduler job management, publish with retry
- [x] 3.7 Create `backend/app/agents/idea_bank.py` — WhatsApp processing, auto-tagging via phi4-mini:3.8b
- [x] 3.8 Create `backend/app/api/agents.py` — POST /agents/captions, /hashtags, /format, /weekly-ideas
- [x] 3.9 Create `frontend/components/posts/CaptionSuggestions.tsx` — 3 AI options + "Use This" + tone/length badges
- [x] 3.10 Create `frontend/components/posts/HashtagSuggestions.tsx` — clickable tags with add/added state

## Phase 4: Integration (PR #2)

- [x] 4.1 Wire schedule/publish in `backend/app/api/posts.py` — POST /posts/{id}/schedule, POST /posts/{id}/publish, POST /posts/{id}/retry
- [x] 4.2 Integrate SchedulerAgent → APScheduler → Instagram Graph API publish (media container + media_publish steps)
- [x] 4.3 Add retry logic for rate-limit and failure scenarios — exponential back-off, max 3 retries, retry_count tracking (R018)
- [x] 4.4 Create schedule UI in frontend posts pages — date/time picker + Schedule/Publish Now/Retry buttons + status indicator dot + failure reason display
- [x] 4.5 Create WhatsApp webhook handler — POST /ideas/whatsapp (R023-R024) + backend/api/whatsapp.py for connect/status
- [x] 4.6 Create `frontend/components/settings/WhatsAppConfig.tsx` — QR code, phone input, connection status

## Phase 5: Dashboard & Metrics (PR #3)

- [ ] 5.1 Create `backend/app/api/dashboard.py` — GET /dashboard/kpis, GET /dashboard/timeseries
- [ ] 5.2 Create `frontend/components/dashboard/KpiCard.tsx` — value, trend, delta
- [ ] 5.3 Create `frontend/components/dashboard/TimeSeriesChart.tsx` — Recharts LineChart
- [ ] 5.4 Create `frontend/components/dashboard/ArchetypeTopMetrics.tsx` — archetype-adaptive layout (R022)
- [ ] 5.5 Create `frontend/app/(dashboard)/dashboard/page.tsx` — KPI dashboard

## Phase 6: Testing (PR #3)

- [ ] 6.1 Write pytest: Pydantic schemas, Fernet crypto, engagement rate calc
- [ ] 6.2 Write pytest: API routes with FastAPI TestClient
- [ ] 6.3 Write pytest: Agent prompt builders + Ollama client (mocked)
- [ ] 6.4 Write pytest: SchedulerAgent APScheduler job registration
- [ ] 6.5 Write pytest: WhatsApp webhook parsing + idea creation
- [ ] 6.6 Write pytest: Instagram Graph API client (mocked responses)
