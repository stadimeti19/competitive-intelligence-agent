"""Deterministic scoring: thesis recall, news (concave), exclusion, completeness."""

from __future__ import annotations

import math
import re
from typing import Dict, List, Set, Tuple

from radar.models import (
    CompanyProfile,
    ScoreBreakdown,
    ScoreComponent,
    ScoringConfig,
    Thesis,
    ThesisFit,
)

# Defaults align with ScoringConfig in models.py
DEFAULT_STRONG_MIN = 0.72
DEFAULT_MIXED_MIN = 0.42

_COMPONENT_KEYS = ("keyword_overlap", "news_signal", "exclusion_clear", "data_completeness")


def default_scoring_config() -> ScoringConfig:
    return ScoringConfig()


def _tokenize(text: str) -> Set[str]:
    """Lowercase alphanumeric tokens, min length 3 (stops common noise)."""
    if not text:
        return set()
    raw = re.findall(r"[a-z0-9]{3,}", text.lower())
    stop = {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "her",
        "was",
        "one",
        "our",
        "out",
        "has",
        "have",
        "been",
        "from",
        "with",
        "that",
        "this",
        "will",
        "your",
        "their",
        "into",
        "than",
        "then",
        "also",
        "such",
    }
    return {t for t in raw if t not in stop}


def _thesis_tokens(thesis: Thesis) -> Set[str]:
    parts = [thesis.statement] + thesis.must_include_keywords
    return _tokenize(" ".join(parts))


def _company_corpus(profile: CompanyProfile) -> str:
    parts: List[str] = [profile.name or "", profile.description or ""]
    parts.extend(profile.industry_tags)
    if profile.domain:
        parts.append(profile.domain.replace(".", " "))
    return " ".join(parts)


def _keyword_overlap_corpus(profile: CompanyProfile) -> str:
    """
    Text for thesis recall only: CE fields + DDG news titles/snippets + optional keyword_corpus_extra.
    Exclusion checks use _company_corpus only, not this string.
    """
    chunks: List[str] = [_company_corpus(profile)]
    for h in profile.news_hits:
        chunks.append(h.title or "")
        chunks.append(h.snippet or "")
    if profile.keyword_corpus_extra and profile.keyword_corpus_extra.strip():
        chunks.append(profile.keyword_corpus_extra.strip())
    return " ".join(chunks)


def compute_keyword_overlap(thesis: Thesis, profile: CompanyProfile) -> Tuple[float, float]:
    """
    Thesis token recall: |T∩C| / |T| over company fields, DDG news text, and optional keyword_corpus_extra.
    Raw and normalized are the same in [0,1]. Returns (0,0) if thesis has no tokens.
    """
    t = _thesis_tokens(thesis)
    c = _tokenize(_keyword_overlap_corpus(profile))
    if not t:
        return (0.0, 0.0)
    if not c:
        return (0.0, 0.0)
    inter = len(t & c)
    recall = inter / len(t)
    r = min(1.0, max(0.0, recall))
    return (r, r)


def compute_news_signal(profile: CompanyProfile) -> Tuple[float, float]:
    """
    Raw = min(hit_count, 5). Normalized uses sqrt of linear saturation to reduce crowding at high hit counts.
    Small recency bump when title/snippet mentions a recent year.
    """
    n = len(profile.news_hits)
    raw = float(min(n, 5))
    base_linear = raw / 5.0
    normalized = min(1.0, math.sqrt(base_linear))
    text_blob = " ".join(
        f"{h.title} {h.snippet}" for h in profile.news_hits[:8]
    ).lower()
    for year in ("2026", "2025", "2024"):
        if year in text_blob:
            normalized = min(1.0, normalized + 0.05)
            break
    return (raw, normalized)


def compute_exclusion_clear(thesis: Thesis, profile: CompanyProfile) -> Tuple[float, float]:
    """
    When must_exclude_keywords is empty: neutral 0.5 (no credit for exclusions you did not specify).
    When set: 1.0 if no excluded term in corpus, else 0.0.
    """
    if not thesis.must_exclude_keywords:
        return (0.5, 0.5)
    corpus = _company_corpus(profile).lower()
    for kw in thesis.must_exclude_keywords:
        if kw and len(kw.strip()) >= 2 and kw.strip().lower() in corpus:
            return (0.0, 0.0)
    return (1.0, 1.0)


def compute_data_completeness(profile: CompanyProfile) -> Tuple[float, float]:
    """Five binary slots: name, domain, description, industry_tags, companyenrich_id."""
    slots = [
        bool(profile.name and profile.name.strip()),
        bool(profile.domain),
        bool(profile.description and profile.description.strip()),
        bool(profile.industry_tags),
        bool(profile.companyenrich_id),
    ]
    filled = sum(1 for s in slots if s)
    raw = float(filled)
    normalized = raw / 5.0
    return (raw, normalized)


def merge_scoring_config(thesis: Thesis, base: ScoringConfig | None = None) -> ScoringConfig:
    cfg = base.model_copy() if base else ScoringConfig()
    if thesis.scoring_weights:
        w = dict(cfg.weights)
        for k, v in thesis.scoring_weights.items():
            if k in _COMPONENT_KEYS and v is not None:
                w[k] = float(v)
        s = sum(w[k] for k in _COMPONENT_KEYS)
        if s <= 0:
            raise ValueError("scoring_weights must sum to a positive value")
        cfg.weights = {k: w[k] / s for k in _COMPONENT_KEYS}
    else:
        cfg.weights = {k: cfg.weights.get(k, 0.0) for k in _COMPONENT_KEYS}
        s = sum(cfg.weights.values())
        if s > 0:
            cfg.weights = {k: cfg.weights[k] / s for k in _COMPONENT_KEYS}
    return cfg


def thesis_fit_from_total(total: float, cfg: ScoringConfig) -> ThesisFit:
    if total >= cfg.strong_min:
        return ThesisFit.strong
    if total >= cfg.mixed_min:
        return ThesisFit.mixed
    return ThesisFit.weak


def score_company(thesis: Thesis, profile: CompanyProfile, config: ScoringConfig | None = None) -> ScoreBreakdown:
    cfg = merge_scoring_config(thesis, config or default_scoring_config())
    w = cfg.weights

    ko_raw, ko_norm = compute_keyword_overlap(thesis, profile)
    ns_raw, ns_norm = compute_news_signal(profile)
    ex_raw, ex_norm = compute_exclusion_clear(thesis, profile)
    dc_raw, dc_norm = compute_data_completeness(profile)

    components: List[ScoreComponent] = [
        ScoreComponent(
            component_id="keyword_overlap",
            raw=ko_raw,
            normalized=ko_norm,
            weight=w["keyword_overlap"],
            contribution=ko_norm * w["keyword_overlap"],
        ),
        ScoreComponent(
            component_id="news_signal",
            raw=ns_raw,
            normalized=ns_norm,
            weight=w["news_signal"],
            contribution=ns_norm * w["news_signal"],
        ),
        ScoreComponent(
            component_id="exclusion_clear",
            raw=ex_raw,
            normalized=ex_norm,
            weight=w["exclusion_clear"],
            contribution=ex_norm * w["exclusion_clear"],
        ),
        ScoreComponent(
            component_id="data_completeness",
            raw=dc_raw,
            normalized=dc_norm,
            weight=w["data_completeness"],
            contribution=dc_norm * w["data_completeness"],
        ),
    ]
    total = sum(c.contribution for c in components)
    total = min(1.0, max(0.0, total))
    fit = thesis_fit_from_total(total, cfg)
    return ScoreBreakdown(total=total, components=components, thesis_fit=fit)
