"""Conversational onboarding agent.

Guides a new creator through a structured conversation to discover their
personal brand: what they want to show, whether they start from zero or have
existing content, their audience, references, and goals.

The agent is stateless by design: the API layer holds the conversation
history and the current state; this class only builds prompts and parses
structured extractions from Ollama.
"""

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ordered conversation states. The system decides the order; the model
# writes the natural-language question for each state based on context.
STATES: list[tuple[str, str]] = [
    (
        "topic",
        "¿Qué querés mostrar en tus redes? Contame con tus palabras: tu tema, "
        "tu pasión, lo que te interesa compartir con el mundo.",
    ),
    (
        "starting_point",
        "¿Arrancás de cero o ya tenés contenido publicado? Contame cómo está "
        "tu situación hoy.",
    ),
    (
        "content_review",
        "Contame qué tenés hoy en tu perfil (o qué te gustaría tener) y qué "
        "te gustaría mejorar. ¿Qué funciona y qué no te convence?",
    ),
    (
        "audience",
        "¿A quién querés llegar? Describime tu audiencia ideal: edad, intereses, "
        "problemas que resolvés.",
    ),
    (
        "references",
        "¿Qué cuentas o creadores te inspiran en tu área? Nombrame los que seguís "
        "o admiras, aunque sea uno o dos.",
    ),
    (
        "goals",
        "¿Qué querés lograr en los próximos 3 meses? Puede ser seguidores, "
        "lanzar un producto, autoridad, ventas, comunidad... Decime tus metas.",
    ),
]

_STATE_HINT: dict[str, str] = {key: hint for key, hint in STATES}


class OnboardingAgent:
    """Builds conversational prompts and extracts a structured profile draft."""

    MODEL = "qwen2.5:7b"

    # ------------------------------------------------------------------
    # Next question
    # ------------------------------------------------------------------

    async def next_prompt(
        self,
        history: list[dict],
        current_state: str,
        niche: str | None = None,
        archetype: str | None = None,
    ) -> str:
        """Return the next conversational question for the current state."""
        context = self._build_context_lines(history, niche, archetype)
        state_hint = _STATE_HINT.get(current_state, "")
        parts = [
            "Eres un coach de marca personal que guía a un creador con preguntas "
            "cortas y naturales, una a la vez. Tu objetivo es conocerlo para "
            "definir su estrategia de contenido.",
        ]
        if context:
            parts.append("Contexto de la conversación hasta ahora:")
            parts.append(context)
        parts.append("")
        parts.append(f"Objetivo de esta pregunta: {state_hint or current_state}")
        parts.append("")
        parts.append(
            "Escribí UNA sola pregunta corta (1 a 2 oraciones) en español, "
            "natural y específica según lo que ya contó el creador. "
            "No expliques nada más, no agregues texto extra."
        )
        prompt = "\n".join(parts)
        raw = await self._ollama_generate(prompt)
        return self._extract_question(raw)

    # ------------------------------------------------------------------
    # Profile extraction (finish)
    # ------------------------------------------------------------------

    async def extract_profile_draft(self, history: list[dict]) -> dict:
        """Extract a structured profile draft from the full conversation."""
        context = self._build_history_text(history)
        archetypes = self._archetype_summary()
        prompt = (
            "Eres un estratega de marca personal. Analizá la siguiente "
            "conversación con un creador y extraé su perfil de marca.\n\n"
            f"Conversación:\n{context}\n\n"
            "Arquetipos de creador disponibles (elegí el que mejor encaje):\n"
            f"{archetypes}\n\n"
            'Respondé SOLO con un objeto JSON con estas claves: '
            '"niche" (string, el tema central), '
            '"archetype" (string, uno de los id válidos), '
            '"voice_description" (string, cómo habla/publica el creador), '
            '"content_pillars" (array de 2 a 5 strings, los pilares de contenido), '
            '"target_audience" (string, la audiencia ideal), '
            '"goals" (string, sus objetivos), '
            '"reference_accounts" (array de strings, cuentas que mencionó o que '
            'encajan), '
            '"starting_point" (string, "from_zero" o "has_content"). '
            "Si un dato no se menciona, usá un valor razonable o string vacío. "
            "Sin markdown, sin explicación."
        )
        raw = await self._ollama_generate(prompt)
        return self._parse_draft(raw)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context_lines(
        history: list[dict], niche: str | None, archetype: str | None
    ) -> str:
        lines: list[str] = []
        for turn in history[-6:]:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                lines.append(f"Creador: {content[:200]}")
            elif role == "assistant":
                lines.append(f"Asistente: {content[:200]}")
        if niche:
            lines.append(f"Nicho detectado hasta ahora: {niche}")
        if archetype:
            lines.append(f"Posible arquetipo: {archetype}")
        return "\n".join(lines)

    @staticmethod
    def _build_history_text(history: list[dict]) -> str:
        lines: list[str] = []
        for turn in history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                lines.append(f"→ {content[:400]}")
            elif role == "assistant":
                lines.append(f"← {content[:400]}")
        return "\n".join(lines)

    @staticmethod
    def _archetype_summary() -> str:
        return (
            "aspiring_influencer: crecer audiencia y atraer colaboraciones; "
            "authority_professional: construir autoridad y pensamiento líder; "
            "personal_sharing: conectar auténticamente con una audiencia cercana; "
            "business_owner: vender y generar leads; "
            "community_builder: unir gente alrededor de un interés común."
        )

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_question(raw: str) -> str:
        cleaned = raw.strip().strip('"').strip("'")
        # Remove common prefixes the model may add
        for prefix in ("Pregunta:", "Pregunta: ", "Pregunta:  ", "Q:", "Asistente: "):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
        return cleaned or "Contame más sobre eso."

    def _parse_draft(self, raw: str) -> dict:
        cleaned = self._clean_json(raw)
        try:
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                data = {}
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Failed to parse profile draft: %s", exc)
            return self._empty_draft()

        valid_archetypes = {
            "aspiring_influencer",
            "authority_professional",
            "personal_sharing",
            "business_owner",
            "community_builder",
        }
        archetype = data.get("archetype", "")
        if archetype not in valid_archetypes:
            archetype = ""

        pillars = data.get("content_pillars", [])
        if isinstance(pillars, str):
            pillars = [p.strip() for p in pillars.split(",") if p.strip()]
        pillars = [str(p) for p in (pillars or [])][:5]

        refs = data.get("reference_accounts", [])
        if isinstance(refs, str):
            refs = [r.strip() for r in refs.split(",") if r.strip()]
        refs = [str(r) for r in (refs or [])][:10]

        return {
            "niche": str(data.get("niche", "")),
            "archetype": archetype,
            "voice_description": str(data.get("voice_description", "")),
            "content_pillars": pillars,
            "target_audience": str(data.get("target_audience", "")),
            "goals": str(data.get("goals", "")),
            "reference_accounts": refs,
            "starting_point": data.get("starting_point", "from_zero"),
        }

    @staticmethod
    def _empty_draft() -> dict:
        return {
            "niche": "",
            "archetype": "",
            "voice_description": "",
            "content_pillars": [],
            "target_audience": "",
            "goals": "",
            "reference_accounts": [],
            "starting_point": "from_zero",
        }

    # ------------------------------------------------------------------
    # Ollama client
    # ------------------------------------------------------------------

    async def _ollama_generate(self, prompt: str) -> str:
        import httpx
        from tenacity import (
            retry,
            stop_after_attempt,
            wait_exponential,
            retry_if_exception_type,
        )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(
                (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)
            ),
        )
        async def _call() -> str:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                }
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")

        return await _call()

    @staticmethod
    def _clean_json(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            first_nl = raw.find("\n")
            if first_nl != -1:
                raw = raw[first_nl + 1 :]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return raw