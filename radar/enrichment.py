"""Two-stage enrichment: CompanyEnrich search, then DDG news per candidate."""

from __future__ import annotations

from typing import Callable, List, Optional

from radar.models import CompanyProfile, SourceRef, Thesis
from radar.sources.companyenrich import company_info_to_profile, search_companies
from radar.sources.ddg_news import DdgSearchFn, fetch_news_hits_for_company
from radar.sources.massive import maybe_enrich_massive


def default_ddg() -> DdgSearchFn:
    from tools.ci_tools import duckduckgo_search

    return duckduckgo_search


def build_profiles_for_thesis(
    thesis: Thesis,
    api_key: Optional[str],
    *,
    ddg_search: Optional[DdgSearchFn] = None,
    industry_hint: Optional[str] = None,
) -> List[CompanyProfile]:
    """
    Primary discovery via CompanyEnrich semantic search, then DDG news hits per row.
    `api_key` from COMPANYENRICH_API_KEY; if missing, raises ValueError.
    """
    if not api_key or not api_key.strip():
        raise ValueError(
            "COMPANYENRICH_API_KEY is not set. Radar enrichment requires a CompanyEnrich API token."
        )
    ddg = ddg_search or default_ddg()
    query = thesis.statement.strip()
    if not query:
        raise ValueError("Thesis statement is empty.")

    raw_items = search_companies(
        api_key.strip(),
        query,
        page_size=thesis.max_companies,
    )
    profiles: List[CompanyProfile] = []
    hint = industry_hint
    if not hint and thesis.must_include_keywords:
        hint = thesis.must_include_keywords[0]

    for raw in raw_items[: thesis.max_companies]:
        profile = company_info_to_profile(raw)
        second = hint or (profile.industry_tags[0] if profile.industry_tags else None)
        news = fetch_news_hits_for_company(profile.name, ddg, second_query=second)
        profile.news_hits = news
        profile.sources = list(profile.sources) + [
            SourceRef(provider="ddg", detail=f"{len(news)} news snippets"),
        ]
        maybe_enrich_massive(profile)
        profiles.append(profile)

    return profiles
