"""Persist analysis runs to Supabase (Postgres + Storage). Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

BUCKET = "analysis-charts"


def _client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception as e:
        print(f"[supabase_store] Supabase client unavailable: {e}")
        return None


def is_configured() -> bool:
    return _client() is not None


def _upload_charts(client, charts: Dict[str, Any], run_id: str) -> Dict[str, str]:
    """Upload local PNG paths to Storage; return chart_key -> public URL."""
    out: Dict[str, str] = {}
    if not charts:
        return out
    bucket = client.storage.from_(BUCKET)
    for key, path in charts.items():
        if not path:
            continue
        if isinstance(path, str) and path.startswith("http"):
            out[key] = path
            continue
        if not isinstance(path, str) or not os.path.isfile(path):
            continue
        dest = f"runs/{run_id}/{key}.png"
        try:
            with open(path, "rb") as f:
                bucket.upload(
                    dest,
                    f,
                    {"content-type": "image/png", "x-upsert": "true"},
                )
            pub = bucket.get_public_url(dest)
            out[key] = pub if isinstance(pub, str) else str(pub)
        except Exception as e:
            print(f"[supabase_store] Chart upload failed ({key}): {e}")
    return out


def save_run(
    input_data: Dict[str, Any],
    summary: Dict[str, Any],
    competitors: List[Any],
    features: List[Any],
    pricing: List[Any],
    log: str,
) -> tuple[Optional[str], Dict[str, Any]]:
    """Insert one run; uploads chart PNGs when possible. Returns (run_id, summary_for_response)."""
    base_summary = dict(summary) if summary else {}
    client = _client()
    if not client:
        return None, base_summary
    run_id = str(uuid.uuid4())
    summary_copy = dict(base_summary)
    raw_charts = dict(summary_copy.get("charts") or {})
    uploaded = _upload_charts(client, raw_charts, run_id)
    summary_copy["charts"] = uploaded

    row = {
        "id": run_id,
        "company_name": input_data.get("companyName") or input_data.get("company_name"),
        "industry": input_data.get("industry"),
        "input": input_data,
        "summary": summary_copy,
        "competitors": competitors,
        "features": features,
        "pricing": pricing,
        "log": log,
        "charts": uploaded,
    }
    try:
        client.table("analysis_runs").insert(row).execute()
        return run_id, summary_copy
    except Exception as e:
        print(f"[supabase_store] Insert failed: {e}")
        return None, base_summary


def list_runs(limit: int = 50) -> List[Dict[str, Any]]:
    client = _client()
    if not client:
        return []
    try:
        r = (
            client.table("analysis_runs")
            .select("id, created_at, company_name, industry")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return r.data or []
    except Exception as e:
        print(f"[supabase_store] list_runs failed: {e}")
        return []


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    client = _client()
    if not client:
        return None
    try:
        r = client.table("analysis_runs").select("*").eq("id", run_id).single().execute()
        return r.data
    except Exception as e:
        print(f"[supabase_store] get_run failed: {e}")
        return None


def save_radar_run(
    input_data: Dict[str, Any],
    scoring_config_snapshot: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> Optional[str]:
    """Insert one radar run. Returns run_id or None if Supabase unavailable or insert fails."""
    client = _client()
    if not client:
        return None
    run_id = str(uuid.uuid4())
    row = {
        "id": run_id,
        "input": input_data,
        "scoring_config_snapshot": scoring_config_snapshot,
        "results": results,
    }
    try:
        client.table("radar_runs").insert(row).execute()
        return run_id
    except Exception as e:
        print(f"[supabase_store] save_radar_run failed: {e}")
        return None


def list_radar_runs(limit: int = 50) -> List[Dict[str, Any]]:
    client = _client()
    if not client:
        return []
    try:
        r = (
            client.table("radar_runs")
            .select("id, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return r.data or []
    except Exception as e:
        print(f"[supabase_store] list_radar_runs failed: {e}")
        return []


def get_radar_run(run_id: str) -> Optional[Dict[str, Any]]:
    client = _client()
    if not client:
        return None
    try:
        r = client.table("radar_runs").select("*").eq("id", run_id).single().execute()
        return r.data
    except Exception as e:
        print(f"[supabase_store] get_radar_run failed: {e}")
        return None
