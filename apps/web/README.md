# FormCheck web application

Owner: Person 1.

React + TypeScript + Vite client for capture guidance, upload, quiet processing wait, coaching results, and terminal states (inconclusive, failed, expired, deleted). Talks only to the public API through an `AnalysisApi` interface.

## Setup

```bash
cd apps/web
npm install
npm run dev
```

Open the printed local URL (default `http://localhost:5173`).

## Mock vs real API

By default the app uses an in-browser **mock API** so frontend work is unblocked.

- Happy-path uploads complete after a short quiet wait.
- Name the file with `inconclusive`, `failed`, or `expired` to exercise those terminal states (for example `trial-inconclusive.mp4`).

To point at Person 2’s API:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

No page or business-logic changes are required when switching clients.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Local development server |
| `npm run build` | Typecheck and production build |
| `npm run preview` | Preview the production build |
| `npm test` | Vitest unit tests |
| `npm run test:e2e` | Playwright happy-path browser test |

First Playwright run may need browsers:

```bash
npx playwright install chromium
```

## Routes

- `/` — capture guidance and recording tips
- `/upload` — drag-and-drop upload form
- `/analyses/:id` — quiet wait, then completed / inconclusive / failed / expired / deleted UI

Capability tokens are stored in `sessionStorage` for the analysis lifetime so a refresh during processing can restore the session. Tokens are never logged.
