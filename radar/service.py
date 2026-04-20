"""Orchestrate enrichment, scoring, and Supabase persistence for radar runs."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import supabase_store
from radar.enrichment import build_profiles_for_thesis
from radar.models import RadarCompanyResult, ScoringConfig, Thesis
from radar.scoring import default_scoring_config, merge_scoring_config, score_company


def run_radar_analysis(thesis: Thesis) -> Tuple[ScoringConfig, List[RadarCompanyResult], Optional[str]]:
    """
    Returns (resolved scoring config, ranked results, run_id or None).
    """
    cfg = merge_scoring_config(thesis, default_scoring_config())
    api_key = os.environ.get("COMPANYENRICH_API_KEY")
    profiles = build_profiles_for_thesis(thesis, api_key)

    scored: List[Tuple[float, Any, Any]] = []
    for p in profiles:
        bd = score_company(thesis, p, cfg)
        scored.append((bd.total, p, bd))

    scored.sort(key=lambda x: -x[0])
    companies: List[RadarCompanyResult] = []
    for rank, (_, p, bd) in enumerate(scored, start=1):
        companies.append(RadarCompanyResult(rank=rank, profile=p, score_breakdown=bd))

    input_snapshot: Dict[str, Any] = thesis.model_dump()
    scoring_snapshot: Dict[str, Any] = cfg.model_dump()
    results_json = [c.model_dump(mode="json") for c in companies]
    run_id = supabase_store.save_radar_run(input_snapshot, scoring_snapshot, results_json)
    return cfg, companies, run_id


def radar_response_payload(
    thesis: Thesis,
    cfg: ScoringConfig,
    companies: List[RadarCompanyResult],
    run_id: Optional[str],
) -> Dict[str, Any]:
    return {
        "runId": run_id,
        "persisted": run_id is not None,
        "thesis": thesis.model_dump(),
        "scoringConfig": cfg.model_dump(),
        "labelLegend": {
            "strong": f"total score ≥ {cfg.strong_min}",
            "mixed": f"{cfg.mixed_min} ≤ total < {cfg.strong_min}",
            "weak": f"total < {cfg.mixed_min}",
        },
        "companies": [c.model_dump(mode="json") for c in companies],
    }
