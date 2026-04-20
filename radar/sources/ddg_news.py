"""DuckDuckGo text search as a lightweight news/recency signal."""

from __future__ import annotations

import json
from typing import Callable, List

from radar.models import NewsHit

# duckduckgo_search returns JSON string of a list of dicts (title, href, body from ddgs).
DdgSearchFn = Callable[[str, int], str]


def ddg_results_to_news_hits(ddg_json: str) -> List[NewsHit]:
    try:
        rows = json.loads(ddg_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []
    hits: List[NewsHit] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        url = r.get("href") or r.get("url") or r.get("link") or ""
        hits.append(
            NewsHit(
                title=str(r.get("title") or ""),
                url=str(url),
                snippet=str(r.get("body") or ""),
            )
        )
    return hits


def fetch_news_hits_for_company(
    company_name: str,
    ddg_search: DdgSearchFn,
    *,
    num_results: int = 6,
    second_query: str | None = None,
) -> List[NewsHit]:
    """
    One or two bounded queries: "{name}" news [+ optional industry token].
    """
    if not company_name.strip():
        return []
    q1 = f'"{company_name.strip()}" news'
    raw = ddg_search(q1, num_results)
    hits = ddg_results_to_news_hits(raw)
    if second_query and len(hits) < 3:
        q2 = f'"{company_name.strip()}" {second_query}'[:240]
        raw2 = ddg_search(q2, max(3, num_results // 2))
        extra = ddg_results_to_news_hits(raw2)
        seen = {h.url for h in hits if h.url}
        for h in extra:
            if h.url and h.url not in seen:
                hits.append(h)
                seen.add(h.url)
    return hits[:8]
