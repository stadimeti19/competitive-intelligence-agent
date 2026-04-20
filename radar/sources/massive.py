"""
Optional Massive (stocks) enrichment: domain-aligned ticker resolve + ticker overview only.
Uses GET /v3/reference/tickers (search) and GET /v3/reference/tickers/{ticker}.
No Massive news API (DDG already covers news).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import requests

from radar.models import CompanyProfile, SourceRef

DEFAULT_BASE = "https://api.massive.com"
SEARCH_LIMIT = 10
TIMEOUT = 25.0


def _api_base() -> str:
    return os.environ.get("MASSIVE_API_BASE", DEFAULT_BASE).rstrip("/")


def _api_key() -> Optional[str]:
    k = os.environ.get("MASSIVE_API_KEY")
    return k.strip() if k and k.strip() else None


def _normalize_host(url_or_host: Optional[str]) -> Optional[str]:
    if not url_or_host or not str(url_or_host).strip():
        return None
    s = str(url_or_host).strip()
    if "://" not in s:
        s = "https://" + s
    try:
        host = (urlparse(s).hostname or "").lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _profile_domain_host(domain: Optional[str]) -> Optional[str]:
    if not domain or not str(domain).strip():
        return None
    d = str(domain).strip().lower().split("/")[0].split(":")[0]
    if d.startswith("www."):
        d = d[4:]
    return d or None


def _pick_ticker_matching_domain(results: List[Dict[str, Any]], domain_host: Optional[str]) -> Optional[str]:
    if not domain_host:
        return None
    for row in results:
        if not isinstance(row, dict):
            continue
        home = row.get("homepage_url")
        h = _normalize_host(home)
        if h and h == domain_host:
            sym = row.get("ticker")
            if sym and isinstance(sym, str):
                return sym.strip().upper()
    return None


def _search_tickers(session: requests.Session, api_key: str, query: str) -> List[Dict[str, Any]]:
    url = f"{_api_base()}/v3/reference/tickers"
    params: Dict[str, Any] = {
        "apiKey": api_key,
        "search": query[:240],
        "active": "true",
        "market": "stocks",
        "limit": SEARCH_LIMIT,
    }
    r = session.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        return []
    res = data.get("results")
    return list(res) if isinstance(res, list) else []


def _ticker_overview(session: requests.Session, api_key: str, ticker: str) -> Optional[Dict[str, Any]]:
    url = f"{_api_base()}/v3/reference/tickers/{quote(ticker, safe='')}"
    r = session.get(url, params={"apiKey": api_key}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        return None
    out = data.get("results")
    return out if isinstance(out, dict) else None


def maybe_enrich_massive(profile: CompanyProfile) -> None:
    """
    If MASSIVE_API_KEY is set, try to resolve a US ticker by matching search homepage to profile.domain,
    then merge ticker overview into profile (in place). No-op on any failure or no match.
    """
    api_key = _api_key()
    if not api_key:
        return
    domain_host = _profile_domain_host(profile.domain)
    if not domain_host:
        return
    name_q = (profile.name or "").strip()
    if not name_q:
        return

    try:
        with requests.Session() as session:
            rows = _search_tickers(session, api_key, name_q)
            ticker = _pick_ticker_matching_domain(rows, domain_host)
            if not ticker:
                return
            overview = _ticker_overview(session, api_key, ticker)
            if not overview:
                return

            profile.ticker = ticker
            sic = overview.get("sic_description")
            if isinstance(sic, str) and sic.strip():
                sic_clean = sic.strip()
                tags_lower = {t.lower() for t in profile.industry_tags}
                if sic_clean.lower() not in tags_lower:
                    profile.industry_tags = list(profile.industry_tags) + [sic_clean]

            desc = overview.get("description")
            parts: List[str] = []
            if isinstance(sic, str) and sic.strip():
                parts.append(sic.strip())
            if isinstance(desc, str) and desc.strip():
                parts.append(desc.strip())
            if parts:
                profile.keyword_corpus_extra = "\n".join(parts)

            profile.sources = list(profile.sources) + [
                SourceRef(provider="massive", detail=f"{ticker} ticker-overview"),
            ]
    except Exception as e:
        print(f"[massive] skip enrichment for {profile.name!r}: {e}")
