"""Enrichment helpers without calling external APIs."""

import json

from radar.models import Thesis
from radar.sources.companyenrich import company_info_to_profile
from radar.sources.ddg_news import ddg_results_to_news_hits, fetch_news_hits_for_company


def test_ddg_results_to_news_hits():
    payload = json.dumps(
        [
            {"title": "A", "href": "https://a", "body": "snippet one"},
            {"title": "B", "url": "https://b", "body": "two"},
        ]
    )
    hits = ddg_results_to_news_hits(payload)
    assert len(hits) == 2
    assert hits[0].url == "https://a"


def test_company_info_to_profile_maps_fields():
    raw = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Acme Corp",
        "domain": "acme.com",
        "website": "https://acme.com",
        "industry": "Software",
        "industries": ["SaaS"],
        "description": "Does things.",
        "employees": "11-50",
        "financial": {"funding_stage": "series_a"},
    }
    p = company_info_to_profile(raw)
    assert p.name == "Acme Corp"
    assert p.domain == "acme.com"
    assert p.companyenrich_id == "550e8400-e29b-41d4-a716-446655440000"
    assert "Software" in p.industry_tags
    assert p.employee_range == "11-50"
    assert p.funding_stage == "series_a"
    assert any(s.provider == "companyenrich" for s in p.sources)


def test_fetch_news_hits_uses_ddg_fn():
    calls = []

    def fake_ddg(q: str, n: int) -> str:
        calls.append((q, n))
        return json.dumps([{"title": "t", "href": "u", "body": "b"}])

    hits = fetch_news_hits_for_company("TestCo", fake_ddg)
    assert len(hits) == 1
    assert "TestCo" in calls[0][0]


def test_thesis_max_companies_bounds():
    t = Thesis(statement="x", max_companies=5)
    assert t.max_companies == 5
