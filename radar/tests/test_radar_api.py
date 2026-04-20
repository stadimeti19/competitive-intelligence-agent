"""FastAPI radar routes with mocked enrichment."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from radar.models import CompanyProfile, NewsHit, Thesis


@pytest.fixture
def client():
    return TestClient(app)


def _sample_profiles():
    return [
        CompanyProfile(
            name="Alpha",
            domain="alpha.com",
            companyenrich_id="11111111-1111-1111-1111-111111111111",
            description="compliance automation for developer workflows",
            industry_tags=["compliance", "developer tools"],
            news_hits=[NewsHit(title="n1", url="https://a", snippet="2025 launch")],
        ),
        CompanyProfile(
            name="Beta",
            domain="beta.com",
            companyenrich_id="22222222-2222-2222-2222-222222222222",
            description="generic consulting",
            industry_tags=["consulting"],
            news_hits=[],
        ),
    ]


@patch("radar.service.supabase_store.save_radar_run", return_value="radar-run-id")
@patch("radar.service.build_profiles_for_thesis")
def test_radar_analyze_returns_ranked_companies(mock_build, mock_save, client):
    mock_build.return_value = _sample_profiles()
    body = {
        "statement": "AI devtools for compliance teams",
        "must_include_keywords": ["compliance"],
        "max_companies": 10,
    }
    r = client.post("/radar/analyze", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["runId"] == "radar-run-id"
    assert data["persisted"] is True
    assert "labelLegend" in data
    comps = data["companies"]
    assert len(comps) == 2
    assert comps[0]["rank"] == 1
    assert comps[0]["score_breakdown"]["total"] >= comps[1]["score_breakdown"]["total"]
    mock_save.assert_called_once()


@patch("radar.service.build_profiles_for_thesis")
def test_radar_analyze_400_without_api_key_flow(mock_build, client):
    mock_build.side_effect = ValueError("COMPANYENRICH_API_KEY is not set")
    r = client.post("/radar/analyze", json={"statement": "test"})
    assert r.status_code == 400


@patch("main.supabase_store.list_radar_runs", return_value=[])
def test_list_radar_runs(mock_list, client):
    r = client.get("/radar/runs")
    assert r.status_code == 200
    assert r.json() == {"runs": []}
