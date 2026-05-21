"""Evidence tracing and confidence tests."""

import sys
from types import ModuleType

import pytest

from radar.evidence import _run_agent_sync, build_evidence, compute_confidence, extract_claims
from radar.models import CompanyProfile, ExtractedClaim, NewsHit, Thesis
from radar.scoring import score_company


def test_build_evidence_has_stable_ids_and_matched_terms():
    thesis = Thesis(statement="AI compliance developer tools")
    profile = CompanyProfile(
        name="Alpha AI",
        domain="alpha.ai",
        companyenrich_id="111",
        description="AI compliance automation for developer teams.",
        industry_tags=["developer tools"],
        news_hits=[NewsHit(title="Alpha launches", url="https://a", snippet="Compliance tool launch")],
        ticker="ALPH",
        keyword_corpus_extra="Developer productivity software overview.",
    )

    evidence = build_evidence(thesis, profile)

    assert [e.id for e in evidence] == [
        "alpha-ai-companyenrich-profile",
        "alpha-ai-ddg-news-1",
        "alpha-ai-massive-overview",
    ]
    assert "compliance" in evidence[0].matched_terms
    assert evidence[1].provider == "ddg"
    assert evidence[2].provider == "massive"


def test_confidence_tracks_evidence_and_contradictions():
    thesis = Thesis(
        statement="developer compliance automation",
        must_exclude_keywords=["crypto"],
    )
    strong = CompanyProfile(
        name="StrongCo",
        domain="strong.co",
        companyenrich_id="111",
        description="Developer compliance automation platform.",
        industry_tags=["developer tools", "compliance"],
        news_hits=[NewsHit(title="StrongCo launch", url="u", snippet="automation for compliance teams")],
    )
    weak = CompanyProfile(
        name="WeakCo",
        description="Crypto exchange for traders.",
        industry_tags=[],
        news_hits=[],
    )

    strong_bd = score_company(thesis, strong)
    weak_bd = score_company(thesis, weak)
    strong_conf = compute_confidence(thesis, strong, strong_bd, build_evidence(thesis, strong))
    weak_conf = compute_confidence(thesis, weak, weak_bd, build_evidence(thesis, weak))

    assert strong_conf.evidence_strength > weak_conf.evidence_strength
    assert strong_conf.data_completeness > weak_conf.data_completeness
    assert weak_conf.contradiction_score == 1.0
    assert strong_conf.confidence_level in {"high", "medium"}
    assert weak_conf.confidence_level == "low"


def test_claim_extraction_failure_returns_no_claims(monkeypatch):
    module = ModuleType("pydantic_ai")

    class BrokenAgent:
        def __init__(self, *args, **kwargs):
            pass

        def run_sync(self, prompt):
            raise RuntimeError("model unavailable")

    module.Agent = BrokenAgent
    monkeypatch.setitem(sys.modules, "pydantic_ai", module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    thesis = Thesis(statement="compliance developer tools")
    profile = CompanyProfile(
        name="FallbackCo",
        description="Compliance tools for developer workflows.",
        industry_tags=["developer tools"],
    )
    evidence = build_evidence(thesis, profile)
    claims = extract_claims(thesis, profile, evidence)

    assert claims == []


def test_claim_extraction_sanitizes_pydanticai_output(monkeypatch):
    module = ModuleType("pydantic_ai")

    class FakeResult:
        output = type(
            "Output",
            (),
            {
                "claims": [
                    ExtractedClaim(
                        claim="FallbackCo targets compliance developers.",
                        category="customer_signal",
                        evidence_ids=["fallbackco-companyenrich-profile", "missing-id"],
                        confidence=0.8,
                    )
                ]
            },
        )()

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            pass

        def run_sync(self, prompt):
            return FakeResult()

    module.Agent = FakeAgent
    monkeypatch.setitem(sys.modules, "pydantic_ai", module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    thesis = Thesis(statement="compliance developer tools")
    profile = CompanyProfile(
        name="FallbackCo",
        description="Compliance tools for developer workflows.",
        industry_tags=["developer tools"],
    )
    evidence = build_evidence(thesis, profile)
    claims = extract_claims(thesis, profile, evidence)

    assert len(claims) == 1
    assert claims[0].evidence_ids == ["fallbackco-companyenrich-profile"]


@pytest.mark.asyncio
async def test_run_agent_sync_works_inside_running_event_loop():
    class FakeAgent:
        def run_sync(self, prompt):
            return f"ok:{prompt}"

    assert _run_agent_sync(FakeAgent(), "prompt") == "ok:prompt"
