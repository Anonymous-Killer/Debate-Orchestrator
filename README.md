# Debate Orchestrator

Debate Orchestrator is a voice-first debate judging system for two-sided debates. It combines a FastAPI backend, a Next.js frontend, persistent debate state, live crowd-style scoring, speech-to-text transcription, and post-debate AI judging.

The project is designed around a central orchestrator rather than loose prompt chaining. The orchestrator owns the debate lifecycle, controls state transitions, invokes specialized services and agents, stores intermediate outputs, and produces a final verdict after the debate is explicitly ended.

## Current Product Flow

1. A user creates a debate with a topic, two participant names, and opposing stances.
2. The live debate screen uses one dynamic voice button.
3. Side A records a point, ends the point, and the system transcribes and scores it.
4. The active side automatically switches to Side B.
5. The same record/end flow repeats for each side.
6. The live crowd split updates throughout the debate as a provisional reaction score.
7. When the debate is ended, the backend finalizes the transcript, extracts claims, reviews evidence, scores both sides, and composes a verdict.
8. The summary screen presents the winner, final crowd split, strengths, weaknesses, deciding factors, and audit notes.

## Architecture

The project is split into two deployable services:

- `app/`: FastAPI backend and orchestration system.
- `frontend/`: Next.js frontend for setup, live debate capture, history, and verdict summary.

The backend remains the source of truth. The frontend sends debate actions to the backend and renders the returned state.

## Backend

The backend handles:

- Debate session creation and state transitions.
- Voice utterance ingestion.
- Gemini speech-to-text transcription.
- NVIDIA NIM reasoning for live crowd scoring and AI-assisted judging.
- Live score preservation and final score recall.
- Transcript storage.
- Claim extraction.
- Evidence review.
- Judge scorecards.
- Verdict composition.
- API responses for the frontend.

The orchestrator controls the debate lifecycle and prevents invalid transitions, such as submitting turns after a debate has ended.

## Frontend

The frontend is a Next.js app with:

- Landing page.
- Debate setup form.
- Live voice debate room.
- Dynamic one-button recording flow.
- Live crowd split visualization.
- Transcript sidebar.
- Winner and verdict summary screen.
- Debate history view.

The frontend communicates with the backend through `frontend/lib/api.ts` using the configured public API base URL.

## Debate State Model

The debate lifecycle is structured around explicit phases:

- `INIT`
- `TOPIC_LOCK`
- `STANCE_CAPTURE`
- `LIVE_CAPTURE`
- `TRANSCRIPT_FINALIZED`
- `CLAIM_EXTRACTION`
- `FACT_CHECK`
- `SCORING`
- `VERDICT`
- `AUDIT`

This keeps orchestration deterministic and makes it easier to reason about what the system is allowed to do at any point.

## AI Services

Gemini is used for speech-to-text transcription from browser-recorded audio.

NVIDIA NIM is used for reasoning-heavy tasks, especially live crowd scoring. The scoring prompt asks NIM to judge:

- topic relevance
- argument quality
- stance alignment
- whether the point should affect the score
- whether the point triggers contextual crowd backlash for discriminatory or ethically toxic framing

The latest point is weighted more heavily than older turns, while previous turns are used as context for stance consistency, repeated patterns, and debate momentum.

## Live Crowd Split

The live crowd split is a provisional audience-reaction style score. It is not the final judge verdict.

The score is normalized as a percentage split between both sides, bounded so it does not exceed the configured floor and ceiling. The backend preserves the final live split after the debate ends so the summary screen can display the same score that was visible during the live debate.

## Persistence

The project is designed to use PostgreSQL, with Neon as the current hosted database option.

Stored data includes:

- debate sessions
- turns and transcripts
- live score snapshots
- extracted claims
- evidence review outputs
- scorecards
- verdicts
- session events and audit metadata

The database allows debate state to survive restarts and lets the frontend retrieve history and completed summaries.

## Deployment Shape

The current hosting model uses:

- Render Web Service for the FastAPI backend.
- Render Web Service for the Next.js frontend.
- Neon Postgres for persistent storage.
- External Gemini and NVIDIA NIM APIs for AI services.

The backend exposes the API and the frontend is deployed as a separate web app. Cross-origin access is controlled through the backend CORS configuration.

## Key Environment Variables

Backend configuration includes:

- `DATABASE_URL`
- `DATABASE_ECHO`
- `CORS_ORIGINS`
- `GEMINI_API_KEY`
- `GEMINI_TRANSCRIBE_MODEL`
- `GEMINI_API_BASE`
- `NVIDIA_NIM_API_KEY`
- `NVIDIA_NIM_MODEL`
- `NVIDIA_NIM_API_BASE`
- `NIM_LIVE_SCORE_RETRIES`
- `NIM_TIMEOUT_SECONDS`

Frontend configuration includes:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_USE_MOCK`
