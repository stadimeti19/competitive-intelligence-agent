# Competitive Intelligence Assistant

This project now supports two parallel workflows:

- **Classic CI Report flow** (`/analyze`): agent-driven competitive intelligence reports.
- **Thesis Radar flow** (`/radar/analyze`): deterministic, structured opportunity ranking against a thesis.

The classic flow is preserved as-is, and radar is an additive extension.

## Core Features

- **Classic CI reports:** competitor discovery, feature/pricing matrix, charts, recommendations.
- **Thesis-driven radar:** submit a thesis, discover companies, enrich with structured data, score with explainable components, and label fit (`strong` / `mixed` / `weak`).
- **Saved runs:** optional Supabase persistence for both CI and radar runs.

## Architecture at a Glance

- **Backend:** FastAPI (`main.py`)
  - Classic: `POST /analyze`, `GET /runs`, `GET /runs/{id}`, chart endpoints
  - Radar: `POST /radar/analyze`, `GET /radar/runs`, `GET /radar/runs/{id}`
- **Frontend:** React + Vite (`frontend/`)
  - Dashboard for classic CI
  - Radar page for thesis ranking (`/radar`)
- **Radar modules:** `radar/`
  - `models.py` for typed contracts
  - `enrichment.py` + `sources/` for CompanyEnrich/DDG/Massive adapters
  - `scoring.py` for deterministic score breakdown

## Setup

### 1) Backend (FastAPI + Python)

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional for classic CI dynamic scraping:

```bash
pip install playwright
playwright install
```

Start API server:

```bash
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000` by default.

### 2) Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` by default.

## Environment Variables

Set these in `.env` (loaded by backend via `python-dotenv`):

### Required for radar analysis

- `COMPANYENRICH_API_KEY` - required for company discovery/enrichment in radar.

### Optional for radar enrichment

- `MASSIVE_API_KEY` - optional; enables public-company ticker overview enrichment.
- `MASSIVE_API_BASE` - optional override (defaults to `https://api.massive.com`).

### Optional for persistence/history

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

If Supabase is not configured, runs still execute; response includes `persisted: false`.

### Classic CI / LLM flow

- `OPENAI_API_KEY` and/or `OAI_CONFIG_LIST` as needed for AutoGen-based classic analysis.

## Usage

### Classic CI Report

1. Open `/` in the frontend.
2. Fill company/industry fields and run analysis.
3. Review summary, competitors, feature/pricing tables, and charts.

### Thesis Radar

1. Open `/radar` in the frontend.
2. Enter a thesis, optional include/exclude keywords, and max companies.
3. Run radar and inspect ranked companies with score breakdown components.

## Radar Scoring Notes

Radar scoring is intentionally deterministic and explainable:

- `keyword_overlap`
- `news_signal`
- `exclusion_clear`
- `data_completeness`

`keyword_overlap` recall uses company profile text plus DDG news text (and optional scoring-only extra corpus from Massive overview).  
`exclusion_clear` intentionally uses only core company corpus (not appended news/extra text).

## API Summary

### Classic CI

- `POST /analyze`
- `GET /runs`
- `GET /runs/{run_id}`

### Radar

- `POST /radar/analyze`
- `GET /radar/runs`
- `GET /radar/runs/{run_id}`

## Testing

Run radar tests:

```bash
python -m pytest radar/tests -v
```

Run frontend build validation:

```bash
cd frontend && npm run build
```