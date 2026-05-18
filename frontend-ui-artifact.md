# DebateAI Frontend UI Artifact

Date: 2026-05-17

This artifact captures the current frontend baseline before UI tuning. The frontend lives in `frontend/` and is a Next.js 14 app using React, Tailwind, and Framer Motion.

## Current App Shape

### Routes

- `/`: landing page with animated canvas glow, hero copy, `Create a Debate`, and `View History`.
- `/debate/setup`: debate creation form for topic, side names, and side A stance. Side B stance is auto-derived.
- `/debate/live`: voice-first live debate room with active speaker, recorder CTA, live crowd split, transcript sidebar, and end-debate action.
- `/debate/summary/[id]`: final verdict/summary screen.
- `/history`: list of previous debates with compact debate cards.

### Visual Language

- Theme: dark, high-contrast, neon debate arena.
- Core colors:
  - Side A: orange `#e87848`
  - Side B: blue `#48a8e0`
  - Accent/CTA: purple `#7c5cfc`
  - Background/card: deep navy/black tones from Tailwind config.
- Typography:
  - `Space Grotesk` for display/headline moments.
  - `Inter` for supporting UI text.
- Motion:
  - Framer Motion reveal animations.
  - Animated hero canvas glow.
  - Recording waveform animation.
  - Winner overlay animation.
  - Crowd split bar width transition.

## Key Components

### `CrowdSplitBar`

Shows side names, percentages, and an animated split bar.

Current strengths:
- Clear A/B color mapping.
- Works in multiple sizes.
- Good visual continuity between live and history views.

Tuning opportunities:
- Add stronger visual treatment for dramatic score swings.
- Consider showing trend arrows or last delta.
- Improve accessibility labels for screen readers.

### `DynamicActionButton`

Single primary CTA for voice flow.

States:
- Ready: `Start the point — {sideName}`
- Recording: `End Point`
- Processing/switching: `Processing...`

Current strengths:
- Matches the desired one-button debate flow.
- Color changes by active side.

Tuning opportunities:
- Make recording state more urgent and unmistakable.
- Add small helper text for what happens after pressing it.
- Ensure disabled state stays legible.

### `VoiceIndicator`

Animated waveform bars for recording state.

Current strengths:
- Simple, readable recording affordance.
- Uses active side color.

Tuning opportunities:
- Add a stronger idle state so the recording area does not feel empty.
- Make the waveform scale better on mobile.

### `DebateCard`

History card showing side names, topic, winner, and split preview.

Current strengths:
- Compact and scannable.
- Winner emphasis is visible.

Tuning opportunities:
- Improve mobile layout; current three-column grid may become tight.
- Show final verdict confidence or status more clearly.

### `AnimatedWinnerOverlay`

Full-screen post-debate winner reveal.

Current strengths:
- Strong theatrical moment.
- Uses winner color and particle motion.

Tuning opportunities:
- Avoid delaying access to final details too long.
- Add reduced-motion fallback later.

## Current UX Flow

1. User lands on `/`.
2. User clicks `Create a Debate`.
3. User fills topic and side names.
4. User chooses side A stance; side B is auto-set to the opposite.
5. User enters live debate room.
6. User records one point at a time.
7. Button alternates between start/end states and sides switch automatically.
8. Live crowd split updates after each submitted point.
9. User ends debate.
10. App moves to summary screen with final verdict and final crowd split.

## API Integration

Frontend API client:

`frontend/lib/api.ts`

Environment variables:

- `NEXT_PUBLIC_API_URL`: backend base URL.
- `NEXT_PUBLIC_USE_MOCK`: toggles mock API mode.

Render frontend should use:

```text
NEXT_PUBLIC_API_URL=https://YOUR-BACKEND.onrender.com
NEXT_PUBLIC_USE_MOCK=false
```

Backend must allow the frontend origin through:

```text
CORS_ORIGINS=https://YOUR-FRONTEND.onrender.com,http://localhost:3000,http://127.0.0.1:3000
```

## UI Issues Noticed

- Several text strings appear mojibaked in source, for example `â€”`, `â€¦`, `Â·`, and arrow symbols rendered as broken characters. These should be normalized to clean ASCII or proper UTF-8 characters.
- Live page uses a fixed two-column layout with `gridTemplateColumns: '1fr 300px'`, which may need mobile responsiveness.
- Landing page is visually strong, but the purple CTA dominates the side A/side B identity. If desired, we can shift the theme toward a more debate-arena feel and reduce purple.
- The setup form is clean but somewhat narrow and form-like; it could be more ceremonial, like setting teams before a match.
- Summary screen should be checked specifically for final crowd split recall and winner reveal timing.

## Suggested UI Tuning Priorities

1. Fix mojibake and text polish across all pages.
2. Improve mobile responsiveness for live debate and history cards.
3. Make the live recording panel feel more like a debate stage.
4. Strengthen crowd split feedback with deltas, trend motion, and score-change explanation.
5. Refine summary page hierarchy: winner, final split, decisive reasons, transcript highlights.
6. Add loading/error states that feel intentional instead of plain text blocks.

## Current Deployment Model

- Backend: Render Python/FastAPI Web Service.
- Frontend: Render Node/Next.js Web Service from `frontend/`.
- Database: Neon Postgres via `DATABASE_URL`.

