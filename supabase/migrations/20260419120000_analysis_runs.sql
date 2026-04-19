-- Applied via Supabase MCP / dashboard; kept here for version control.
-- Table: analysis runs. Bucket: public chart PNGs.

CREATE TABLE IF NOT EXISTS public.analysis_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  company_name text,
  industry text,
  input jsonb NOT NULL DEFAULT '{}',
  summary jsonb,
  competitors jsonb DEFAULT '[]'::jsonb,
  features jsonb DEFAULT '[]'::jsonb,
  pricing jsonb DEFAULT '[]'::jsonb,
  log text,
  charts jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS analysis_runs_created_at_idx ON public.analysis_runs (created_at DESC);

ALTER TABLE public.analysis_runs ENABLE ROW LEVEL SECURITY;

INSERT INTO storage.buckets (id, name, public)
VALUES ('analysis-charts', 'analysis-charts', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "analysis_charts_public_read" ON storage.objects;
CREATE POLICY "analysis_charts_public_read"
ON storage.objects FOR SELECT
USING (bucket_id = 'analysis-charts');
