"""CompanyEnrich API: company search -> CompanyProfile (without DDG news)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from radar.models import CompanyProfile, SourceRef

CE_BASE = os.environ.get("COMPANYENRICH_API_BASE", "https://api.companyenrich.com")


def search_companies(
    api_key: str,
    semantic_query: str,
    *,
    page_size: int = 15,
    page: int = 1,
    timeout: float = 45.0,
) -> List[Dict[str, Any]]:
    """
    POST /companies/search with semanticQuery.
    Returns raw `items` list from the API response.
    """
    url = f"{CE_BASE.rstrip('/')}/companies/search"
    body: Dict[str, Any] = {
        "page": page,
        "pageSize": min(100, max(1, page_size)),
        "semanticQuery": (semantic_query or "")[:500],
    }
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    return list(data.get("items") or [])


def _employee_str(raw: Optional[Dict[str, Any]]) -> Optional[str]:
    if not raw:
        return None
    emp = raw.get("employees")
    if isinstance(emp, str):
        return emp
    return None


def company_info_to_profile(raw: Dict[str, Any]) -> CompanyProfile:
    """Map one CompanyInfo JSON object to CompanyProfile."""
    fin = raw.get("financial") if isinstance(raw.get("financial"), dict) else {}
    funding_stage = fin.get("funding_stage") if isinstance(fin, dict) else None
    tags: List[str] = []
    if raw.get("industry"):
        tags.append(str(raw["industry"]))
    inds = raw.get("industries")
    if isinstance(inds, list):
        tags.extend(str(x) for x in inds if x)
    cats = raw.get("categories")
    if isinstance(cats, list):
        for c in cats:
            if isinstance(c, dict) and c.get("name"):
                tags.append(str(c["name"]))
            elif isinstance(c, str):
                tags.append(c)
    # de-dupe preserving order
    seen = set()
    uniq = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            uniq.append(t)
    tags = uniq

    name = (raw.get("name") or "").strip() or "Unknown"
    domain = raw.get("domain")
    if domain:
        domain = str(domain).strip() or None
    cid = raw.get("id")
    companyenrich_id = str(cid) if cid else None

    website = raw.get("website")
    canonical = str(website).strip() if website else None
    desc = raw.get("description") or raw.get("seo_description")
    description = str(desc).strip() if desc else None

    employees = raw.get("employees")
    employee_range = str(employees) if employees else None

    return CompanyProfile(
        name=name,
        domain=domain,
        companyenrich_id=companyenrich_id,
        canonical_url=canonical,
        description=description,
        industry_tags=tags,
        employee_range=employee_range,
        funding_stage=str(funding_stage) if funding_stage else None,
        news_hits=[],
        sources=[
            SourceRef(provider="companyenrich", detail="companies/search"),
        ],
    )
