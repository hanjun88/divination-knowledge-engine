# -*- coding: utf-8 -*-
"""Provider 侧契约固化测试：rules_manifest.json 四字段 + openapi_schema.json 一致性。

由 CI (rule-engine-ci.yml) 在 engine/ 目录下运行：
    PYTHONPATH=. python -m pytest -q tests
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = REPO_ROOT / "engine"

MANIFEST = ENGINE_DIR / "rules_manifest.json"
SCHEMA = REPO_ROOT / "openapi_schema.json"

REQUIRED_FIELDS = ("provider_commit", "schema_version", "schema_sha256",
                   "canonical_manifest_sha")


def _canonical_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def test_manifest_files_exist():
    assert MANIFEST.exists(), "engine/rules_manifest.json missing"
    assert SCHEMA.exists(), "openapi_schema.json missing (run scripts/export_schema.py)"


def test_manifest_four_traceability_fields_present_and_nonempty():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for k in REQUIRED_FIELDS:
        assert k in m and isinstance(m[k], str) and m[k].strip(), f"field {k} missing/empty"
    assert m["schema_version"] == "1.0.0"
    # provider_commit 形如 git SHA（允许 "unknown" 兜底，但正常应为 hex）
    assert len(m["provider_commit"]) >= 7


def test_manifest_preserves_rule_data():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    domains = {r["domain"]: r["count"] for r in m["rules"]}
    assert domains == {"bazi": 294, "liuyao": 192, "ziwei": 64}, domains


def test_schema_sha256_matches_openapi_file():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual = hashlib.sha256(SCHEMA.read_bytes()).hexdigest()
    assert m["schema_sha256"] == actual


def test_canonical_manifest_sha_self_consistent():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stored = raw.pop("canonical_manifest_sha")
    recomputed = hashlib.sha256(_canonical_bytes(raw)).hexdigest()
    assert stored == recomputed


def test_openapi_schema_is_valid_3x_with_health():
    spec = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["version"] == "1.0.0"
    assert "/health" in spec["paths"]
    for p in ("/api/rules/{domain}", "/api/liuyao/analyze",
              "/api/ziwei/analyze", "/api/bazi/analyze"):
        assert p in spec["paths"], p
