# Netvrio design direction

Design Read: **a real-time operations console for payment-risk analysts, in a calm instrument-panel style (graphite, warm ink, one violet accent), dials ENERGY 1 / RHYTHM 2 / MOTION 2.**

This file is the direction anti-slop (R-37) asks for, plus the one-line reason for every major choice (R-31).
Rules referenced: [miqdadbadjuber/anti-slop](https://github.com/miqdadbadjuber/anti-slop) R-01 to R-40.

## Dials

| Dial | Value | Reason |
|---|---|---|
| ENERGY | 1 (calm) | Analysts watch this for hours; the data should be the loudest thing on screen. |
| RHYTHM | 2 | Queue and stream sit side by side; charts below vary in size by importance, not a uniform card grid. |
| MOTION | 2 | Only state transitions: new-row highlight (arrival is information), button press depth. No loops, pulses or floating effects. `prefers-reduced-motion` turns all of it off. |

## Hierarchy (C-3, R-20)

The screen is built around the operator's one decision: **which payments need a human now?**

1. Review queue ("Needs a decision") is the focal point, with working Approve and Decline actions.
2. Event stream next to it, for investigation (click or Enter opens the pipeline trace).
3. A single status strip instead of a wall of stat cards. Every figure is computed from real events.
4. Charts last, each titled with the question it answers.

The default "sidebar + four stat cards + chart + table" shell was rejected for this reason.

## Tokens

| Token | Value | Reason |
|---|---|---|
| canvas / surface / raised | `#0e0f11` / `#15171a` / `#1d2024` | Warm graphite, not blue-black, so it doesn't read as the default "AI dark mode". |
| ink / muted / subtle | `#ecebe7` / `#b4b2ac` / `#908e88` | Warm off-white text. Subtle is ≥ 5:1 on surface (R-25). |
| allow / review / block | `#6cc58f` / `#e2a945` / `#f0705f` | Functional status colours only; never decoration. |
| zombie (accent) | `#b49cff` | The single deliberate accent. Zombie Card Saver and card exposure are the product's signature finding, so this is the one colour that pulls the eye. |
| Radii | 3 / 5 / 6 px | Small and consistent (R-11); nothing is pill-shaped. |
| Shadows | Overlays only (drawer, palette) | Elevation marker, not decoration (R-12). Panels are flat with a 1px line. |

Palette = graphite + ink (2 core) + violet (1 accent). Status colours are semantic, not brand (R-29).
Theme: **dark only**. Reason: operations rooms run dim and screens stay on all shift; a light mode would be untested, so no toggle ships (R-21, R-34).

## Type

- **IBM Plex Sans** for the interface: engineered for technical UIs, distinct letterforms at small sizes.
- **IBM Plex Mono** only for data: amounts, IDs, hashes, timestamps, so columns align (R-06: mono is for data, not style).
- Self-hosted via `@fontsource` so the strict `Content-Security-Policy` (no third-party origins) stays intact.
- Sentence case labels. No wide-tracked uppercase eyebrows.

## Components

| Component | Choice | Reason |
|---|---|---|
| PlateButton | Pushable button: chamfered face over a darker edge that drops on press (pattern after Josh Comeau's 3D button write-up). | Used only for actions that change state (approve, decline, start traffic, verify), so they feel physically different from navigation. |
| Tags | Small square-cornered tags | Only for real state: decision, risk level, source health (R-09). |
| Left stripe | 2px violet or red rule | Marks a real state only: zombie item, the stage that stopped a request (R-01/R-31). |
| Command palette | Ctrl/⌘K | Every command performs a real action and reports its result (R-26). |
| Shell | Collapsible sidebar, sticky top bar with breadcrumb and command button | Layout pattern from navbar.gallery sidebar/search examples; no branding taken. |
| Mark | Flat monoline shield | No gradient, glow or sparkle (R-01, R-04). |

## Copy

No em dashes, no buzzwords, no invented numbers (R-02, R-16, R-17). Empty, loading and error states name the cause and the next step (R-27).
Status claims are measured in the browser (API responding, stream connected) or labelled honestly ("NOT CONNECTED", "NOT VERIFIED / CONTRACT TESTED").

## References used

- anti-slop rule set (R-01 to R-40) for the audit and this gate.
- navbar.gallery (sidebar + search patterns), cta.gallery (two-action pattern used for Approve / Decline) via the vishnuai.in resource list. Layout only, no branding.
- Josh Comeau, "Building a Magical 3D Button" for the PlateButton mechanics.
- Libraries: Recharts 3 (MIT), lucide-react (ISC), @fontsource IBM Plex (OFL).

## Delivery gate (self-audit, 2026-11-09)

| Block | Result | Evidence |
|---|---|---|
| Hard gate | PASS | No em dashes in UI copy (grep). No horizontal overflow at 375px (`scrollWidth == innerWidth`). No fabricated data: every number derives from live events or API responses. All controls do real work (tests cover approve/decline, palette commands). Keyboard: rows, drawer (Esc), palette (arrows, Enter, Esc). |
| Purpose gate | PASS | Accent, stripes, shadows, mono, motion each have a reason above. |
| Liveliness | PASS | Dials declared; focal point is the review queue; one accent; identity motif = plate buttons + shield mark. |
| Quality locks | PASS with one note | Tap targets ≥ 36px on desktop controls, 44px for mobile navigation. Filter tabs are 36px, below the 44px mobile ideal; acceptable for a desktop-first console, listed here rather than hidden. |
