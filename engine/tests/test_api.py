"""HTTP contract tests for the existing FastAPI application."""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_reports_loaded_rule_counts():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "domains": {"liuyao": 192, "ziwei": 64, "bazi": 294},
    }


def test_list_rules_and_invalid_domain():
    response = client.get("/api/rules/liuyao")
    assert response.status_code == 200
    assert response.json()["count"] == 192
    assert response.json()["domain"] == "liuyao"

    invalid = client.get("/api/rules/no_such_domain")
    assert invalid.status_code == 400


def test_three_analysis_endpoints_return_contract_shape():
    cases = [
        ("/api/liuyao/analyze", {"month_zh": "申", "day_zh": "子", "yong_shen": {"zhi": "申", "wx": "金"}}),
        ("/api/ziwei/analyze", {"ming_gong": {"palace": "命", "main_stars": ["紫微"]}}),
        ("/api/bazi/analyze", {"day_gan": "甲", "month_zhi": "寅", "ri_zhu_wx": "木", "ri_zhu_wangshuai": "旺"}),
    ]
    for path, payload in cases:
        response = client.post(path, json=payload)
        assert response.status_code == 200, (path, response.text)
        body = response.json()
        assert set(body) == {"domain", "matched_rules", "conclusions", "total_weight", "matched_count"}
