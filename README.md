# HausMate Match

HausMate Match is now a Vite + React + TypeScript frontend styled with Tailwind CSS and shadcn-style UI primitives.

## Stack

- Vite
- React
- TypeScript
- Tailwind CSS v4
- Supabase JavaScript client

## Run locally

```bash
npm install
npm run dev
```

The dev server is configured for port `8501` to stay close to the previous Streamlit workflow.

## Environment

Create a `.env.local` file from `.env.example`.

```bash
cp .env.example .env.local
```

Required variables for live submissions:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SUPABASE_TABLE`

If those variables are not set, submissions are stored in `localStorage` so the UI still works during local redesign and review.

## Secret guardrails

Install the repo git hooks once for your clone:

```bash
npm run setup:githooks
```

The hooks block commits and pushes if:

- `.env.example` contains real Supabase values instead of blanks or placeholders
- tracked files contain common secret values such as private keys, service role tokens, or API secrets

You can also run the checks manually:

```bash
npm run check:secrets
```

## Deploy

Build with:

```bash
npm run build
```

Deploy the generated `dist/` output to the same host currently serving the public URL if you want the URL to remain unchanged.
