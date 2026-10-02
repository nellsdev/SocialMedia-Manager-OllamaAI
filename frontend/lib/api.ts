/**
 * Typed FastAPI client for the Social Media Manager backend.
 *
 * Usage:
 *   const api = new ApiClient('http://localhost:8000');
 *   const ideas = await api.getIdeas();
 */

interface RequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  // ---- Auth ----

  async getSessionToken(): Promise<string | null> {
    // In a client component, read from cookie or Supabase client.
    // For now this returns null — the actual token is injected via
    // Authorization header from the AuthProvider context.
    return typeof window !== "undefined"
      ? localStorage.getItem("session_token")
      : null;
  }

  private async headers(extra?: Record<string, string>): Promise<Record<string, string>> {
    const h = { ...this.defaultHeaders, ...extra };
    const token = await this.getSessionToken();
    if (token) {
      h["Authorization"] = `Bearer ${token}`;
    }
    return h;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    opts?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const h = await this.headers(opts?.headers);

    const res = await fetch(url, {
      method,
      headers: h,
      body: body ? JSON.stringify(body) : undefined,
      signal: opts?.signal,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      const error = new ApiError(res.status, errorData.detail || "Unknown error", path);

      if (res.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("session_token");
        document.cookie = "session_token=; path=/; max-age=0";
        window.location.href = "/login";
      }

      throw error;
    }

    return res.json() as Promise<T>;
  }

  private async upload<T>(path: string, form: FormData): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    // Do NOT set Content-Type manually: the browser must generate the
    // multipart boundary. Only the Authorization header is attached.
    const h: Record<string, string> = {};
    const token = await this.getSessionToken();
    if (token) {
      h["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(url, {
      method: "POST",
      headers: h,
      body: form,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      const error = new ApiError(res.status, errorData.detail || "Unknown error", path);

      if (res.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("session_token");
        document.cookie = "session_token=; path=/; max-age=0";
        window.location.href = "/login";
      }

      throw error;
    }

    return res.json() as Promise<T>;
  }

  // ---- Auth ----

  register(email: string, password: string) {
    return this.request<{ user_id: string; message: string }>("POST", "/api/auth/register", { email, password });
  }

  login(email: string, password: string) {
    return this.request<{ session_token: string; user_id: string }>("POST", "/api/auth/login", { email, password });
  }

  getSession() {
    return this.request<{ user: Record<string, unknown>; profile: Record<string, unknown> | null }>("GET", "/api/auth/session");
  }

  // ---- Profiles ----

  getMyProfile() {
    return this.request<Record<string, unknown>>("GET", "/api/profiles/me");
  }

  updateStrategy(data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>("PUT", "/api/profiles/me/strategy", data);
  }

  listArchetypes() {
    return this.request<Array<Record<string, unknown>>>("GET", "/api/profiles/me/archetypes");
  }

  // ---- Social / Instagram ----

  connectInstagram(redirectUri: string) {
    return this.request<{ auth_url: string }>("POST", "/api/social/instagram/connect", { redirect_uri: redirectUri });
  }

  instagramCallback(code: string) {
    return this.request<Record<string, unknown>>("POST", "/api/social/instagram/callback", { code });
  }

  getInstagramStatus() {
    return this.request<{ connected: boolean; account: Record<string, unknown> | null }>("GET", "/api/social/instagram/status");
  }

  // ---- Ideas ----

  getIdeas(filters?: { pillar?: string; status?: string; source?: string }) {
    const params = new URLSearchParams();
    if (filters?.pillar) params.set("pillar", filters.pillar);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.source) params.set("source", filters.source);
    const qs = params.toString();
    return this.request<Array<Record<string, unknown>>>("GET", `/api/ideas${qs ? `?${qs}` : ""}`);
  }

  createIdea(data: { title: string; description?: string; suggested_format?: string; content_pillar?: string }) {
    return this.request<Record<string, unknown>>("POST", "/api/ideas", data);
  }

  convertIdea(ideaId: string) {
    return this.request<{ post_id: string }>("PUT", `/api/ideas/${ideaId}/convert`);
  }

  // ---- Posts ----

  getPosts(filters?: { status?: string; format?: string }) {
    const params = new URLSearchParams();
    if (filters?.status) params.set("status_filter", filters.status);
    if (filters?.format) params.set("format_filter", filters.format);
    const qs = params.toString();
    return this.request<Array<Record<string, unknown>>>("GET", `/api/posts${qs ? `?${qs}` : ""}`);
  }

  createPost(data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>("POST", "/api/posts", data);
  }

  updatePost(postId: string, data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>("PUT", `/api/posts/${postId}`, data);
  }

  // ---- Grid ----

  getGrid(year?: number, month?: number) {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (month) params.set("month", String(month));
    const qs = params.toString();
    return this.request<{ days: Array<{ date: string; posts: Array<Record<string, unknown>> }> }>(
      "GET", `/api/grid${qs ? `?${qs}` : ""}`
    );
  }

  getGridDistribution() {
    return this.request<{ pillars: Array<Record<string, unknown>>; formats: Array<Record<string, unknown>>; total_posts: number }>(
      "GET", "/api/grid/distribution"
    );
  }

  // ---- Agents / AI ----

  suggestCaptions(postContext: string, n: number = 3) {
    return this.request<{ options: Array<{ text: string; tone: string; length: string; pillar: string }> }>(
      "POST", "/api/agents/captions", { post_context: postContext, n }
    );
  }

  suggestHashtags(caption: string, pillars?: string[]) {
    return this.request<{ hashtags: string[] }>(
      "POST", "/api/agents/hashtags", { caption, pillars }
    );
  }

  suggestFormat(idea: string) {
    return this.request<{ format: string; reasoning: string }>(
      "POST", "/api/agents/format", { idea }
    );
  }

  generateWeeklyIdeas() {
    return this.request<{ ideas: Array<{ title: string; description: string; suggested_format: string; content_pillar: string }> }>(
      "POST", "/api/agents/weekly-ideas"
    );
  }

  // ---- Onboarding / Research ----

  onboardingTurn(data: { history: Array<{ role: string; content: string }>; current_state: string; niche?: string; archetype?: string }) {
    return this.request<{ question: string }>("POST", "/api/agents/onboarding/turn", data);
  }

  onboardingFinish(data: { history: Array<{ role: string; content: string }> }) {
    return this.request<{ profile: Record<string, unknown>; niche_analysis: Record<string, unknown> }>("POST", "/api/agents/onboarding/finish", data);
  }

  getOnboardingResearch() {
    return this.request<{ status: string; niche_analysis: Record<string, unknown> }>("GET", "/api/agents/onboarding/research");
  }

  // ---- Onboarding visual refs + starter kit ----

  onboardingVisualRef(file: File) {
    const form = new FormData();
    form.append("file", file);
    return this.upload<{
      url: string;
      dominant_colors: Array<{ hex: string; name: string }>;
      mood_hints: string[];
      style_hint: string;
    }>("/api/agents/onboarding/visual-ref", form);
  }

  generateStarterKit(data: { niche?: string; niche_analysis?: Record<string, unknown> }) {
    return this.request<{ brand_starter: Record<string, unknown> }>(
      "POST",
      "/api/agents/onboarding/starter-kit",
      data
    );
  }

  // ---- Scheduling / Publishing ----

  schedulePost(postId: string, scheduledFor: string) {
    return this.request<{ status: string; job_id: string | null }>(
      "POST", `/api/posts/${postId}/schedule`, { scheduled_for: scheduledFor }
    );
  }

  publishPost(postId: string) {
    return this.request<{ status: string; platform_post_id: string | null; platform_permalink: string | null; failure_reason: string | null }>(
      "POST", `/api/posts/${postId}/publish`
    );
  }

  retryPublish(postId: string) {
    return this.request<{ status: string; platform_post_id: string | null; platform_permalink: string | null; failure_reason: string | null }>(
      "POST", `/api/posts/${postId}/retry`
    );
  }

  // ---- Dashboard ----

  getDashboardKpis() {
    return this.request<{
      followers: number;
      likes: number;
      comments: number;
      reach: number;
      engagement_rate: number;
      followers_delta: number;
      engagement_delta: number;
    }>("GET", "/api/dashboard/kpis");
  }

  getDashboardTimeseries(metric: string = "followers", days: number = 30) {
    const params = new URLSearchParams({ metric, days: String(days) });
    return this.request<{ metric: string; days: number; data: Array<{ date: string; value: number }> }>(
      "GET",
      `/api/dashboard/timeseries?${params.toString()}`
    );
  }

  // ---- WhatsApp ----

  sendWhatsappIdea(message: string, media?: string[]) {
    return this.request<Record<string, unknown>>(
      "POST", "/api/ideas/whatsapp", { message, media }
    );
  }

  getWhatsAppStatus() {
    return this.request<{ connected: boolean; phone: string | null; qr_code: string | null }>(
      "GET", "/api/whatsapp/status"
    );
  }

  connectWhatsApp(phone: string) {
    return this.request<{ qr_code: string; connected: boolean }>(
      "POST", "/api/whatsapp/connect", { phone }
    );
  }
}

export class ApiError extends Error {
  status: number;
  path: string;

  constructor(status: number, detail: string, path: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
  }
}

// Singleton
let _api: ApiClient | null = null;

export function getApi(): ApiClient {
  if (!_api) {
    _api = new ApiClient();
  }
  return _api;
}
