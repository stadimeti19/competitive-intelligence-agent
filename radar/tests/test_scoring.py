"""Golden-style tests for deterministic scoring."""

import pytest

from radar.models import CompanyProfile, NewsHit, ScoringConfig, Thesis
from radar.scoring import (
    compute_exclusion_clear,
    compute_keyword_overlap,
    merge_scoring_config,
    score_company,
    thesis_fit_from_total,
)


def test_high_overlap_strong_fit():
    thesis = Thesis(
        statement="AI developer tools for compliance automation",
        must_include_keywords=["compliance", "developer"],
    )
    profile = CompanyProfile(
        name="ComplianceDev AI",
        domain="compliancedev.ai",
        companyenrich_id="550e8400-e29b-41d4-a716-446655440000",
        description=(
            "Developer tools and compliance automation for security teams; "
            "our platform focuses on compliance automation workflows."
        ),
        industry_tags=["developer tools", "compliance", "compliance automation"],
        news_hits=[
            NewsHit(title="ComplianceDev raises seed", url="https://x.com/a", snippet="2025 funding"),
            NewsHit(title="Product launch", url="https://x.com/b", snippet="news"),
        ],
    )
    bd = score_company(thesis, profile)
    assert bd.total >= 0.72
    assert bd.thesis_fit.value == "strong"
    ids = {c.component_id for c in bd.components}
    assert ids == {"keyword_overlap", "news_signal", "exclusion_clear", "data_completeness"}
    assert abs(sum(c.contribution for c in bd.components) - bd.total) < 1e-9


def test_exclusion_keyword_forces_weak():
    """Excluded term in corpus zeros exclusion_clear; low thesis recall keeps total below mixed."""
    thesis = Thesis(
        statement="aquaculture supply chain planning software",
        must_exclude_keywords=["crypto"],
    )
    profile = CompanyProfile(
        name="CryptoCorp",
        description="We are a crypto exchange and digital asset platform for global traders.",
        industry_tags=["trading"],
        news_hits=[NewsHit(title="n", url="u", snippet="s")],
    )
    bd = score_company(thesis, profile)
    assert bd.components[2].component_id == "exclusion_clear"
    assert bd.components[2].normalized == 0.0
    assert bd.thesis_fit.value == "weak"


def test_mixed_band():
    thesis = Thesis(statement="obscure niche xyzzy12345 onlyterm")
    profile = CompanyProfile(
        name="OtherCo",
        description="Generic business services without overlap tokens.",
        industry_tags=["retail"],
        news_hits=[],
    )
    bd = score_company(thesis, profile)
    # Low overlap, no news, completeness partial
    assert bd.thesis_fit.value in ("weak", "mixed")


def test_weight_override_renormalizes():
    thesis = Thesis(
        statement="saas platform",
        scoring_weights={"keyword_overlap": 0.8, "news_signal": 0.2},
    )
    cfg = merge_scoring_config(thesis)
    s = sum(cfg.weights.values())
    assert abs(s - 1.0) < 1e-6


def test_thesis_fit_thresholds():
    cfg = ScoringConfig(strong_min=0.7, mixed_min=0.4)
    assert thesis_fit_from_total(0.71, cfg).value == "strong"
    assert thesis_fit_from_total(0.5, cfg).value == "mixed"
    assert thesis_fit_from_total(0.39, cfg).value == "weak"


def test_keyword_recall_increases_when_company_matches_more_thesis_terms():
    thesis = Thesis(statement="alpha beta gamma delta")
    low = CompanyProfile(
        name="Co",
        description="alpha platform",
        industry_tags=[],
    )
    high = CompanyProfile(
        name="Co",
        description="alpha beta gamma delta products",
        industry_tags=[],
    )
    s_low = score_company(thesis, low).components[0].normalized
    s_high = score_company(thesis, high).components[0].normalized
    assert s_high > s_low


def test_vacuous_exclusion_is_neutral_not_full_credit():
    thesis = Thesis(statement="saas analytics")
    profile = CompanyProfile(
        name="X",
        description="analytics dashboards",
        industry_tags=["saas"],
        companyenrich_id="550e8400-e29b-41d4-a716-446655440000",
    )
    ex = score_company(thesis, profile).components[2]
    assert ex.component_id == "exclusion_clear"
    assert ex.normalized == 0.5
    assert ex.raw == 0.5


def test_keyword_recall_includes_ddg_news_text():
    thesis = Thesis(statement="zebra quantum uniquephrase")
    base = CompanyProfile(name="Co", description="zebra", industry_tags=[], news_hits=[])
    with_news = CompanyProfile(
        name="Co",
        description="zebra",
        industry_tags=[],
        news_hits=[
            NewsHit(title="Press", url="u", snippet="quantum uniquephrase product update"),
        ],
    )
    r_base, _ = compute_keyword_overlap(thesis, base)
    r_news, _ = compute_keyword_overlap(thesis, with_news)
    assert r_news > r_base


def test_exclusion_does_not_scan_ddg_news_text():
    thesis = Thesis(statement="enterprise software", must_exclude_keywords=["crypto"])
    profile = CompanyProfile(
        name="CleanCo",
        description="enterprise software for teams",
        industry_tags=["software"],
        news_hits=[
            NewsHit(title="Tabloid", url="u", snippet="crypto market volatility headline"),
        ],
    )
    raw, norm = compute_exclusion_clear(thesis, profile)
    assert norm == 1.0
    assert raw == 1.0


def test_keyword_corpus_extra_boosts_recall():
    thesis = Thesis(statement="semiconductor manufacturing equipment")
    without = CompanyProfile(
        name="FabTools",
        description="We build tools for factories.",
        industry_tags=["industrial"],
        news_hits=[],
    )
    extra = CompanyProfile(
        name="FabTools",
        description="We build tools for factories.",
        industry_tags=["industrial"],
        news_hits=[],
        keyword_corpus_extra="Leading semiconductor manufacturing equipment vendor.",
    )
    r0, _ = compute_keyword_overlap(thesis, without)
    r1, _ = compute_keyword_overlap(thesis, extra)
    assert r1 > r0
