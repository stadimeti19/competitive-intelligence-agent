"""Thesis-driven opportunity radar (parallel to legacy CI /analyze)."""

from radar.models import (
    CompanyProfile,
    NewsHit,
    RadarCompanyResult,
    RadarRunResults,
    ScoreBreakdown,
    ScoringConfig,
    SourceRef,
    Thesis,
    ThesisFit,
)
from radar.scoring import default_scoring_config, score_company

__all__ = [
    "CompanyProfile",
    "NewsHit",
    "RadarCompanyResult",
    "RadarRunResults",
    "ScoreBreakdown",
    "ScoringConfig",
    "SourceRef",
    "Thesis",
    "ThesisFit",
    "default_scoring_config",
    "score_company",
]
