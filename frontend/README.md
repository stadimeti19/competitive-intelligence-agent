# Frontend (React + Vite)

This frontend powers both:

- **Classic CI dashboard** (`/`)
- **Thesis Radar** (`/radar`)

## Local Development

```sh
cd frontend
npm install
npm run dev
```

By default, the app runs on `http://localhost:5173`.

## Backend API Base URL

Set `VITE_API_BASE` to point to your FastAPI backend if needed.

If unset, the app defaults to:

```txt
http://localhost:8000
```

## Main Frontend Routes

- `/` - Competitive Intelligence dashboard (classic report flow)
- `/radar` - Thesis-driven opportunity radar

## Radar UI Behavior

The radar page submits thesis input to:

- `POST /radar/analyze`

and renders:

- ranked company list
- `strong` / `mixed` / `weak` label
- expandable score breakdown (`keyword_overlap`, `news_signal`, `exclusion_clear`, `data_completeness`)

## Build Check

```sh
npm run build
```

## Stack

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS
