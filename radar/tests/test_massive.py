"""Massive optional enrichment (mocked HTTP)."""

from unittest.mock import patch

from radar.models import CompanyProfile
from radar.sources.massive import maybe_enrich_massive


@patch("radar.sources.massive._api_key", return_value=None)
def test_maybe_enrich_skips_without_api_key(_mock_key):
    p = CompanyProfile(name="Apple Inc", domain="apple.com", description="Consumer electronics")
    maybe_enrich_massive(p)
    assert p.ticker is None
    assert p.keyword_corpus_extra is None


@patch("radar.sources.massive._api_key", return_value="test-key")
@patch("radar.sources.massive._ticker_overview")
@patch("radar.sources.massive._search_tickers")
def test_maybe_enrich_merges_on_domain_match(mock_search, mock_overview, _key):
    mock_search.return_value = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "homepage_url": "https://www.apple.com",
        },
        {
            "ticker": "OTHER",
            "name": "Other",
            "homepage_url": "https://other.com",
        },
    ]
    mock_overview.return_value = {
        "ticker": "AAPL",
        "description": "Designs smartphones and computers.",
        "sic_description": "ELECTRONIC COMPUTERS",
    }
    p = CompanyProfile(name="Apple Inc", domain="apple.com", description="Hardware")
    maybe_enrich_massive(p)
    assert p.ticker == "AAPL"
    assert p.keyword_corpus_extra and "smartphones" in p.keyword_corpus_extra.lower()
    assert any(s.provider == "massive" for s in p.sources)
    assert "ELECTRONIC COMPUTERS" in p.industry_tags


@patch("radar.sources.massive._api_key", return_value="test-key")
@patch("radar.sources.massive._search_tickers")
def test_maybe_enrich_skips_when_no_homepage_domain_match(mock_search, _key):
    mock_search.return_value = [
        {"ticker": "ZZZ", "name": "Wrong", "homepage_url": "https://wrong.com"},
    ]
    p = CompanyProfile(name="Apple Inc", domain="apple.com", description="x")
    maybe_enrich_massive(p)
    assert p.ticker is None
