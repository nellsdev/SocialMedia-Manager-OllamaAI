# Design: MVP — Personal Profile + Instagram

## Technical Approach

Monorepo with `backend/` (FastAPI + agents) and `frontend/` (Next.js 14 App Router). Supabase provides auth, PostgreSQL, RLS, and storage. Ollama serves local Llama 3.1 for AI features. Custom Python agent classes (not CrewAI) coordinate via an async Orchestrator. All 8 specs (R001–R024) map to vertical slices connecting frontend → API → agents → external APIs.

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Custom agents vs CrewAI | CrewAI offers orchestration out of box but hides flow; custom teaches fundamentals | Custom Python classes (specs R013–R016) |
| Supabase Vault vs Fernet for tokens | Vault is managed but slower dev loop; Fernet is simpler for MVP | Fernet encryption (R022 risk mitigation) |
| APScheduler vs Celery | Celery needs Redis/RabbitMQ; APScheduler is zero-dependency for single-user | APScheduler (spec R017–R018) |
| DnD library: dnd-kit vs react-beautiful-dnd | react-beautiful-dnd unmaintained; dnd-kit is modern, tree-shakable | dnd-kit (spec R010) |
| Charts: Recharts vs Chart.js | Recharts is React-native, composable; Chart.js is imperative | Recharts (spec R020–R021) |
| WhatsApp: Twilio vs WhatsApp Cloud API | Twilio $0.05/msg; WhatsApp Cloud API free for business-initiated | WhatsApp Cloud API (spec R023–R024) |

## API Endpoints

| Method | Path | Description | Request → Response |
|--------|------|-------------|-------------------|
| POST | `/auth/register` | Register via email | `{email, password}` → `{user_id}` |
| POST | `/auth/login` | Login via email/password | `{email, password}` → `{session_token}` |
| GET | `/auth/session` | Verify session | → `{user, profile}` |
| GET | `/profiles/me` | Get current profile | → `{profile, strategy}` |
| PUT | `/profiles/me/strategy` | Update strategy | `{archetype, voice, pillars[]}` → `{updated}` |
| GET | `/profiles/me/archetypes` | List archetypes | → `[{id, name, defaults}]` |
| POST | `/social/instagram/connect` | Initiate IG OAuth | `{redirect_uri}` → `{auth_url}` |
| POST | `/social/instagram/callback` | Handle OAuth callback | `{code}` → `{account}` |
| GET | `/social/instagram/status` | Account status | → `{connected, username, expires_at}` |
| GET | `/ideas` | List ideas | `?pillar=&status=&source=` → `[{id, title, ...}]` |
| POST | `/ideas` | Create idea | `{title, description, format?, pillar?}` → `{id}` |
| POST | `/ideas/whatsapp` | WhatsApp webhook | `{message, media?}` → `{id}` |
| PUT | `/ideas/{id}/convert` | Convert to draft | → `{post_id}` |
| GET | `/posts` | List posts | `?status=&format=&date=` → `[{id, ...}]` |
| POST | `/posts` | Create post | `{format, title, caption, media[]}` → `{id}` |
| PUT | `/posts/{id}` | Update post | → `{updated}` |
| POST | `/posts/{id}/schedule` | Schedule | `{scheduled_for}` → `{status: "scheduled"}` |
| POST | `/posts/{id}/publish` | Publish immediately | → `{status, platform_post_id}` |
| GET | `/grid` | Content grid data | `?view=month&date=` → `{days: {date: [post]}}` |
| GET | `/grid/distribution` | Pillar/format analysis | → `{pillars: {name, count, pct}, formats: {...}}` |
| POST | `/agents/captions` | Request caption suggestions | `{post_content, archetype}` → `{options: [str;3]}` |
| POST | `/agents/hashtags` | Request hashtags | `{caption, pillars[]}` → `{hashtags: [str;5-10]}` |
| POST | `/agents/weekly-ideas` | Generate weekly batch | → `{ideas: [{title, format, pillar}]}` |
| GET | `/dashboard/kpis` | Current KPIs | → `{followers, likes, comments, reach, engagement_rate}` |
| GET | `/dashboard/timeseries` | Metrics over time | `?metric=&days=30` → `[{date, value}]` |
| POST | `/whatsapp/connect` | Initiate WhatsApp | `{phone}` → `{qr_code}` |
| GET | `/whatsapp/status` | WhatsApp connection | → `{connected, phone}` |

## Database Schema

### profiles
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → auth.users | Supabase managed |
| name | TEXT | "Personal" for MVP |
| slug | TEXT UNIQUE | "personal" |
| avatar_url | TEXT | nullable |
| archetype | TEXT | ENUM: aspiring_influencer, authority_professional, personal_sharing, business_owner, community_builder |
| voice_description | TEXT | Creator's tone definition |
| content_pillars | TEXT[] | 1–5 pillars |
| target_audience | TEXT | Description |
| goals | TEXT | Primary objectives |
| visual_references | TEXT[] | URLs |
| created_at | TIMESTAMPTZ | |

### social_accounts
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| profile_id | UUID FK → profiles | |
| platform | TEXT | "instagram" |
| account_name | TEXT | |
| account_id | TEXT | Instagram user ID |
| access_token | TEXT | Fernet-encrypted |
| refresh_token | TEXT | Fernet-encrypted |
| token_expires_at | TIMESTAMPTZ | |
| is_active | BOOLEAN | default true |

### content_ideas
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| profile_id | UUID FK → profiles | |
| title | TEXT | |
| description | TEXT | |
| suggested_format | TEXT | nullable: story/carousel/reel/live |
| content_pillar | TEXT | nullable |
| source | TEXT | "manual" / "whatsapp" |
| media_refs | TEXT[] | URLs from WhatsApp |
| status | TEXT | "idea" / "converted" |
| converted_to | UUID FK → content_posts | nullable |
| created_at | TIMESTAMPTZ | |

### content_posts
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| profile_id | UUID FK → profiles | |
| ig_account_id | UUID FK → social_accounts | |
| format | TEXT | story / carousel / reel / live |
| title | TEXT | |
| caption | TEXT | |
| first_comment | TEXT | nullable |
| media_urls | TEXT[] | Uploaded to Supabase Storage |
| hashtags | TEXT[] | |
| status | TEXT | draft / scheduled / published / failed / retrying |
| scheduled_for | TIMESTAMPTZ | nullable |
| published_at | TIMESTAMPTZ | nullable |
| platform_post_id | TEXT | Instagram media ID |
| platform_permalink | TEXT | Post URL |
| failure_reason | TEXT | nullable |

### metrics_snapshots
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| social_account_id | UUID FK → social_accounts | |
| metric_date | DATE | |
| followers | INTEGER | |
| likes | INTEGER | |
| comments | INTEGER | |
| reach | INTEGER | |
| saves | INTEGER | |
| shares | INTEGER | |
| engagement_rate | FLOAT | |
| raw_data | JSONB | Full API response |

### scheduler_jobs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| post_id | UUID FK → content_posts | |
| job_id | TEXT | APScheduler job ID |
| scheduled_at | TIMESTAMPTZ | |
| status | TEXT | pending / running / completed / failed |
| retry_count | INTEGER | default 0 |

### RLS Policies
All tables scoped via `profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())`. Three policies per table: SELECT own, INSERT own, UPDATE own. `social_accounts.access_token` has column-level security — only server-side functions can read.

## Component Tree

```
app/
├── layout.tsx                    # AuthProvider, ThemeProvider
├── page.tsx                      # Redirect to /dashboard
├── (auth)/
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/                  # Protected layout
│   ├── layout.tsx                # Sidebar, TopBar, ProfileSwitcher
│   ├── dashboard/page.tsx        # KPIDashboard (metric cards, Recharts)
│   ├── content-grid/page.tsx     # CalendarView, DayDetail
│   ├── posts/
│   │   ├── [id]/page.tsx         # PostEditorForm
│   │   └── new/page.tsx          # FormatSelector → PostEditorForm
│   ├── ideas/page.tsx            # IdeaBankList, IdeaCard, IdeaFilters
│   └── settings/
│       ├── strategy/page.tsx     # ArchetypeSelector, StrategyForm
│       ├── integrations/page.tsx # InstagramConnect, WhatsAppConfig
│       └── account/page.tsx

components/
├── auth/
│   ├── LoginForm.tsx
│   └── RegisterForm.tsx
├── profile/
│   ├── OnboardingWizard.tsx       # Stepper: archetype → voice → pillars → audience → goals
│   ├── ArchetypeCard.tsx
│   └── StrategyForm.tsx
├── grid/
│   ├── CalendarView.tsx           # Month/week/day toggle, renders PostCard per day
│   ├── PostCard.tsx               # Title, pillar color dot, format badge, status
│   ├── DayDetail.tsx              # Sidebar/popover with full day posts
│   ├── PillarDonut.tsx            # Recharts donut chart
│   └── FormatBalanceAlert.tsx     # Warning when format skew >70%
├── posts/
│   ├── PostEditorForm.tsx         # Dynamic fields by format
│   ├── FormatSelector.tsx         # Card grid: Story/Carousel/Reel/Live
│   ├── CaptionSuggestions.tsx     # 3 AI captions with "Use This"
│   ├── HashtagSuggestions.tsx     # 5-10 tags, clickable add
│   └── MediaUploader.tsx          # Image/video upload to Supabase Storage
├── ideas/
│   ├── IdeaBankList.tsx           # Filterable list/grid
│   ├── IdeaCard.tsx               # Title, pillar badge, format badge, source
│   ├── IdeaFilters.tsx            # Pillar/status/source filters
│   └── NewIdeaModal.tsx
├── dashboard/
│   ├── KpiCard.tsx                # Value + trend arrow + delta
│   ├── TimeSeriesChart.tsx        # Recharts LineChart with range selector
│   └── ArchetypeTopMetrics.tsx    # Conditional layout based on archetype
├── settings/
│   ├── InstagramConnect.tsx       # OAuth button, status display
│   └── WhatsAppConfig.tsx         # QR code, phone display
└── shared/
    ├── DragProvider.tsx           # dnd-kit context wrapper
    ├── DraggableIdea.tsx          # Wraps IdeaCard for drag
    └── DroppableDate.tsx          # Calendar date cell as drop target
```

## Agent Interfaces

```python
# backend/app/agents/orchestrator.py
class Orchestrator:
    """Coordinates agent execution, dispatches to specific agents by task type."""
    async def run_task(self, task: AgentTask, profile_id: str) -> AgentResult: ...
    async def run_batch(self, tasks: list[AgentTask]) -> list[AgentResult]: ...
    async def get_agent(self, agent_type: AgentType) -> BaseAgent: ...

# backend/app/agents/base.py
class BaseAgent(ABC):
    profile: ProfileStrategy  # Injected via constructor, contains voice/pillars/archetype

# backend/app/agents/content_creator.py
class ContentCreatorAgent(BaseAgent):
    """Generates captions, hashtags, and format recommendations via Ollama."""
    async def suggest_captions(self, post_context: str, n: int = 3) -> list[CaptionSuggestion]: ...
    async def suggest_hashtags(self, caption: str, pillars: list[str]) -> list[str]: ...
    async def suggest_format(self, idea: str) -> FormatRecommendation: ...
    async def generate_weekly_ideas(self) -> list[ContentIdea]: ...

# backend/app/agents/trend_researcher.py
class TrendResearcherAgent(BaseAgent):
    """Fetches trending topics/hashtags from Instagram and web."""
    async def get_trending_hashtags(self, pillars: list[str]) -> list[str]: ...
    async def get_trending_topics(self, niche: str) -> list[TrendTopic]: ...

# backend/app/agents/scheduler_agent.py
class SchedulerAgent(BaseAgent):
    """Manages APScheduler jobs for post publishing."""
    async def schedule_post(self, post_id: str, scheduled_for: datetime) -> str: ...
    async def cancel_post(self, post_id: str) -> bool: ...
    async def publish_post(self, post_id: str) -> PublishResult: ...
    async def retry_failed(self, post_id: str) -> PublishResult: ...

# backend/app/agents/analytics_agent.py
class AnalyticsAgent(BaseAgent):
    """Fetches Instagram metrics and computes KPIs."""
    async def fetch_metrics(self, account_id: str) -> MetricsSnapshot: ...
    async def get_timeseries(self, days: int) -> list[MetricsSnapshot]: ...
    async def compute_engagement_rate(self, likes: int, comments: int, reach: int) -> float: ...

# backend/app/agents/idea_bank.py
class IdeaBankAgent(BaseAgent):
    """Processes incoming ideas, auto-categorizes, suggests formats."""
    async def process_whatsapp_message(self, text: str, media: list[str]) -> Idea: ...
    async def auto_tag_pillar(self, description: str) -> str | None: ...
    async def suggest_format_from_text(self, description: str) -> FormatRecommendation | None: ...
```

## Data Flows

### Content Creation Loop
```
User edits draft ──→ POST /agents/captions
                        │
              ContentCreatorAgent.loads strategy profile
                        │
              Builds prompt: "Archetype: {archetype}.
                Voice: {voice}. Pillars: {pillars}.
                Audience: {audience}. Suggest 3 captions for: {post_content}"
                        │
              POST localhost:11434/api/generate (Ollama)
              model: llama3.1, stream: false
                        │
              Parse response → 3 captions → HTTP 200 [{text, tone, length}]
                        │
              User clicks "Use This" → caption fills editor
                        │
              User clicks "Suggest Hashtags"
              → same flow, prompt asks for 5-10 niche + trending tags
```

### Scheduling & Publishing
```
User sets date → POST /posts/{id}/schedule {scheduled_for}
                        │
              backend validates future timestamp
                        │
              SchedulerAgent.schedule_post(post_id, scheduled_for)
                        │
              APScheduler.add_job(
                func=publish_post,
                trigger="date",
                run_date=scheduled_for
              ) → returns job_id
                        │
              DB: content_posts.status = "scheduled"
              DB: scheduler_jobs {post_id, job_id, scheduled_at, status: "pending"}
                        │
              ── at scheduled_for ──
                        │
              SchedulerAgent.publish_post(post_id)
                        │
              Instagram Graph API: POST /{ig-user-id}/media
                {media_type, media_url, caption, access_token}
                        │
              On success → POST /{ig-user-id}/media_publish
                {creation_id, access_token}
                        │
              DB: status = "published", platform_post_id, platform_permalink
                        │
              AnalyticsAgent.fetch_metrics() → daily snapshot
```

### Idea Capture Flow
```
┌─ In-app ──────────────────────────────────┐
│ User types title + description             │
│   → POST /ideas                          │
│   → DB: content_ideas {source: "manual"} │
└───────────────────────────────────────────┘

┌─ WhatsApp ───────────────────────────────────────────────────┐
│ User forwards message → WhatsApp Cloud API webhook            │
│   → POST /ideas/whatsapp (from backend webhook handler)       │
│   → IdeaBankAgent.process_whatsapp_message(text, media)      │
│     → Suggests pillar via keyword matching on description     │
│     → Suggests format via Ollama: "Is this educational?      │
│        Promotional? Lifestyle?" → format recommendation      │
│   → DB: content_ideas {source: "whatsapp", media_refs}      │
└──────────────────────────────────────────────────────────────┘

┌─ Convert to Post ────────────────────────────────────────────┐
│ User drags IdeaCard → DroppableDate in CalendarView           │
│   → dnd-kit onDragEnd → PUT /ideas/{id}/convert             │
│   → DB: idea.status = "converted", idea.converted_to = post │
│   → DB: content_posts created prefilled with idea data       │
│   → Router push to /posts/{new_post_id} for editing          │
└──────────────────────────────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/main.py` | Create | FastAPI app entry, CORS, router includes |
| `backend/app/core/config.py` | Create | Pydantic Settings, env loading |
| `backend/app/core/security.py` | Create | Fernet token encryption/decryption |
| `backend/app/core/database.py` | Create | Supabase client singleton |
| `backend/app/api/auth.py` | Create | Auth routes (R001) |
| `backend/app/api/profiles.py` | Create | Profile & strategy routes (R002–R004) |
| `backend/app/api/social.py` | Create | Instagram OAuth routes |
| `backend/app/api/ideas.py` | Create | Idea CRUD + WhatsApp webhook (R005–R007, R023–R024) |
| `backend/app/api/posts.py` | Create | Post CRUD + schedule/publish (R011–R012, R017–R018) |
| `backend/app/api/agents.py` | Create | AI suggestion endpoints (R013–R016) |
| `backend/app/api/grid.py` | Create | Content grid + distribution (R008–R010) |
| `backend/app/api/dashboard.py` | Create | KPI + timeseries endpoints (R020–R022) |
| `backend/app/agents/__init__.py` | Create | Agent exports |
| `backend/app/agents/orchestrator.py` | Create | Agent coordinator |
| `backend/app/agents/base.py` | Create | Abstract base agent |
| `backend/app/agents/content_creator.py` | Create | Prompt builder, Ollama client |
| `backend/app/agents/trend_researcher.py` | Create | Instagram scraping/API trends |
| `backend/app/agents/scheduler_agent.py` | Create | APScheduler management |
| `backend/app/agents/analytics_agent.py` | Create | Metrics fetch + compute |
| `backend/app/agents/idea_bank.py` | Create | Auto-categorization |
| `backend/app/models/` | Create | SQLAlchemy models (all tables) |
| `backend/app/schemas/` | Create | Pydantic request/response schemas |
| `backend/requirements.txt` | Create | FastAPI, supabase-py, apscheduler, cryptography, httpx, ollama |
| `frontend/app/layout.tsx` | Create | Root layout + providers |
| `frontend/app/(auth)/login/page.tsx` | Create | Login page |
| `frontend/app/(dashboard)/dashboard/page.tsx` | Create | KPI dashboard |
| `frontend/app/(dashboard)/content-grid/page.tsx` | Create | Calendar view |
| `frontend/app/(dashboard)/posts/new/page.tsx` | Create | New post wizard |
| `frontend/app/(dashboard)/ideas/page.tsx` | Create | Idea bank |
| `frontend/components/...` | Create | All components per tree above |
| `frontend/lib/api.ts` | Create | FastAPI client |
| `frontend/package.json` | Create | next, react, recharts, dnd-kit |

(N = ~50 Create, M = 0 Modify, K = 0 Delete — greenfield)

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | Pydantic schemas, agent prompt builders, engagement rate calc | pytest |
| Unit | APScheduler job registration, Fernet encrypt/decrypt | pytest |
| Integration | API routes (FastAPI TestClient), Supabase local/remote | pytest + httpx |
| Integration | Ollama client (mock responses), WhatsApp webhook parsing | pytest with mocks |
| E2E | Full flow: register → create post → schedule → mock publish | Playwright (future) |

## Migration / Rollout

No migration required — greenfield project. Alembic will generate initial migration with all tables. Supabase migrations run on first deploy. Token encryption keys generated on first `uvicorn` start via `openssl rand -hex 32`.

## Open Questions

- [ ] Instagram Graph API app review timeline — must start API onboarding week 1 (spec R022 risk)
- [ ] WhatsApp Cloud API requires Meta Business Verification — confirm eligibility
- [ ] Ollama 7B model selection — test Llama 3.1 8B vs Mistral 7B for caption quality
- [ ] Supabase free tier 500MB DB — define row retention policy for metrics_snapshots
