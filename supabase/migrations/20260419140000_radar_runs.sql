-- Radar runs: thesis snapshot + scoring config + ranked company results (JSONB).

CREATE TABLE IF NOT EXISTS public.radar_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  input jsonb NOT NULL DEFAULT '{}',
  scoring_config_snapshot jsonb NOT NULL DEFAULT '{}',
  results jsonb NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS radar_runs_created_at_idx ON public.radar_runs (created_at DESC);

ALTER TABLE public.radar_runs ENABLE ROW LEVEL SECURITY;
