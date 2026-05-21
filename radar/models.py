"""Pydantic models for radar thesis, company profiles, and scoring."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThesisFit(str, Enum):
    """Deterministic label from total score thresholds."""

    strong = "strong"
    mixed = "mixed"
    weak = "weak"


class ConfidenceLevel(str, Enum):
    """How much to trust the fit assessment, separate from fit quality."""

    high = "high"
    medium = "medium"
    low = "low"


class Thesis(BaseModel):
    """User thesis input; persisted as JSON snapshot on each run."""

    statement: str = Field(..., min_length=1, description="Investment or opportunity thesis text.")
    must_include_keywords: List[str] = Field(default_factory=list)
    must_exclude_keywords: List[str] = Field(default_factory=list)
    max_companies: int = Field(default=12, ge=1, le=50)
    scoring_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional override for component keys matching ScoringConfig.weights.",
    )


class NewsHit(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""


class SourceRef(BaseModel):
    provider: str  # "companyenrich" | "ddg" | "massive"
    detail: str = ""


class CompanyProfile(BaseModel):
    """Normalized profile after CompanyEnrich + DDG merge."""

    name: str
    domain: Optional[str] = None
    companyenrich_id: Optional[str] = None
    canonical_url: Optional[str] = None
    description: Optional[str] = None
    industry_tags: List[str] = Field(default_factory=list)
    employee_range: Optional[str] = None
    funding_stage: Optional[str] = None
    news_hits: List[NewsHit] = Field(default_factory=list)
    sources: List[SourceRef] = Field(default_factory=list)
    ticker: Optional[str] = Field(
        default=None,
        description="US stock symbol when resolved (e.g. via Massive); optional.",
    )
    keyword_corpus_extra: Optional[str] = Field(
        default=None,
        description="Scoring-only text (e.g. Massive ticker overview) for keyword recall; not used for exclusion.",
    )


class ScoreComponent(BaseModel):
    component_id: str
    raw: float
    normalized: float = Field(..., ge=0.0, le=1.0)
    weight: float
    contribution: float


class ScoreBreakdown(BaseModel):
    """Per-company deterministic score with explainable parts."""

    total: float
    components: List[ScoreComponent]
    thesis_fit: ThesisFit


class EvidenceItem(BaseModel):
    """Source-grounded snippet used to support radar scoring or extracted claims."""

    id: str
    provider: str  # "companyenrich" | "ddg" | "massive"
    source_type: str  # "profile" | "news" | "ticker_overview"
    title: str = ""
    url: str = ""
    snippet: str = ""
    matched_terms: List[str] = Field(default_factory=list)


class ExtractedClaim(BaseModel):
    """Typed claim extracted from evidence, with source references by evidence id."""

    claim: str
    category: str = "market_signal"
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ConfidenceBreakdown(BaseModel):
    """Trust metrics for a ranking; kept separate from the fit score."""

    fit_score: float = Field(..., ge=0.0, le=1.0)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    data_completeness: float = Field(..., ge=0.0, le=1.0)
    contradiction_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel


class ScoringConfig(BaseModel):
    """
    Weights for four components (must sum to 1.0).
    - keyword_overlap: thesis token recall |T∩C|/|T| vs company corpus
    - news_signal: DDG hits with concave (sqrt) normalization
    - exclusion_clear: 0.5 neutral if no must_exclude list; else 1 clear / 0 hit
    - data_completeness: fraction of key fields populated
    """

    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "keyword_overlap": 0.56,
            "news_signal": 0.19,
            "exclusion_clear": 0.13,
            "data_completeness": 0.12,
        }
    )
    # Total score thresholds for ThesisFit (inclusive bounds documented in scoring.py)
    strong_min: float = 0.72
    mixed_min: float = 0.42


class RadarCompanyResult(BaseModel):
    rank: int
    profile: CompanyProfile
    score_breakdown: ScoreBreakdown
    evidence: List[EvidenceItem] = Field(default_factory=list)
    claims: List[ExtractedClaim] = Field(default_factory=list)
    confidence: Optional[ConfidenceBreakdown] = None


class RadarRunResults(BaseModel):
    companies: List[RadarCompanyResult]

    def model_dump_json_safe(self) -> List[Dict[str, Any]]:
        return [c.model_dump(mode="json") for c in self.companies]
