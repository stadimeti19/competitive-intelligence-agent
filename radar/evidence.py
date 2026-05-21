"""Evidence tracing, typed claim extraction, and confidence for radar results."""

from __future__ import annotations

import os
import re
import threading
from typing import Iterable, List, Sequence, Set

from pydantic import BaseModel, Field

from radar.models import (
    CompanyProfile,
    ConfidenceBreakdown,
    ConfidenceLevel,
    EvidenceItem,
    ExtractedClaim,
    ScoreBreakdown,
    Thesis,
)
from radar.scoring import compute_data_completeness


_STOP_WORDS = {
    "the",
    "and",
    "for",
    "are",
    "but",
    "not",
    "you",
    "all",
    "can",
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


class ClaimExtractionResult(BaseModel):
    """Structured PydanticAI output for evidence-backed claims."""

    claims: List[ExtractedClaim] = Field(default_factory=list)


def _tokenize(text: str) -> Set[str]:
    raw = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    return {t for t in raw if t not in _STOP_WORDS}


def _thesis_terms(thesis: Thesis) -> Set[str]:
    return _tokenize(" ".join([thesis.statement, *thesis.must_include_keywords]))


def _matched_terms(text: str, thesis_terms: Set[str]) -> List[str]:
    text_terms = _tokenize(text)
    return sorted(text_terms & thesis_terms)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "company").lower()).strip("-")
    return slug[:40] or "company"


def _compact(parts: Iterable[str | None], *, limit: int = 600) -> str:
    text = " ".join(p.strip() for p in parts if p and p.strip())
    return text[:limit].strip()


def build_evidence(thesis: Thesis, profile: CompanyProfile) -> List[EvidenceItem]:
    """Create stable source snippets from normalized enrichment output."""
    terms = _thesis_terms(thesis)
    slug = _slugify(profile.name)
    evidence: List[EvidenceItem] = []

    profile_bits = [
        profile.description,
        f"Industry tags: {', '.join(profile.industry_tags)}" if profile.industry_tags else None,
        f"Employees: {profile.employee_range}" if profile.employee_range else None,
        f"Funding stage: {profile.funding_stage}" if profile.funding_stage else None,
        f"Domain: {profile.domain}" if profile.domain else None,
    ]
    profile_snippet = _compact(profile_bits)
    if profile_snippet:
        evidence.append(
            EvidenceItem(
                id=f"{slug}-companyenrich-profile",
                provider="companyenrich",
                source_type="profile",
                title=f"{profile.name} company profile",
                url=profile.canonical_url or (f"https://{profile.domain}" if profile.domain else ""),
                snippet=profile_snippet,
                matched_terms=_matched_terms(profile_snippet, terms),
            )
        )

    for idx, hit in enumerate(profile.news_hits[:8], start=1):
        snippet = _compact([hit.title, hit.snippet], limit=500)
        if not snippet:
            continue
        evidence.append(
            EvidenceItem(
                id=f"{slug}-ddg-news-{idx}",
                provider="ddg",
                source_type="news",
                title=hit.title or f"{profile.name} news result {idx}",
                url=hit.url,
                snippet=hit.snippet or hit.title,
                matched_terms=_matched_terms(snippet, terms),
            )
        )

    if profile.keyword_corpus_extra and profile.keyword_corpus_extra.strip():
        snippet = _compact([profile.keyword_corpus_extra], limit=700)
        evidence.append(
            EvidenceItem(
                id=f"{slug}-massive-overview",
                provider="massive",
                source_type="ticker_overview",
                title=f"{profile.ticker or profile.name} ticker overview",
                url="",
                snippet=snippet,
                matched_terms=_matched_terms(snippet, terms),
            )
        )

    return evidence


def compute_confidence(
    thesis: Thesis,
    profile: CompanyProfile,
    score_breakdown: ScoreBreakdown,
    evidence: Sequence[EvidenceItem],
) -> ConfidenceBreakdown:
    """Compute deterministic trust metrics, separate from ranking quality."""
    terms = _thesis_terms(thesis)
    supported_terms = {term for item in evidence for term in item.matched_terms}
    term_coverage = (len(supported_terms) / len(terms)) if terms else 0.0
    provider_diversity = len({item.provider for item in evidence if item.matched_terms})
    matched_evidence_count = len([item for item in evidence if item.matched_terms])
    evidence_strength = min(
        1.0,
        (term_coverage * 0.65)
        + (min(provider_diversity, 3) / 3.0 * 0.25)
        + (min(matched_evidence_count, 6) / 6.0 * 0.10),
    )

    _, completeness = compute_data_completeness(profile)
    exclusion_hits = 0
    if thesis.must_exclude_keywords:
        corpus = " ".join([item.snippet for item in evidence] + [profile.description or ""]).lower()
        for kw in thesis.must_exclude_keywords:
            needle = kw.strip().lower()
            if len(needle) >= 2 and needle in corpus:
                exclusion_hits += 1
    contradiction_score = min(1.0, exclusion_hits / max(1, len(thesis.must_exclude_keywords)))

    combined = (
        evidence_strength * 0.50
        + completeness * 0.25
        + score_breakdown.total * 0.15
        + (1.0 - contradiction_score) * 0.10
    )
    if combined >= 0.72:
        level = ConfidenceLevel.high
    elif combined >= 0.45:
        level = ConfidenceLevel.medium
    else:
        level = ConfidenceLevel.low

    return ConfidenceBreakdown(
        fit_score=score_breakdown.total,
        evidence_strength=evidence_strength,
        data_completeness=completeness,
        contradiction_score=contradiction_score,
        confidence_level=level,
    )


def _sanitize_claims(claims: Sequence[ExtractedClaim], valid_ids: Set[str]) -> List[ExtractedClaim]:
    clean: List[ExtractedClaim] = []
    for claim in claims:
        ids = [eid for eid in claim.evidence_ids if eid in valid_ids]
        if not claim.claim.strip() or not ids:
            continue
        clean.append(claim.model_copy(update={"evidence_ids": ids}))
        if len(clean) >= 5:
            break
    return clean


def _run_agent_sync(agent, prompt: str):
    """
    PydanticAI run_sync cannot run inside FastAPI's active event loop.
    Bounce to a short-lived thread when a loop is already running.
    """
    try:
        import asyncio

        asyncio.get_running_loop()
    except RuntimeError:
        return agent.run_sync(prompt)

    box = {}

    def target():
        try:
            box["result"] = agent.run_sync(prompt)
        except Exception as e:
            box["error"] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["result"]


def extract_claims(thesis: Thesis, profile: CompanyProfile, evidence: Sequence[EvidenceItem]) -> List[ExtractedClaim]:
    """
    Use PydanticAI for typed claim extraction when configured.
    Returns no extracted claims on import/config/runtime failures; evidence and confidence remain deterministic.
    """
    if not evidence:
        return []
    model_name = os.environ.get("PYDANTICAI_CLAIM_MODEL") or os.environ.get("OPENAI_MODEL") or "openai:gpt-5.4-nano"
    if not os.environ.get("OPENAI_API_KEY"):
        return []

    try:
        from pydantic_ai import Agent
    except Exception as e:
        print(f"[radar.evidence] PydanticAI unavailable; skipping claim extraction: {e}")
        return []

    evidence_payload = "\n".join(
        f"- id={item.id}; provider={item.provider}; title={item.title}; snippet={item.snippet[:450]}"
        for item in evidence[:10]
    )
    prompt = (
        "Extract concise market-intelligence claims for this company and thesis.\n"
        f"Thesis: {thesis.statement}\n"
        f"Company: {profile.name}\n"
        "Rules: each claim must cite one or more provided evidence ids; do not invent sources; "
        "prefer product, market, customer, funding, or risk signals; max five claims.\n"
        f"Evidence:\n{evidence_payload}"
    )

    try:
        agent = Agent(
            model_name,
            output_type=ClaimExtractionResult,
            instructions=(
                "You extract source-grounded competitive intelligence claims. "
                "Return only claims supported by the provided evidence ids."
            ),
        )
        result = _run_agent_sync(agent, prompt)
        return _sanitize_claims(result.output.claims, {item.id for item in evidence})
    except Exception as e:
        print(f"[radar.evidence] Claim extraction failed for {profile.name!r}; skipping claims: {e}")
        return []
