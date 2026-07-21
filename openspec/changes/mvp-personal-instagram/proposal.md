# Proposal: MVP — Personal Profile + Instagram

> **Change**: `mvp-personal-instagram`
> **Status**: Proposal
> **Date**: 2026-06-25
> **Author**: Nelly Rodríguez

---

## Problem Statement

Social media creators managing multiple platforms face five core challenges:

1. **Fragmented workflow** — Posting, scheduling, and analytics live in separate platforms with no unified view
2. **One-size-fits-all tools** — Existing tools treat every creator the same. An aspiring influencer, a professional building authority, and a business owner have radically different goals, yet tools offer the same generic features
3. **AI lacks persistence** — Generic AI assistants don't remember the creator's voice, tone, brand identity, or posting patterns across sessions
4. **No strategic guidance** — Most tools are schedulers, not strategists. Creators don't need more posting slots; they need to know WHAT to post, WHY, and for WHOM
5. **Inexpensive tools are limited** — Free tiers of existing tools (Buffer, Hootsuite) restrict features; paid plans are costly for individual creators

The creator (Nelly) manages three distinct personas (personal, collective, professional) across Instagram, TikTok, Facebook, X/Threads, WhatsApp, and LinkedIn — entirely manually. No existing tool solves the combination of multi-persona management, archetype-aware AI strategy, AI-assisted content with memory, and affordable collaboration.

## Proposed Solution

A local-first multi-agent system that evolves into a SaaS platform. The MVP validates the core loop for a single persona (Personal) on a single platform (Instagram):

```
Connect Instagram → Create post with AI assistance → Schedule → Publish → View metrics
```

### Core Differentiators
- **Creator archetype system** — Users define what type of creator they are (aspiring influencer, authority professional, personal sharing, business owner, community builder, etc.). The entire system adapts: content suggestions, success metrics, tone guidance, and strategy recommendations change based on archetype
- **AI with persona memory** — The system remembers the creator's voice, tone, content pillars, objectives, and target audience. AI suggestions are tailored to the persona, not generic
- **Content strategy coach, not just a scheduler** — Visual content grid showing pillar distribution, gaps, and balance. The system helps plan WHAT to post, not just WHEN
- **Human-first design** — AI assists with copy, captions, ideas, and strategy but does NOT replace the creator's visual/manual design process
- **Multi-agent architecture** — Specialized agents (Trend Researcher, Content Creator, Scheduler, Analytics Agent) collaborate autonomously
- **Idea bank with multi-channel capture** — Never lose an idea: capture via in-app notes, WhatsApp messages
- **Local-first, zero-cost MVP** — Everything runs on the creator's machine with free-tier services

## Scope

### In Scope (MVP)

| Area | Detail |
|------|--------|
| **Auth** | User registration and login via Supabase Auth (magic link / email) |
| **Profile & Strategy Setup** | Define brand voice, content pillars, target audience, goals, and visual references per profile |
| **Creator Archetype** | Select creator archetype (e.g., aspiring influencer, authority professional, personal sharing, business owner, community builder). System adapts content strategy, metrics focus, and AI tone based on archetype |
| **Social Accounts** | Connect ONE Instagram business account via Meta Graph API |
| **Idea Bank** | Quick-capture ideas via in-app text input + WhatsApp message forwarding. Tag by content pillar AND suggested format (Story, Carousel, Reel, Live). Search, filter, and convert ideas into posts |
| **Content Grid / Parrilla** | Visual calendar showing planned content by day/week/month. Highlights pillar distribution, posting frequency, format mix, and scheduling gaps. Drag-and-drop planning |
| **Post Management** | Create drafts with format selection: Story, Carousel, Reel, or Live. Edit, save as draft, schedule, publish. Each format has tailored fields (e.g., carousel = multiple images, reel = video + cover) |
| **AI Content Assistant** | Real-time: suggests captions, hashtags, and **format recommendations** while writing — tailored to the profile's archetype, voice, and strategy. Batch: generates weekly content ideas from trends, each with format suggestion (e.g., "this topic works better as a Reel for your audience") |
| **Scheduling** | Calendar view, schedule posts, automated publishing at specified times |
| **Basic Dashboard** | KPIs: followers, likes, comments, reach, engagement rate. Line charts over time. Metrics adapt to archetype (e.g., authority creators see engagement quality; brand creators see conversion signals) |
| **API Integration** | Single Instagram connection via Meta Graph API |

### Out of Scope (MVP)

- Any platform other than Instagram
- Collective and Professional profiles
- Team collaboration / multi-user
- WhatsApp community management (beyond idea capture)
- Voice memo / audio transcription for idea capture
- Archetype discovery quiz (onboarding wizard for new creators)
- Advanced analytics (predictive, recommendations, sentiment analysis)
- SaaS billing/subscriptions
- Mobile app
- Public API

## Approach

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.12+ / FastAPI | Async-native, Python ecosystem for AI/data, strong typing with Pydantic |
| Frontend | Next.js 14+ (App Router) | Industry standard for SaaS, SSR, API routes, huge ecosystem |
| Database | PostgreSQL via Supabase | Free tier, built-in auth, RLS, realtime subscriptions |
| AI (local) | Ollama + Llama 3.1 8B / Mistral | Free, local inference, no API costs during development |
| AI (cloud, future) | OpenAI / Claude API | Upgrade path when users need better quality |
| Agent Framework | Custom Python classes (MVP) → CrewAI (post-MVP) | Learn fundamentals first, abstract later |
| Task Scheduling | APScheduler | Simple cron-like scheduling without external dependencies |
| Hosting (dev) | Local: uvicorn + next dev | Zero-cost development environment |

### Architecture Overview

```
┌──────────────┐      ┌─────────────────────────────────────┐
│   Next.js    │◄────►│           FastAPI Backend            │
│   Frontend   │ REST │                                     │
│              │      │  ┌───────────────────────────────┐  │
│  Dashboard   │      │  │        Agent System           │  │
│  Post Editor │      │  │  ┌──────┐ ┌──────┐ ┌──────┐  │  │
│  Calendar    │      │  │  │Trend │ │Content│ │Analyt│  │  │
│  Auth UI     │      │  │  │Resrch│ │Creator│ │Agent │  │  │
└──────────────┘      │  │  └──────┘ └──────┘ └──────┘  │  │
                      │  │  ┌─────────────────────────┐  │  │
                      │  │  │   Scheduler / Publisher  │  │  │
                      │  │  └─────────────────────────┘  │  │
                      │  └───────────────────────────────┘  │
                      │                                     │
                      │  ┌───────────────────────────────┐  │
                      │  │       External APIs           │  │
                      │  │  Meta Graph API (Instagram)   │  │
                      │  │  Ollama (local LLM)           │  │
                      │  └───────────────────────────────┘  │
                      └─────────────────────────────────────┘
```

### Agent Architecture (MVP)

For the MVP, agents are simple Python classes managed by an `Orchestrator`:

1. **ContentCreatorAgent** — Generates captions, hashtags, and post ideas using Ollama. Reads the profile's **strategy profile** (voice, tone, content pillars, goals, target audience) to produce on-brand suggestions. Maintains conversation memory for consistent recommendations.

2. **TrendResearcherAgent** — Fetches trending topics/hashtags relevant to the profile's niche and content pillars from Instagram and web sources.

3. **SchedulerAgent** — Manages the post queue, triggers publishing at scheduled times.

4. **AnalyticsAgent** — Fetches Instagram metrics via Graph API, computes KPIs, stores daily snapshots.

5. **IdeaBankAgent** *(lightweight)* — Processes incoming ideas (in-app text, forwarded WhatsApp messages), auto-categorizes by content pillar, and surfaces them when relevant during post creation.

### Creator Archetype System

The archetype is the **north star** of the entire system. It shapes every interaction:

```
User selects archetype ──► System loads archetype configuration
    │                          │
    │                    ┌─────┴──────────┐
    │                    │  Content tone   │
    │                    │  Metrics focus  │
    │                    │  Strategy tips  │
    │                    │  AI personality │
    │                    └────────────────┘
    │
    ▼
User customizes: voice, pillars, audience, goals
    │
    ▼
System now operates in "archetype mode"
```

**Example archetypes and how they change system behavior:**

| Archetype | Goal | AI Tone | Key Metrics | Content Strategy |
|-----------|------|---------|-------------|-----------------|
| Aspiring Influencer | Grow audience, attract brands | Trend-aware, engaging | Followers, reach, saves | Viral hooks, collaborations, trends |
| Authority Professional | Build credibility | Expert, educational | Engagement quality, shares | Thought leadership, case studies, insights |
| Personal Sharing | Connect with close audience | Warm, authentic | Comments, interactions | Lifestyle, everyday moments |
| Business Owner | Drive sales, leads | Value-first, CTA-oriented | Clicks, conversions, ROI | Product demos, testimonials, offers |
| Community Builder | Engage collective | Inclusive, conversational | Participation rate, replies | Polls, discussions, UGC features |

The MVP includes **3-4 pre-defined archetypes** with customization. Future versions may include an archetype discovery quiz for new creators.

### Content Grid (Parrilla de Contenido)

A visual drag-and-drop calendar that answers three questions at a glance:

1. **¿Qué publico esta semana?** — See all scheduled posts in day/week/month view, filtered by format
2. **¿Estoy balanceado?** — Color-coded content pillars AND format badges show distribution (too many Reels? not enough Carousels? gaps in Stories?)
3. **¿Cumplo mi frecuencia?** — Daily/weekly posting targets vs. actuals, broken down by format
4. **¿Estoy usando el formato correcto?** — AI highlights if a content pillar is over/under-represented in a specific format

The grid is the central planning surface. Users drag ideas from the Idea Bank directly into calendar slots, where they become draft posts ready for AI assistance.

### Data Flow (Core Loop)

#### Strategy Setup (first-time)
```
User selects creator archetype ──► System pre-configures tone, metrics, strategy
User defines voice, content pillars ──► Stored in profile strategy
        target audience, goals
```

#### Idea Capture (ongoing)
```
┌──────────────────┐
│ In-app text note  │──► IdeaBankAgent categorizes
│ WhatsApp forward  │──► by pillar and stores
└──────────────────┘
                          │
                   User browses idea bank
                          │
                   Convert idea → post draft
```

#### Content Creation Loop
```
User writes draft ──► ContentCreatorAgent reads strategy profile
                           │
                    Agent suggests caption, hashtags, angles
                    (tailored to voice + pillars + audience)
                           │
                    User reviews & edits
                           │
                    Schedule post ──► SchedulerAgent queues it
                                           │
                                    Scheduled time triggers
                                           │
                                    PublisherAgent: API call → Instagram
                                           │
                                    Status update (success/fail)
                                           │
                                    AnalyticsAgent fetches metrics
                                           │
                                    Dashboard updates
```

## Success Criteria

1. User can register and log in
2. User can select a creator archetype and customize their strategy profile (voice, pillars, audience, goals)
3. User can connect an Instagram business account
4. User can capture an idea via in-app text note and via WhatsApp forwarding
5. Content Grid shows planned content with pillar color-coding and gap detection
6. User can drag an idea from the Idea Bank into the Content Grid to create a draft post
7. User can create a post draft selecting from Instagram formats (Story, Carousel, Reel, Live), with format-appropriate fields
8. AI Content Assistant suggests both content AND format recommendations based on the idea and archetype
9. User can schedule a post for future publishing
10. Post publishes automatically at the scheduled time via Instagram Graph API
11. Dashboard shows followers, likes, comments, reach, and engagement rate with daily snapshots
12. The full loop works for one persona (Personal) on one platform (Instagram)

## Rollback Plan

Since this is greenfield development with no production users during development:

| Scenario | Rollback Action |
|----------|----------------|
| Instagram API integration fails | Fall back to manual publishing with automated reminders |
| Local LLM quality too low | Switch to OpenAI API with minimal code changes (adapter pattern) |
| Database schema needs changes | Store schema version, use Supabase migrations (reversible) |
| Agent system too complex | Replace custom agents with simplified function-based pipeline |

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|-----------|
| Instagram API access denied (app review) | Medium | High | Start with Instagram Basic Display API for read-only; use Meta's self-review checklist early |
| Local LLM latency too high on CPU | Medium | Medium | Use small models (7B), cache responses, async generation |
| Token storage security | Low | High | Encrypt tokens at rest using Supabase Vault or Fernet |
| Scope creep during MVP | High | Medium | Strict MVP definition; defer any non-Instagram feature to v2 |
| Learning curve slows development | Medium | Medium | Follow learning path: FastAPI → Supabase → Next.js → Agents (sequential, not parallel) |

## Next Steps

1. **Spec** — Write detailed functional and technical specifications for each MVP component
2. **Design** — Create API contracts, database schema, component tree, agent interfaces
3. **Tasks** — Break design into implementable work units with effort estimates
4. **Apply** — Implement tasks incrementally with test coverage

---

*This proposal is the first SDD change (`mvp-personal-instagram`) of the social-media-manager project.*
