# Conversational Onboarding + Brand Research

**Estado**: Completado (Fases A/B/C implementadas y verificadas end-to-end)
**Feature**: Onboarding conversacional guiado por LLM + research de nicho persistido

## Contexto
El usuario quiere que el onboarding sea una conversación donde el modelo conozca
al creador (qué quiere mostrar, si arranca de cero o tiene contenido, audiencia,
referencias, objetivos) y después investigue tendencias y cuentas modelo del
nicho para producir insights que se persistan en el perfil.

## Decisiones cerradas
1. Research con conocimiento del modelo (Ollama) primero; arquitectura por
   interfaz lista para swap a datos reales de Instagram Graph API después.
2. El research se persiste en el perfil del usuario.
3. El onboarding conversacional es el PRIMER paso; el resto (voz, pilares,
   arquetipo) se pre-llenan con lo aprendido.

## Fases
- Fase A: OnboardingAgent + endpoints de turnos + persistencia del perfil ✅
- Fase B: Research persistido (interfaz TrendDataSource + fuente conocimiento) ✅
- Fase C: Frontend — pantalla de chat conversacional + resumen editable ✅

## Evidencia (commits en el main saneado post filter-repo)
- 9781a2b feat(onboarding): conversational chat UI with editable summary and research polling
- 1662143 feat(onboarding): language-aware research, aesthetic state, starter kit
- 132191a feat(onboarding): upload visual references with auto color-palette extraction
- 12a0ae4 feat(onboarding): aesthetic image-upload step + on-demand starter kit UI
- bafaef1 fix(ui): fill page width with two-column onboarding layout
- c1f898c fix(onboarding): tolerant JSON parsing, language-aware research, session profile read
  (verificación end-to-end en sesión del agente: profile completo devuelto —
  language, brand_starter, niche_analysis, brand_colors hex, archetype)

## Log
- L1: Request original del usuario: onboarding conversacional que conozca al
  creador + research de nicho persistido en el perfil.
- L2: Fix raíz: anon client no reenviaba el JWT en queries de tablas → todos
  los endpoints de profile usaban Bearer token.
- L3: 2026-09-30 — incidente de credencial: ENV_SETUP.md contenía clave Fernet
  real; rotada, docs con comando de generación, historial saneado con
  git filter-repo + force push. Este documento se restauró tras el saneado.
